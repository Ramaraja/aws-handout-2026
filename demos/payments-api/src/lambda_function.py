import json
import uuid

CARD_FIELDS = {"cardnumber", "pan", "cvv", "cvc"}
CURRENCIES = {"INR", "USD"}


def lambda_handler(event, context):
    method = (event.get("requestContext") or {}).get("http", {}).get("method", "")
    path = event.get("rawPath") or ""
    params = event.get("pathParameters") or {}

    if method == "GET" and path == "/health":
        return _respond(200, {"status": "ok"})

    if method == "POST" and path == "/payments":
        body, error = _payment_request(event)
        if error:
            return _respond(400, {"message": error})
        payment_id = str(uuid.uuid4())
        print("authorized", payment_id)
        return _respond(
            201,
            {
                "paymentId": payment_id,
                "status": "AUTHORIZED",
                "amount": body["amount"],
                "currency": body["currency"],
            },
        )

    payment_id = params.get("paymentId")
    if method == "GET" and payment_id and path == f"/payments/{payment_id}":
        print("read", payment_id)
        return _respond(200, {"paymentId": payment_id, "status": "AUTHORIZED"})

    if method == "POST" and payment_id and path == f"/payments/{payment_id}/capture":
        print("captured", payment_id)
        return _respond(200, {"paymentId": payment_id, "status": "CAPTURED"})

    return _respond(404, {"message": "Not found"})


def _payment_request(event):
    if event.get("isBase64Encoded"):
        return None, "Request body must be JSON"
    raw = event.get("body") or ""
    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return None, "Request body must be JSON"
    if not isinstance(body, dict):
        return None, "Request body must be a JSON object"

    lowered = {str(key).lower() for key in body}
    if lowered & CARD_FIELDS:
        return None, "Do not send card numbers or a CVV"

    missing = [
        name
        for name in ("amount", "currency", "paymentMethodToken")
        if name not in body or body[name] in ("", None)
    ]
    if missing:
        return None, "Missing " + ", ".join(missing)

    try:
        amount = float(body["amount"])
    except (TypeError, ValueError):
        return None, "amount must be a positive number"
    if amount <= 0:
        return None, "amount must be a positive number"

    currency = str(body["currency"]).upper()
    if currency not in CURRENCIES:
        return None, "currency must be INR or USD"

    token = str(body["paymentMethodToken"]).strip()
    if not token:
        return None, "paymentMethodToken is required"

    return {"amount": amount, "currency": currency}, None


def _respond(status, payload):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload),
    }
