# Demos

Companion projects for the course. The module labs stay as they are. These folders are extra examples you create in the AWS console.

## Payments API

[payments-api](payments-api/README.md) is one Python Lambda, `sample-payments`, behind an HTTP API, `sample-payments-api`, in `ap-south-1`.

Create it by following [payments-api/SETUP.md](payments-api/SETUP.md). That guide is the Lambda console and the API Gateway console. A CloudFormation template of the same resources is in the folder for reading. The setup guide does not deploy that file.

Routes:

| Call | Result |
| --- | --- |
| `GET /health` | 200 and a short status |
| `POST /payments` with amount, currency, and a fake payment-method token | 201, a new `paymentId`, status `AUTHORIZED` |
| `POST /payments` with a bad body, or a card number or CVV | 400, no payment id |
| `GET /payments/{paymentId}` | 200 and status `AUTHORIZED` |
| `POST /payments/{paymentId}/capture` | 200 and status `CAPTURED` |

The function does not charge a card.

## Invoice bucket

[s3-invoices](s3-invoices/README.md) is the Module 8 bucket in `ap-south-1`. Create it by following [s3-invoices/SETUP.md](s3-invoices/SETUP.md).

You enable versioning and SSE-S3, upload `invoice.txt` twice, download the older version, add a lifecycle rule for noncurrent versions, and allow `sample-create-order-role` to get and put objects. Block Public Access stays on. You do not create a replication rule.

Later course demos, such as queue fan-out, are not in this folder yet.
