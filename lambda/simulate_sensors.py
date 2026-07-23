"""
Operational Signal Forge - Field Sensor Simulator
====================================================
Pushes synthetic radar/thermal/acoustic readings into the SQS ingest
queue so you can test the fusion engine and dashboard before real field
sensor units are wired in.

Usage:
    pip install boto3 --break-system-packages
    python simulate_sensors.py --site caracas-site-7 --duration 120 --profile signal-forge
"""

import argparse
import json
import random
import time
import boto3

SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/465362303774/signal-forge-sensor-ingest"

HOTSPOTS = [
    {"lat": 10.48065, "lon": -66.90362},
    {"lat": 10.48041, "lon": -66.90398},
]


def jitter(coord, spread=0.0006):
    return coord + random.uniform(-spread, spread)


def make_radar_reading(is_hotspot):
    if is_hotspot:
        return {
            "void_detected": True,
            "doppler_periodicity_hz": round(random.uniform(0.18, 0.5), 3),
            "doppler_amplitude": round(random.uniform(0.5, 0.95), 2),
            "depth_m": round(random.uniform(1.0, 3.5), 1),
        }
    return {
        "void_detected": random.random() < 0.2,
        "doppler_periodicity_hz": round(random.uniform(0, 3), 3),
        "doppler_amplitude": round(random.uniform(0, 0.3), 2),
        "depth_m": round(random.uniform(0.5, 6), 1),
    }


def make_thermal_reading(is_hotspot):
    if is_hotspot:
        return {
            "delta_t_celsius": round(random.uniform(3.5, 7.5), 1),
            "hotspot_size_cm2": round(random.uniform(300, 900), 0),
            "ambient_c": round(random.uniform(24, 30), 1),
        }
    return {
        "delta_t_celsius": round(random.uniform(0, 2.5), 1),
        "hotspot_size_cm2": round(random.uniform(0, 200), 0),
        "ambient_c": round(random.uniform(24, 30), 1),
    }


def make_acoustic_reading(is_hotspot):
    if is_hotspot:
        return {
            "tap_pattern_detected": random.random() < 0.6,
            "voice_likelihood": round(random.uniform(0.3, 0.8), 2),
            "snr_db": round(random.uniform(8, 18), 1),
        }
    return {
        "tap_pattern_detected": False,
        "voice_likelihood": round(random.uniform(0, 0.15), 2),
        "snr_db": round(random.uniform(2, 10), 1),
    }


def emit_reading(sqs, site_id, sensor_type, lat, lon, reading):
    payload = {
        "sensor_id": f"{sensor_type.upper()}-{random.randint(1, 30):03d}",
        "sensor_type": sensor_type,
        "lat": lat,
        "lon": lon,
        "timestamp": int(time.time()),
        "reading": reading,
        "site_id": site_id,
    }
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(payload),
    )
    return payload


def run(site_id, duration_seconds, interval_seconds=2, profile=None):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    sqs = session.client("sqs", region_name="us-east-1")

    print(f"Simulating field sensors for site '{site_id}' for {duration_seconds}s...")
    print(f"Pushing to SQS: {SQS_QUEUE_URL}")
    end_time = time.time() + duration_seconds
    builders = {
        "radar": make_radar_reading,
        "thermal": make_thermal_reading,
        "acoustic": make_acoustic_reading,
    }

    while time.time() < end_time:
        use_hotspot = random.random() < 0.4
        if use_hotspot:
            base = random.choice(HOTSPOTS)
        else:
            anchor = random.choice(HOTSPOTS)
            base = {
                "lat": anchor["lat"] + random.uniform(-0.002, 0.002),
                "lon": anchor["lon"] + random.uniform(-0.002, 0.002),
            }

        lat = jitter(base["lat"], 0.00015)
        lon = jitter(base["lon"], 0.00015)
        sensor_type = random.choice(list(builders.keys()))
        reading = builders[sensor_type](use_hotspot)

        emit_reading(sqs, site_id, sensor_type, lat, lon, reading)
        print(f"  -> {sensor_type:8s} @ ({lat:.5f},{lon:.5f})  hotspot={use_hotspot}")
        time.sleep(interval_seconds)

    print("Simulation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="caracas-site-7")
    parser.add_argument("--duration", type=int, default=120, help="seconds to run")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between readings")
    parser.add_argument("--profile", default=None, help="AWS CLI profile to use")
    args = parser.parse_args()
    run(args.site, args.duration, args.interval, args.profile)