# Module 3 lab: POST /orders on an HTTP API

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** `sample-create-order`, `sample-create-order-role`, and `sample-orders-api`  
**You will not install:** the Serverless Framework, Node.js, or the AWS CLI

The function returns a stub order. It does not read a database.

## 1. Create the function

1. Set the region to **ap-south-1**.
2. Open **Lambda** → **Create function** → Author from scratch.
3. Function name: `sample-create-order`.
4. Runtime: **Python 3.12**.
5. Create a new execution role named `sample-create-order-role` with basic Lambda permissions.
6. Create the function.
7. Replace the editor contents with this code and deploy it:

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

8. Set the timeout to **3** seconds and memory to **128** MB.

## 2. Test it once in the Lambda console

1. Open the **Test** tab.
2. Create an event named `http-post` with this JSON:

```json
{
  "requestContext": { "http": { "method": "POST", "path": "/orders" } },
  "body": "{\"sku\":\"BOOK-1\",\"qty\":1}"
}
```

3. Run the test.
4. Confirm the response has `statusCode` 201 and a body containing `orderId` and `ACCEPTED`.

## 3. Add the HTTP API

1. Open **API Gateway** → **Create API** → **HTTP API**.
2. Add an integration to the Lambda function `sample-create-order` in `ap-south-1`.
3. Name the API `sample-orders-api`.
4. Add a route: method **POST**, resource path `/orders`.
5. Stage name `$default`, with auto-deploy enabled.
6. Copy the invoke URL.

## 4. Call POST /orders

Use the invoke URL from the console. The path must end in `/orders`.

```bash
curl -sS -X POST "https://REPLACE.execute-api.ap-south-1.amazonaws.com/orders" \
  -H "content-type: application/json" \
  -d '{"sku":"BOOK-1","qty":1}'
```

Call it twice. Write down both order ids. They should differ.

If you do not have a terminal, use a teammate’s machine or the instructor’s call. Record the response body you were shown.

## 5. Read the framework file

On the instructor’s screen, find these four fields in `serverless.yml`: region, function name, handler, and `POST /orders`. You are not asked to deploy that file.

## 6. Cleanup

1. Delete the API `sample-orders-api`.
2. Delete the function `sample-create-order`.
3. Delete the role `sample-create-order-role`.
4. Delete the log group `/aws/lambda/sample-create-order` if it exists.

## Done when

- A POST returned 201 and an `orderId`.
- A second POST returned a different `orderId`.
- The API, the function, and the role are deleted.
