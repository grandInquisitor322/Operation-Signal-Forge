"""
Operational Signal Forge - SMS Subscription API
=================================================
Handles opt-in consent flow for public updates on search operations.
Uses Twilio for SMS delivery (AWS SNS SMS not available on this account).

Routes:
  POST /subscribe    -> { "phone": "+15551234567", "name": "Edward" }
  POST /confirm      -> { "phone": "+15551234567", "code": "YES123" }
  POST /unsubscribe  -> { "phone": "+15551234567" }
"""

import json
import os
import time
import random
import string
import urllib.request
import urllib.parse
import base64
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
secretsmanager = boto3.client("secretsmanager")

SUBSCRIBERS_TABLE = os.environ.get("SUBSCRIBERS_TABLE", "signal-forge-subscribers")
PUBLIC_UPDATES_TOPIC_ARN = os.environ.get("PUBLIC_UPDATES_TOPIC_ARN")
TWILIO_SECRET_ARN = os.environ.get("TWILIO_SECRET_ARN", "signal-forge/twilio")

table = dynamodb.Table(SUBSCRIBERS_TABLE)

# Cache Twilio credentials in memory across warm invocations
_twilio_creds = None


def get_twilio_creds() -> dict:
    global _twilio_creds
    if _twilio_creds:
        return _twilio_creds
    secret = secretsmanager.get_secret_value(SecretId=TWILIO_SECRET_ARN)
    _twilio_creds = json.loads(secret["SecretString"])
    return _twilio_creds


def send_sms_twilio(to_number: str, message: str) -> bool:
    """Send SMS via Twilio REST API using only stdlib (no requests dependency)."""
    creds = get_twilio_creds()
    account_sid = creds["account_sid"]
    auth_token = creds["auth_token"]
    from_number = creds["from_number"]

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    data = urllib.parse.urlencode({
        "To": to_number,
        "From": from_number,
        "Body": message,
    }).encode("utf-8")

    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"Twilio SMS sent: SID={result.get('sid')} status={result.get('status')}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Twilio HTTP error {e.code}: {error_body}")
        return False
    except Exception as e:
        print(f"Twilio send failed: {e}")
        return False


def generate_confirm_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone.startswith("+"):
        raise ValueError("Phone number must be in E.164 format starting with + (e.g. +15551234567)")
    if len(phone) < 8 or len(phone) > 16:
        raise ValueError("Phone number length invalid")
    return phone

def handler(event, context):
    try:
        print("Full event received:", json.dumps(event, default=str))
        
        # Try multiple ways to get the route
        path = event.get("rawPath") or event.get("path") or ""
        http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")
        route_key = event.get("routeKey")

        print(f"Detected - path: {path}, method: {http_method}, routeKey: {route_key}")

        # Parse body
        if "body" in event and event["body"]:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        phone = body.get("phone")

        if not phone:
            return respond(400, {"error": "phone is required"})

        # Route matching
        if http_method == "POST" and ("/subscribe" in path):
            return handle_subscribe(body)
        elif http_method == "POST" and ("/confirm" in path):
            return handle_confirm(body)
        elif http_method == "POST" and ("/unsubscribe" in path):
            return handle_unsubscribe(body)
        else:
            return respond(404, {"error": f"Unknown route - path: {path}, method: {http_method}"})

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return respond(500, {"error": "internal error"})


def respond(code: int, body: dict):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }



