"""
Operational Signal Forge - Field Gateway with Store-and-Forward Buffering
============================================================================
Runs on a small device at the field site (laptop, Raspberry Pi, etc.) that
sits between the sensor units and AWS. Sensor units talk to this gateway
over a local connection (serial, local MQTT broker, etc - adapt the
read_from_sensor() stub below to your actual hardware interface).

The key design point for unreliable power/internet (e.g. outages affecting
the site): readings are written to a local on-disk queue FIRST, then a
separate forwarding loop tries to push them to AWS IoT Core. If the
connection is down, readings simply accumulate on disk - nothing is lost,
and a recovering connection drains the backlog instead of dropping
whatever happened to come in while service was out.

This also tolerates the gateway device itself rebooting (e.g. after a
power blip) since the queue lives on disk, not in memory.

Run as two processes (or two threads):
    python field_gateway.py --mode collect    # writes incoming readings to queue
    python field_gateway.py --mode forward    # drains queue to AWS when online

Requires:
    pip install awsiotsdk --break-system-packages
"""

import argparse
import json
import os
import sqlite3
import time
import socket
import uuid

QUEUE_DB_PATH = os.environ.get("SIGNAL_FORGE_QUEUE_DB", "signal_forge_queue.sqlite3")
IOT_ENDPOINT = os.environ.get("SIGNAL_FORGE_IOT_ENDPOINT")  # e.g. xxxx.iot.us-east-1.amazonaws.com
SITE_ID = os.environ.get("SIGNAL_FORGE_SITE_ID", "caracas-site-7")
TOPIC_TEMPLATE = "signal-forge/sensors/{sensor_id}/reading"

MAX_FORWARD_BATCH = 25
CONNECTIVITY_CHECK_INTERVAL = 10  # seconds between retry attempts when offline


# ---------------------------------------------------------------------------
# Local queue (SQLite - durable across power loss / reboot, zero setup)
# ---------------------------------------------------------------------------

def init_queue():
    conn = sqlite3.connect(QUEUE_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reading_queue (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            queued_at INTEGER NOT NULL,
            sent INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def enqueue_reading(conn, payload: dict):
    conn.execute(
        "INSERT INTO reading_queue (id, payload, queued_at, sent) VALUES (?, ?, ?, 0)",
        (str(uuid.uuid4()), json.dumps(payload), int(time.time())),
    )
    conn.commit()


def get_unsent_batch(conn, limit=MAX_FORWARD_BATCH):
    rows = conn.execute(
        "SELECT id, payload FROM reading_queue WHERE sent = 0 ORDER BY queued_at ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return rows


def mark_sent(conn, row_id):
    conn.execute("UPDATE reading_queue SET sent = 1 WHERE id = ?", (row_id,))
    conn.commit()


def prune_sent(conn, older_than_seconds=86400):
    """Periodically clear out old sent records so the DB doesn't grow forever."""
    cutoff = int(time.time()) - older_than_seconds
    conn.execute("DELETE FROM reading_queue WHERE sent = 1 AND queued_at < ?", (cutoff,))
    conn.commit()


def queue_depth(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM reading_queue WHERE sent = 0").fetchone()[0]


# ---------------------------------------------------------------------------
# Collection mode: pull readings from sensor hardware, push into queue
# ---------------------------------------------------------------------------

def read_from_sensor():
    """
    STUB - replace with your actual hardware read.
    Should return a dict matching the shape fusion_engine.py expects, e.g.:
    {
      "sensor_id": "GPR-014", "sensor_type": "radar",
      "lat": 10.4806, "lon": -66.9036, "timestamp": <unix ts>,
      "reading": {...}, "site_id": SITE_ID
    }
    Return None if no new reading is available right now.
    """
    raise NotImplementedError(
        "Wire this up to your sensor unit's actual interface "
        "(serial port, local MQTT broker, GPIO, etc.)"
    )


def run_collect_loop(poll_interval=1.0):
    conn = init_queue()
    print(f"[collect] writing to local queue at {QUEUE_DB_PATH}")
    while True:
        try:
            reading = read_from_sensor()
            if reading:
                enqueue_reading(conn, reading)
                print(f"[collect] queued reading from {reading.get('sensor_id')} "
                      f"(backlog: {queue_depth(conn)})")
        except NotImplementedError as e:
            print(f"[collect] {e}")
            return
        except Exception as e:
            # Never let a single bad reading crash collection - log and continue.
            print(f"[collect] error reading sensor, skipping: {e}")
        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Forward mode: drain queue to AWS IoT Core when connectivity is available
# ---------------------------------------------------------------------------

def is_online(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False


def run_forward_loop():
    """
    Drains the local queue to AWS IoT Core whenever connectivity is up.
    Uses MQTT over TLS via the AWS IoT Device SDK. Falls back to idle-waiting
    when offline, and resumes draining the backlog as soon as the network
    recovers - no readings are lost during an outage, only delayed.
    """
    from awscrt import mqtt, io
    from awsiot import mqtt_connection_builder

    if not IOT_ENDPOINT:
        print("[forward] SIGNAL_FORGE_IOT_ENDPOINT not set, cannot connect to AWS IoT Core")
        return

    conn = init_queue()
    mqtt_connection = None

    def ensure_connected():
        nonlocal mqtt_connection
        if mqtt_connection is not None:
            return True
        if not is_online():
            return False
        try:
            mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=IOT_ENDPOINT,
                cert_filepath=os.environ["SIGNAL_FORGE_CERT_PATH"],
                pri_key_filepath=os.environ["SIGNAL_FORGE_KEY_PATH"],
                ca_filepath=os.environ["SIGNAL_FORGE_ROOT_CA_PATH"],
                client_id=f"signal-forge-gateway-{SITE_ID}",
                clean_session=False,
                keep_alive_secs=30,
            )
            mqtt_connection.connect().result()
            print("[forward] connected to AWS IoT Core")
            return True
        except Exception as e:
            print(f"[forward] connection failed: {e}")
            mqtt_connection = None
            return False

    last_prune = time.time()

    while True:
        if not ensure_connected():
            print(f"[forward] offline - backlog: {queue_depth(conn)} readings waiting")
            time.sleep(CONNECTIVITY_CHECK_INTERVAL)
            continue

        batch = get_unsent_batch(conn)
        if not batch:
            time.sleep(CONNECTIVITY_CHECK_INTERVAL)
        else:
            for row_id, payload_json in batch:
                payload = json.loads(payload_json)
                topic = TOPIC_TEMPLATE.format(sensor_id=payload.get("sensor_id", "unknown"))
                try:
                    mqtt_connection.publish(
                        topic=topic,
                        payload=payload_json,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                    )
                    mark_sent(conn, row_id)
                except Exception as e:
                    print(f"[forward] publish failed, will retry: {e}")
                    mqtt_connection = None  # force reconnect next loop
                    break

        if time.time() - last_prune > 3600:
            prune_sent(conn)
            last_prune = time.time()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["collect", "forward"], required=True)
    args = parser.parse_args()

    if args.mode == "collect":
        run_collect_loop()
    else:
        run_forward_loop()