# Force redeploy - OpenCellID test - 2026-07-20
# Force redeploy - payload debug - 2026-07-21
# Force redeploy - payload debug final - 2026-07-21
"""
Operational Signal Forge - Sensor Fusion Engine (SQS Version)
==============================================================
Ingests radar/thermal/acoustic/celltower sensor readings from SQS,
fuses them into a per-grid-cell probability score,
and writes results to DynamoDB.
"""

import json
import os
import time
from decimal import Decimal, ROUND_HALF_UP

import boto3

from celltower import score_celltower, lookup_celltower_location 


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ.get("DETECTIONS_TABLE", "signal-forge-detections-prod")
ALERT_TOPIC_ARN = os.environ.get("ALERT_TOPIC_ARN")
HIGH_CONFIDENCE_THRESHOLD = float(os.environ.get("HIGH_CONFIDENCE_THRESHOLD", "0.75"))

table = dynamodb.Table(TABLE_NAME)

# ---------------------------------------------------------------------------
# Decimal helpers — DynamoDB requires Decimal, never plain float
# ---------------------------------------------------------------------------

def d(value) -> Decimal:
    """Safe float → Decimal conversion for DynamoDB."""
    return Decimal(str(round(float(value), 6)))


def cell_id_from_coords(lat: float, lon: float) -> str:
    """
    Simple grid cell ID from lat/lon truncated to 4 decimal places.
    ~11m x ~11m cells at the equator — sufficient for USAR grid resolution.
    No external dependencies required.
    """
    lat_grid = int(float(lat) * 10000) / 10000
    lon_grid = int(float(lon) * 10000) / 10000
    return f"{lat_grid:.4f}_{lon_grid:.4f}"


# ---------------------------------------------------------------------------
# Signal scoring (0.0 – 1.0)
# ---------------------------------------------------------------------------

def score_radar(reading: dict) -> float:
    if not reading.get("void_detected"):
        return 0.0
    periodicity = float(reading.get("doppler_periodicity_hz", 0))
    amplitude = float(reading.get("doppler_amplitude", 0))
    breathing_band = 0.15 <= periodicity <= 0.6
    cardiac_band = 0.8 <= periodicity <= 2.0
    base = 0.6 if breathing_band else (0.45 if cardiac_band else 0.0)
    score = base + (0.35 * min(amplitude / 1.0, 1.0))
    depth = float(reading.get("depth_m", 0))
    if depth > 4:
        score *= 0.85
    return min(score, 1.0)


def score_thermal(reading: dict) -> float:
    delta_t = float(reading.get("delta_t_celsius", 0))
    hotspot_size = float(reading.get("hotspot_size_cm2", 0))
    if delta_t <= 0:
        return 0.0
    if 3 <= delta_t <= 8:
        temp_score = 0.7
    elif delta_t > 8:
        temp_score = 0.4
    else:
        temp_score = 0.3 * (delta_t / 3)
    size_score = min(hotspot_size / 600, 1.0)
    return min(temp_score * 0.7 + size_score * 0.3, 1.0)


def score_acoustic(reading: dict) -> float:
    score = 0.0
    if reading.get("tap_pattern_detected"):
        score += 0.6
    voice_likelihood = float(reading.get("voice_likelihood", 0.0))
    score += 0.4 * voice_likelihood
    snr = float(reading.get("snr_db", 0))
    if snr < 6:
        score *= 0.7
    return min(score, 1.0)


def fuse_scores(radar: float, thermal: float, acoustic: float) -> float:
    base = radar * 0.4 + thermal * 0.3 + acoustic * 0.3
    active = sum(1 for s in (radar, thermal, acoustic) if s > 0.3)
    bonus = {1: 0.0, 2: 0.10, 3: 0.20}.get(active, 0.0)
    return round(min(base + bonus, 1.0), 3)


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def get_or_create_cell(cell_id: str, lat: float, lon: float, site_id: str) -> dict:
    resp = table.get_item(Key={"cell_id": cell_id})
    if "Item" in resp:
        return resp["Item"]
    return {
        "cell_id": cell_id,
        "site_id": site_id or "unknown",
        "lat": d(lat),
        "lon": d(lon),
        "radar_score": d(0),
        "thermal_score": d(0),
        "acoustic_score": d(0),
        "fused_probability": d(0),
        "status": "unassigned",
        "created_at": int(time.time()),
    }


def score_celltower(reading: dict) -> float:
    """
    Score a cell tower geolocation based on the reported positioning accuracy
    returned by the OpenCellID lookup.
    """
    accuracy = float(reading.get("accuracy", 1000))
    if accuracy <= 20:
        return 1.0
    elif accuracy <= 50:
        return 0.9
    elif accuracy <= 100:
        return 0.8
    elif accuracy <= 250:
        return 0.6
    elif accuracy <= 500:
        return 0.4
    else:
        return 0.2