def handle_subscribe(body: dict):
    phone_raw = body.get("phone", "").strip()
    name = body.get("name", "").strip()[:100]

    if not phone_raw:
        return respond(400, {"error": "phone is required"})

    try:
        phone = normalize_phone(phone_raw)
    except ValueError as e:
        return respond(400, {"error": str(e)})

    existing = table.get_item(Key={"phone": phone}).get("Item")
    if existing and existing.get("status") == "confirmed":
        return respond(200, {
            "message": "This number is already subscribed to Signal Forge updates."
        })

    code = generate_confirm_code()

    table.put_item(Item={
        "phone": phone,
        "name": name,
        "status": "pending",
        "confirm_code": code,
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    })

    confirmation_message = (
        f"Signal Forge SAR Updates: Reply YES{code} to confirm your subscription "
        f"and receive search-and-rescue operation updates. "
        f"Reply STOP at any time to unsubscribe. Msg frequency varies."
    )

    sent = send_sms_twilio(phone, confirmation_message)
    if not sent:
        return respond(500, {"error": "failed to send confirmation SMS"})

    print(f"Subscription pending for {phone} ({name}), code={code}")
    return respond(200, {
        "message": (
            "A confirmation SMS has been sent to your number. "
            "Reply with YES followed by your confirmation code to complete your subscription."
        ),
        "status": "pending"
    })


def handle_confirm(body: dict):
    phone_raw = body.get("phone", "").strip()
    code_input = body.get("code", "").strip().upper()

    if not phone_raw or not code_input:
        return respond(400, {"error": "phone and code are required"})

    try:
        phone = normalize_phone(phone_raw)
    except ValueError as e:
        return respond(400, {"error": str(e)})

    record = table.get_item(Key={"phone": phone}).get("Item")
    if not record:
        return respond(404, {"error": "no pending subscription found for this number"})

    if record.get("status") == "confirmed":
        return respond(200, {"message": "Already confirmed — you are subscribed."})

    expected_code = record.get("confirm_code", "")
    if code_input not in (expected_code, f"YES{expected_code}"):
        return respond(400, {"error": "confirmation code does not match"})

    created_at = int(record.get("created_at", 0))
    if time.time() - created_at > 86400:
        return respond(400, {
            "error": "confirmation code has expired — please subscribe again"
        })

    # Subscribe to SNS public updates topic
    try:
        sub_resp = sns.subscribe(
            TopicArn=PUBLIC_UPDATES_TOPIC_ARN,
            Protocol="sms",
            Endpoint=phone,
        )
        subscription_arn = sub_resp.get("SubscriptionArn", "pending")
    except Exception as e:
        print(f"SNS subscribe failed (non-fatal for now): {e}")
        subscription_arn = "sns-unavailable"

    table.update_item(
        Key={"phone": phone},
        UpdateExpression=(
            "SET #s = :s, confirmed_at = :ca, subscription_arn = :arn, updated_at = :u"
        ),
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "confirmed",
            ":ca": int(time.time()),
            ":arn": subscription_arn,
            ":u": int(time.time()),
        },
    )

    # Welcome SMS via Twilio
    send_sms_twilio(
        phone,
        "You are now subscribed to Signal Forge SAR updates. "
        "You will receive notifications when high-confidence detections are made. "
        "Reply STOP at any time to unsubscribe."
    )

    print(f"Subscription confirmed for {phone}")
    return respond(200, {
        "message": "You are now subscribed to Signal Forge updates.",
        "status": "confirmed"
    })


def handle_unsubscribe(body: dict):
    phone_raw = body.get("phone", "").strip()

    if not phone_raw:
        return respond(400, {"error": "phone is required"})

    try:
        phone = normalize_phone(phone_raw)
    except ValueError as e:
        return respond(400, {"error": str(e)})

    record = table.get_item(Key={"phone": phone}).get("Item")
    if not record:
        return respond(404, {"error": "no subscription found for this number"})

    sub_arn = record.get("subscription_arn")
    if sub_arn and sub_arn not in ("pending", "sns-unavailable"):
        try:
            sns.unsubscribe(SubscriptionArn=sub_arn)
        except Exception as e:
            print(f"SNS unsubscribe failed (non-fatal): {e}")

    table.update_item(
        Key={"phone": phone},
        UpdateExpression="SET #s = :s, unsubscribed_at = :ua, updated_at = :u",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "unsubscribed",
            ":ua": int(time.time()),
            ":u": int(time.time()),
        },
    )

    print(f"Unsubscribed {phone}")
    return respond(200, {
        "message": "You have been unsubscribed from Signal Forge updates.",
        "status": "unsubscribed"
    })


def respond(code: int, body: dict):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }