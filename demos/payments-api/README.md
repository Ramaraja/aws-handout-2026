# Sample Payments API

One Lambda function and one HTTP API. The function authorizes a payment, reads it back, and captures it. Nothing is charged. Do not send a card number, expiry, or CVV.

Create the resources in the AWS console. The clicks are in [SETUP.md](SETUP.md).

[template.yaml](template.yaml) is the same role, function, API, routes, and invoke permission written as CloudFormation. Read it beside the console steps. Do not upload it to create this demo.

## Names

| Piece | Name |
| --- | --- |
| Region | `ap-south-1` |
| Function | `sample-payments` |
| Handler in the console | `lambda_function.lambda_handler` |
| Role | `sample-payments-role` |
| HTTP API | `sample-payments-api` |
| Stage | `$default` |

## Routes

- `GET /health`
- `POST /payments`
- `GET /payments/{paymentId}`
- `POST /payments/{paymentId}/capture`

A valid authorize body is `amount`, `currency` (`INR` or `USD`), and `paymentMethodToken`. A missing field, a non-positive amount, an unknown currency, or a `cardNumber`, `pan`, `cvv`, or `cvc` field returns 400.

## Files

| File | Use |
| --- | --- |
| [src/lambda_function.py](src/lambda_function.py) | Paste this into the Lambda console. |
| [events/](events/) | Test events for the Lambda console, before the API exists. |
| [SETUP.md](SETUP.md) | Console steps. |
| [template.yaml](template.yaml) | CloudFormation reading copy. |