def process_reading(payload: dict) -> dict:
    sensor_type = payload["sensor_type"]
    
    if sensor_type == "celltower":
        # Special handling for celltower
        location = lookup_celltower_location(payload["reading"])
        lat = location["lat"]
        lon = location["lon"]
        signal_score = score_celltower(payload["reading"])
    else:
        # Standard sensors
        lat = float(payload["lat"])
        lon = float(payload["lon"])
        reading = payload["reading"]
        score_fn = {
            "radar": score_radar,
            "thermal": score_thermal,
            "acoustic": score_acoustic,
        }.get(sensor_type)
        signal_score = score_fn(reading)

    site_id = payload.get("site_id", "unknown")
    cell_id = cell_id_from_coords(lat, lon)
    cell = get_or_create_cell(cell_id, lat, lon, site_id)

    # Update this sensor's score
    cell[f"{sensor_type}_score"] = d(signal_score)
    cell[f"{sensor_type}_last_updated"] = int(time.time())

    # Fuse all three scores
    fused = fuse_scores(
        float(cell.get("radar_score", 0)),
        float(cell.get("thermal_score", 0)),
        float(cell.get("acoustic_score", 0)),
    )
    cell["fused_probability"] = d(fused)
    cell["updated_at"] = int(time.time())

    # Write to DynamoDB
    table.put_item(Item=cell)
    print(f"Wrote cell {cell_id} fused={fused:.3f} site={site_id}")

    alert = False
    if fused >= HIGH_CONFIDENCE_THRESHOLD and ALERT_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=ALERT_TOPIC_ARN,
                Subject="Signal Forge: High-confidence detection",
                Message=(
                    f"HIGH-CONFIDENCE DETECTION\n"
                    f"Cell: {cell_id} ({lat:.5f}, {lon:.5f})\n"
                    f"Site: {site_id}\n"
                    f"Fused probability: {fused}\n"
                    f"Radar: {float(cell.get('radar_score',0)):.2f}  "
                    f"Thermal: {float(cell.get('thermal_score',0)):.2f}  "
                    f"Acoustic: {float(cell.get('acoustic_score',0)):.2f}\n"
                    f"Dispatch search team immediately."
                ),
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    }
                },
            )
            alert = True
        except Exception as e:
            print(f"SNS alert failed: {e}")

    return {"cell_id": cell_id, "fused_probability": fused, "alert": alert}


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

# Errors that are worth retrying (transient AWS service issues)
RETRYABLE_ERRORS = (
    "ProvisionedThroughputExceededException",
    "RequestLimitExceeded",
    "ServiceUnavailable",
    "ThrottlingException",
    "InternalServerError",
)


def handler(event, context):
    results = []
    failed_records = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            body = record["body"]
            payload = json.loads(body) if isinstance(body, str) else body
            print("=== FULL PAYLOAD ===")
            print(json.dumps(payload, indent=2))
            print("=== END PAYLOAD ===")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[SKIP] Message {message_id}: malformed JSON — {e}")
            continue

        # DEBUG LINE - RIGHT HERE
        print(f"DEBUG: Sensor type: {payload.get('sensor_type')}, Keys: {list(payload.keys())}")

        # Validate required fields based on sensor_type
        sensor_type = payload.get("sensor_type")
        if sensor_type in ("radar", "thermal", "acoustic"):
            required = ("lat", "lon", "sensor_type", "reading")
            missing = [f for f in required if f not in payload]
            if missing:
                print(f"[SKIP] Message {message_id}: missing fields {missing} — discarding")
                continue

            try:
                lat = float(payload["lat"])
                lon = float(payload["lon"])
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    print(f"[SKIP] Message {message_id}: invalid coordinates ({lat}, {lon}) — discarding")
                    continue
            except (ValueError, TypeError) as e:
                print(f"[SKIP] Message {message_id}: bad coordinates — {e}")
                continue
        elif sensor_type == "celltower":
            required = ("sensor_type", "mcc", "mnc", "lac", "cid")
            missing = [f for f in required if f not in payload]
            if missing:
                print(f"[SKIP] Message {message_id}: missing fields {missing} — discarding")
                continue
        else:
            print(f"[SKIP] Message {message_id}: unknown sensor_type '{sensor_type}' — discarding")
            continue

        try:
            result = process_reading(payload)
            results.append(result)
            print(f"[OK] Message {message_id}: {result}")
        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if any(retryable in error_code for retryable in RETRYABLE_ERRORS):
                print(f"[RETRY] Message {message_id}: transient error '{error_code}' — will retry")
                failed_records.append(record)
            else:
                import traceback
                print(f"[ERROR] Message {message_id}: non-retryable error — {e}")
                print(traceback.format_exc())

    # If any records need retrying, raise so SQS handles retry/DLQ routing
    if failed_records:
        raise Exception(
            f"{len(failed_records)} record(s) failed with transient errors — retrying"
        )

    return {
        "processed": len(results),
        "alerts_fired": sum(1 for r in results if r.get("alert")),
    }