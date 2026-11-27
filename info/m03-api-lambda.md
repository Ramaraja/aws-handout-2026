# API Gateway, Lambda, and serverless

**Handout.** Region: **ap-south-1** (Mumbai).

You put an HTTP API in front of the order function. You create function `sample-create-order`, role `sample-create-order-role`, and HTTP API `sample-orders-api`. The function stays out of a VPC.

## Goals

By the end of this handout you can explain:

1. What “serverless” changes for Sample Orders, including cold starts and the 15-minute Lambda limit.
2. How to read a Lambda event, name the execution role, and connect a function to a later event source without changing the business code’s shape.
3. How to put an HTTP API in front of the function with a Lambda proxy integration and a `POST /orders` route.
4. How to read a `serverless.yml` that describes that same API. The working copy is created in the console.

## Serverless architecture

“Serverless” means Sample Orders does not provision a server for the HTTP request. AWS runs the function when a request arrives and bills for the requests and the time used, in GB-seconds. Nobody SSHes into the worker. Nobody patches its operating system. Sample Orders still owns the code, the role, the timeout, and the memory.

What you give up:

- You do not control the instance. A cold start is a new execution environment: download the code, start the runtime, run static init, then the handler. Python with a few imports is usually a short pause. A large package or a function inside a VPC is slower. Provisioned concurrency keeps environments warm and bills while idle. The practice function does not use it.
- The function is stateless. Local files in `/tmp` and global variables do not survive as a database. The order row belongs in Aurora. The invoice belongs in S3.
- The maximum timeout is **15 minutes**. `sample-create-order` should finish in well under a second. The nightly export must not be forced into this function if it can run long. That export is the Glue job.

API Gateway plus Lambda fits `POST /orders` because the work is short, the traffic is spiky, and there is no idle server to pay for between orders. It is a poor fit for the packing process that stays running while people work a queue of shipments. That process is Fargate.

## Lambda and event-driven execution

A function has a name, a runtime, a handler, a role, a timeout, and memory. Sample’s function:

| Setting | Value |
| --- | --- |
| Name | `sample-create-order` |
| Runtime | Python 3.12 |
| Handler | `lambda_function.lambda_handler` |
| Role | `sample-create-order-role` |
| Timeout | 3 seconds |
| Memory | 128 MB |

Memory also sets the CPU. 128 MB is enough for a stub that returns JSON. Raising memory is a performance knob, not a storage knob.

The handler receives `(event, context)`. For an HTTP API with proxy integration, `event` contains the route, the HTTP method, headers, and a `body` string. `context` contains the request id and the remaining time. The stub ignores the body and returns a new order id. A queue worker receives a different event shape: a batch of SQS records. Same runtime, different event. The function does not poll a server you manage. Lambda’s service polls SQS when you add an event source mapping, and it invokes the function when API Gateway receives a request.

The execution role is assumed on each invoke. `AWSLambdaBasicExecutionRole` is enough here because the function does not call S3, SNS, or Aurora. When those calls are added, you add actions on those resource ARNs. You do not paste keys into environment variables.

Retries depend on the event source. API Gateway does not retry a failed function the way an asynchronous invoke does. SQS retries until the message is deleted or it lands on a dead-letter queue.

Limits that change design:

- A synchronous payload from API Gateway is not a file upload. Keep the order event small.
- Account concurrency is shared by every function. A tight reserved concurrency on one function protects the account and can throttle that function. Leave it unset for this example.
- CloudWatch Logs receives whatever the function prints. A `print` in the stub proves the path when you add monitoring.

```python
import json
import uuid

def lambda_handler(event, context):
    order_id = str(uuid.uuid4())
    print("accepted", order_id)
    return {
        "statusCode": 201,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"orderId": order_id, "status": "ACCEPTED"}),
    }
```

The `print` line is the log line to look for later. It is not a monitoring design.

## API Gateway and Lambda integration

Sample Orders uses an **HTTP API**, not a REST API. An HTTP API is the lower-cost, lower-ceremony front door. It supports Lambda proxy integration, stages, and JWT authorizers. A REST API adds API keys, usage plans, and request validation models. Sample Orders does not need those for a first order API. If the console offers both, choose HTTP API.

**Lambda proxy integration** means API Gateway passes the HTTP request through and expects the status code, headers, and body from the function. You do not map individual fields in a mapping template. The stub’s return value is already the proxy shape. A bare dict without `statusCode` makes the client get a 500.

Pieces to name:

- **API** `sample-orders-api`.
- **Route** `POST /orders`. A route without a method match is how a catch-all `ANY /` gets opened by accident.
- **Integration** pointing at `sample-create-order`. Payload format 2.0 is the right choice for an HTTP API.
- **Stage** `$default`. Auto-deploy so a console change is invoked on the next call. A stage is an environment pointer (dev, prod). One stage is enough here.
- **Invoke permission.** API Gateway needs `lambda:InvokeFunction` on the function. The console adds this resource policy when you create the integration. That permission is not the function’s execution role. Two different identities: API Gateway is allowed to invoke, Lambda is allowed to write logs.

