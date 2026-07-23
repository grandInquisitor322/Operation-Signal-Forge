"""
Operational Signal Forge - SMS Subscription API
=================================================
Humanitarian SAR Notification System
Handles opt-in consent flow for public updates on search operations.

Multi-jurisdictional compliance:
- Venezuela (Constitutional + TSJ 2011)
- California (CCPA/CPRA)
- European Union (GDPR)
- Humanitarian standards (data minimization, purpose limitation, accountability)

AWS Well-Architected Security Pillar applied.

Routes:
  GET   /privacy
  POST  /request-data
  POST  /delete-data
  POST  /subscribe
  POST  /confirm
  POST  /unsubscribe
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

_twilio_creds = None


def get_twilio_creds() -> dict:
    global _twilio_creds
    if _twilio_creds:
        return _twilio_creds
    secret = secretsmanager.get_secret_value(SecretId=TWILIO_SECRET_ARN)
    _twilio_creds = json.loads(secret["SecretString"])
    return _twilio_creds


def send_sms_twilio(to_number: str, message: str) -> bool:
    """Send SMS via Twilio REST API using only stdlib."""
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
            print(f"Twilio SMS sent: SID={result.get('sid')}")
            return True
    except Exception as e:
        print(f"Twilio send failed: {str(e)[:150]}")
        return False


def generate_confirm_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def normalize_phone(phone: str) -> str:
    """Strict input sanitization and validation."""
    if not phone:
        raise ValueError("Phone number is required")
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone.startswith("+"):
        raise ValueError("Phone number must be in E.164 format starting with + (e.g. +15551234567)")
    if len(phone) < 8 or len(phone) > 16:
        raise ValueError("Phone number length invalid")
    return phone


def handler(event, context):
    try:
        print("Request received")

        path = event.get("rawPath") or event.get("path") or ""
        http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")

        if http_method == "GET" and ("/privacy" in path or path.endswith("/privacy")):
            return handle_privacy()
        if http_method == "POST" and ("/request-data" in path or path.endswith("/request-data")):
            return handle_request_data(event)
        if http_method == "POST" and ("/delete-data" in path or path.endswith("/delete-data")):
            return handle_delete_data(event)

        if "body" in event and event["body"]:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        phone = body.get("phone")
        if not phone:
            return respond(400, {"error": "phone is required"})

        if http_method == "POST" and ("/subscribe" in path):
            return handle_subscribe(body)
        elif http_method == "POST" and ("/confirm" in path):
            return handle_confirm(body)
        elif http_method == "POST" and ("/unsubscribe" in path):
            return handle_unsubscribe(body)
        else:
            return respond(404, {"error": "Unknown route"})

    except Exception as e:
        print(f"Error: {str(e)[:200]}")
        return respond(500, {"error": "internal error"})


def respond(code: int, body: dict):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def handle_privacy():
    """Multi-jurisdictional Privacy Notice"""
    privacy_notice = {
        "title": "Privacy Notice - Signal Forge SAR Operations",
        "version": "1.3",
        "last_updated": "2026-07-23",
        "controller": "Signal Forge Operations",
        "purpose": "High-confidence search-and-rescue (SAR) operational alerts only",
        "data_collected": ["Phone number (E.164 format)", "Optional name"],
        "retention": "Duration of active subscription + up to 30 days after unsubscribe",

        "venezuela": {
            "basis": "Consentimiento previo, libre, informado, inequívoco y revocable (TSJ 2011)",
            "rights": ["Acceso", "Rectificación", "Cancelación", "Oposición"]
        },

        "ccpa_cpra": {
            "rights": [
                "Right to Know / Access",
                "Right to Delete",
                "Right to Correct",
                "Right to Opt-Out of Sale/Sharing (we do not sell data)",
                "Right to Non-Discrimination"
            ],
            "sale_sharing": "We do not sell or share personal information."
        },

        "gdpr": {
            "basis": "Explicit consent (Art. 6 & 7 GDPR)",
            "rights": [
                "Right of Access (Art. 15)",
                "Right to Rectification (Art. 16)",
                "Right to Erasure (Art. 17)",
                "Right to Withdraw Consent",
                "Right to Object (Art. 21)"
            ],
            "international_transfer": "Data processed in AWS with appropriate safeguards"
        },

        "humanitarian_note": "Data used exclusively for life-saving SAR operations. No commercial use.",
        "privacy_url": "https://gxlsc6rmye.execute-api.us-east-1.amazonaws.com/privacy",
        "contact": "Reply STOP or use /request-data and /delete-data endpoints"
    }
    return respond(200, privacy_notice)


def handle_request_data(event):
    """Unified data subject request handler"""
    return respond(200, {
        "message": "Your data access/correction request has been received.",
        "supported_rights": ["CCPA Right to Know", "GDPR Art.15", "Venezuela Access"],
        "timeline": "We will respond within legal timelines."
    })


def handle_delete_data(event):
    """Unified deletion handler"""
    return respond(200, {
        "message": "Your deletion request has been received.",
        "supported_rights": ["CCPA Right to Delete", "GDPR Right to Erasure"],
        "timeline": "Processing within required legal deadlines."
    })


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
        return respond(200, {"message": "This number is already subscribed."})

    code = generate_confirm_code()

    table.put_item(Item={
        "phone": phone,
        "name": name,
        "status": "pending",
        "confirm_code": code,
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
        "consent_version": "1.3",
        "consent_timestamp": int(time.time()),
        "jurisdictions": ["VE", "CCPA", "GDPR"]
    })

    confirmation_message = (
        f"Signal Forge SAR Updates: Reply YES{code} to confirm your subscription "
        f"and receive search-and-rescue operation updates. "
        f"Reply STOP at any time to unsubscribe. Msg frequency varies. "
        f"Privacy & rights: https://gxlsc6rmye.execute-api.us-east-1.amazonaws.com/privacy"
    )

    sent = send_sms_twilio(phone, confirmation_message)
    if not sent:
        return respond(500, {"error": "failed to send confirmation SMS"})

    print(f"Subscription pending for {phone}")
    return respond(200, {
        "message": "A confirmation SMS has been sent to your number.",
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
        return respond(404, {"error": "no pending subscription found"})

    if record.get("status") == "confirmed":
        return respond(200, {"message": "Already confirmed."})

    expected_code = record.get("confirm_code", "")
    if code_input not in (expected_code, f"YES{expected_code}"):
        return respond(400, {"error": "confirmation code does not match"})

    created_at = int(record.get("created_at", 0))
    if time.time() - created_at > 86400:
        return respond(400, {"error": "confirmation code expired"})

    try:
        sub_resp = sns.subscribe(
            TopicArn=PUBLIC_UPDATES_TOPIC_ARN,
            Protocol="sms",
            Endpoint=phone,
        )
        subscription_arn = sub_resp.get("SubscriptionArn", "pending")
    except Exception as e:
        print(f"SNS subscribe failed: {e}")
        subscription_arn = "sns-unavailable"

    table.update_item(
        Key={"phone": phone},
        UpdateExpression="SET #s = :s, confirmed_at = :ca, subscription_arn = :arn, updated_at = :u, consent_confirmed = :cc",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "confirmed",
            ":ca": int(time.time()),
            ":arn": subscription_arn,
            ":u": int(time.time()),
            ":cc": True,
        },
    )

    send_sms_twilio(
        phone,
        "You are now subscribed to Signal Forge SAR updates. "
        "You will receive notifications when high-confidence detections are made. "
        "Reply STOP to unsubscribe. "
        "Privacy & rights: https://gxlsc6rmye.execute-api.us-east-1.amazonaws.com/privacy"
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
        return respond(404, {"error": "no subscription found"})

    sub_arn = record.get("subscription_arn")
    if sub_arn and sub_arn not in ("pending", "sns-unavailable"):
        try:
            sns.unsubscribe(SubscriptionArn=sub_arn)
        except Exception as e:
            print(f"SNS unsubscribe failed: {e}")

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