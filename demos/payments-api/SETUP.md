# Create the payments API in the console

Do this in the AWS console. Region: **ap-south-1**. Do not open CloudFormation for these steps. [template.yaml](template.yaml) is a reading copy of the same resources.

You will create:

1. Lambda function `sample-payments`
2. HTTP API `sample-payments-api` with four routes on that function

The function returns ids and statuses. It does not charge a card. Do not type a real card number, expiry, or CVV.

## 1. Set the region

1. Sign in to the training account.
2. In the top bar, set the region selector to **Asia Pacific (Mumbai) ap-south-1**.
3. Leave it there for every step below.

## 2. Create the Lambda function

1. Search for **Lambda** and open it.
2. Choose **Create function**.
3. Choose **Author from scratch**.
4. Function name: `sample-payments`.
5. Runtime: **Python 3.12**.
6. Architecture: **x86_64**.
7. Under permissions, choose **Create a new role with basic Lambda permissions**.
8. Expand the role settings if needed and name the role `sample-payments-role`. If the console does not ask for a name, it will create a role for you. After the function exists, open **Configuration**, then **Permissions**, and confirm the role only has basic logging (`AWSLambdaBasicExecutionRole`). Rename is optional. Do not attach `AdministratorAccess`.
9. Choose **Create function**.

### Paste the handler

1. Open [src/lambda_function.py](src/lambda_function.py).
2. In the Lambda code editor, select all of the default file and replace it with that file.
3. Confirm the handler setting is `lambda_function.lambda_handler`. The console file name is `lambda_function.py`.
4. Choose **Deploy**.

### Timeout and memory

1. Open **Configuration**, then **General configuration**, then **Edit**.
2. Memory: **128 MB**.
3. Timeout: **3** seconds.
4. Save.

### Test the function before you create the API

1. Open the **Test** tab.
2. Create a new event named `post-payment`.
3. Paste the JSON from [events/post-payment.json](events/post-payment.json).
4. Save and run the test.

Expected: `statusCode` **201**. The body contains `paymentId`, `status` `AUTHORIZED`, `amount` 499, and `currency` `INR`. The log line says `authorized` and the payment id. It does not print the token.

Then run [events/post-payment-invalid.json](events/post-payment-invalid.json). Expected: `statusCode` **400** and a message that `currency` is missing. There is no `paymentId`.

Optional checks, still on the Test tab:

- [events/get-payment.json](events/get-payment.json) returns 200, `paymentId` `pay-demo-1001`, status `AUTHORIZED`.
- [events/capture-payment.json](events/capture-payment.json) returns 200, status `CAPTURED`.

## 3. Create the HTTP API

1. Search for **API Gateway** and open it.
2. Choose **Create API**.
3. Find **HTTP API** and choose **Build**. Do not choose REST API.
4. Add an integration:
   - Integration type: **Lambda**.
   - Region: **ap-south-1**.
   - Lambda function: `sample-payments`.
5. API name: `sample-payments-api`.
6. Choose **Next**.

### Routes

The wizard may start with one route. Set that first route, then add the rest. Every route uses the same Lambda integration.

| Method | Path |
| --- | --- |
| GET | `/health` |
| POST | `/payments` |
| GET | `/payments/{paymentId}` |
| POST | `/payments/{paymentId}/capture` |

1. Set the first route to **GET** `/health`.
2. Add **POST** `/payments`.
3. Add **GET** `/payments/{paymentId}`.
4. Add **POST** `/payments/{paymentId}/capture`.
5. If the wizard added **ANY** `/{proxy+}` or a `$default` catch-all route, delete it. Leave only the four routes above.
6. Choose **Next**.

If the create wizard only accepts one route, finish the wizard with `GET /health`, then on the API page open **Routes**, choose **Create**, and add the other three. Point each one at the existing Lambda integration.

### Stage

1. Stage name: `$default`.
2. Turn **Auto-deploy** on.
3. Choose **Next**, review, then **Create**.

The console adds permission for API Gateway to invoke `sample-payments`. That permission is not the function’s execution role.

## 4. Call the API

1. On the API page, copy the **Invoke URL**. It looks like `https://abc123.execute-api.ap-south-1.amazonaws.com`.
2. Do not append a stage name. `$default` is already the root of that URL.

Set the URL in your shell, then run each call.

```bash
export API="https://abc123.execute-api.ap-south-1.amazonaws.com"
```

Health. Expected HTTP 200 and `"status": "ok"`.

```bash
curl -sS -D - "$API/health" -o /tmp/health.json
cat /tmp/health.json
```

Authorize. Expected HTTP 201, a new `paymentId`, and `"status": "AUTHORIZED"`.

```bash
curl -sS -D - -X POST "$API/payments" \
  -H "content-type: application/json" \
  -d '{"amount":499,"currency":"INR","paymentMethodToken":"pm_test_visa"}'
```

Copy the `paymentId` from that response. The next two calls use it. Below it is written as `PAYMENT_ID`.

```bash
export PAYMENT_ID="paste-the-id"
```

Missing currency. Expected HTTP 400 and no `paymentId`.

```bash
curl -sS -D - -X POST "$API/payments" \
  -H "content-type: application/json" \
  -d '{"amount":499,"paymentMethodToken":"pm_test_visa"}'
```

Card field. Expected HTTP 400. The body of the response must not echo the card field.

```bash
curl -sS -D - -X POST "$API/payments" \
  -H "content-type: application/json" \
  -d '{"amount":499,"currency":"INR","paymentMethodToken":"pm_test_visa","cardNumber":"do-not-send"}'
```

Read. Expected HTTP 200 and `"status": "AUTHORIZED"`.

```bash
curl -sS -D - "$API/payments/$PAYMENT_ID"
```

Capture. Expected HTTP 200 and `"status": "CAPTURED"`.

```bash
curl -sS -D - -X POST "$API/payments/$PAYMENT_ID/capture"
```

### If the call returns 403

API Gateway is not allowed to invoke the function. In API Gateway, open **Integrations**, select the Lambda integration, and attach `sample-payments` again so the console adds `lambda:InvokeFunction`. Then call `GET /health` again. Do not fix this by uploading [template.yaml](template.yaml).

### If the call returns 500

The function returned something other than `statusCode`, `headers`, and `body`. Open the Lambda editor and confirm it matches [src/lambda_function.py](src/lambda_function.py), then choose **Deploy** again.

## 5. Delete what you created

1. API Gateway: open `sample-payments-api` and delete the API.
2. Lambda: delete the function `sample-payments`.
3. IAM: delete the role `sample-payments-role`.
4. CloudWatch: delete the log group `/aws/lambda/sample-payments`.

Confirm the API and the function are gone before you leave.