The invoke URL looks like `https://{api-id}.execute-api.ap-south-1.amazonaws.com/orders`. The stage `$default` is often omitted from the path. Use the URL the console shows. Call it with POST, not GET.

There is no authorizer in this example. The URL is public to anyone who has it. A production API would add IAM auth or a JWT authorizer.

## Serverless Framework

The Serverless Framework turns a YAML file into CloudFormation and deploys it. The file is the source-controlled twin of the console clicks. You do not need Node or the CLI to create the API.

```yaml
service: sample-orders
frameworkVersion: "3"
provider:
  name: aws
  runtime: python3.12
  region: ap-south-1
  httpApi:
    name: sample-orders-api
functions:
  createOrder:
    name: sample-create-order
    handler: lambda_function.lambda_handler
    events:
      - httpApi:
          path: /orders
          method: post
```

What the file is saying:

- `provider.region` is `ap-south-1`. A deploy from a laptop whose default region is different is the same mistake as the console region selector.
- `functions.createOrder.events` creates the route and the permission for API Gateway to invoke the function.
- The handler string must match the file and the function name. In the console editor the file is `lambda_function.py` and the handler is `lambda_function.lambda_handler`.

`serverless deploy` packages the directory, uploads it, and updates a stack. `serverless remove` deletes that stack. The console path reaches the same end state: one function, one HTTP API, one route.

AWS SAM and AWS CDK describe the same resources in other syntaxes. The click path is a stand-in for a template. The invoice bucket later has a real CloudFormation template.

## In the console

### 1. Create the function

1. Region **ap-south-1**.
2. **Lambda** → **Create function** → Author from scratch.
3. Name `sample-create-order`. Runtime **Python 3.12**. Architecture x86_64.
4. Execution role: create a new role named `sample-create-order-role` with basic Lambda permissions. If that role already exists from the networking example, attach it instead of creating a second one.
5. Create the function. Replace the default code with the stub above. **Deploy**.
6. Configuration → General configuration: timeout **3** seconds, memory **128** MB.

**Expected:** the function page shows the role `sample-create-order-role`.

**If it fails:** the role name exists and is not a Lambda role. Open IAM, fix the trust policy or delete the stray role, then retry.

### 2. Test the function alone

1. Test tab → create a test event named `http-post`. Use this event:

```json
{
  "requestContext": { "http": { "method": "POST", "path": "/orders" } },
  "body": "{\"sku\":\"BOOK-1\",\"qty\":1}"
}
```

2. Run the test.

**Expected:** status 201 and a JSON body with `orderId` and `status` `ACCEPTED`. The log output includes `accepted`.

### 3. Put the HTTP API in front

1. **API Gateway** → **Create API** → **HTTP API** → Build.
2. Integration: Lambda, region ap-south-1, function `sample-create-order`.
3. API name `sample-orders-api`.
4. Route: method **POST**, path `/orders`. Delete the extra `$default` route if the wizard adds one and you do not want a catch-all.
5. Stage `$default`, auto-deploy on.
6. Copy the invoke URL.

**Expected:** the route `POST /orders` shows the Lambda integration.

### 4. Call it

```bash
curl -sS -X POST "$INVOKE_URL/orders" \
  -H "content-type: application/json" \
  -d '{"sku":"BOOK-1","qty":1}'
```

If the console’s invoke URL already ends in a stage name, do not append another `/orders` beyond the path the route expects. The usual form is `{invoke-url}/orders`.

**Expected:** HTTP 201 and a JSON order id. A second call returns a different id.

**If it fails:**

- 403 or missing invoke permission: the integration was not granted `lambda:InvokeFunction`. Recreate the integration from the API Gateway side so the console adds the permission.
- 500 and a body about malformed JSON: the function returned a Python dict instead of the proxy shape. Redeploy the stub.
- The method does not match: fix the route. Do not add `ANY /`.
- Timeout: the function was attached to a VPC with no network path. Remove the VPC configuration. This function has no VPC.

### 5. Read the YAML

Match `path`, `method`, `region`, and `handler` to the API you just created. You do not need to deploy the file.

## When you are done

1. API Gateway → `sample-orders-api` → Delete.
2. Lambda → `sample-create-order` → Delete.
3. IAM → `sample-create-order-role` → Delete.
4. CloudWatch → Log groups → delete `/aws/lambda/sample-create-order`.

Keep the example to one function, one route, and one test call. A custom domain, an authorizer, and a database can wait. The POST body is ignored by the stub on purpose. Persisting `sku` needs the database and the event path, not more code in this function.

## What this costs

A handful of invokes and one HTTP API for under an hour sit inside the free tier for most accounts. Delete the API and the function so a later experiment does not keep a public URL. There is no NAT gateway and no VPC in this example.
