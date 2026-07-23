"""
OpenCellID Sensor Module
========================
Processes cell tower data (MCC, MNC, LAC, CID) via OpenCellID API
and returns a location + confidence score.
"""

import json
import os
import urllib.request
import urllib.error

OPENCELLID_API_KEY = os.environ.get("OPENCELLID_API_KEY")

def lookup_celltower_location(reading: dict) -> dict:
    """
    Resolve a cell tower (MCC/MNC/LAC/CID) to latitude/longitude using
    the OpenCellID API.
    """
    if not OPENCELLID_API_KEY:
        raise RuntimeError("OPENCELLID_API_KEY environment variable is not set")

    payload = {
        "token": OPENCELLID_API_KEY,
        "radio": reading.get("radio", "lte"),
        "mcc": int(reading["mcc"]),
        "mnc": int(reading["mnc"]),
        "cells": [{
            "lac": int(reading["lac"]),
            "cid": int(reading["cid"])
        }]
    }

    data = urllib.parse.urlencode(payload).encode("utf-8")
    url = "https://us1.unwiredlabs.com/v2/process.php"

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        if data.get("status") != "ok":
            raise RuntimeError(f"OpenCellID lookup failed: {data}")

        return {
            "lat": float(data["lat"]),
            "lon": float(data["lon"]),
            "accuracy": float(data.get("accuracy", 1000)),
        }

    except Exception as e:
        raise RuntimeError(f"OpenCellID lookup failed: {e}")


def score_celltower(reading: dict) -> dict:
    """
    Process cell tower data and return location + score.
    reading: {
        "mcc": int,
        "mnc": int,
        "lac": int,
        "cid": int,
        "signal_strength": int (optional)
    }
    """
    try:
        mcc = reading.get("mcc")
        mnc = reading.get("mnc")
        lac = reading.get("lac")
        cid = reading.get("cid")

        if not all([mcc, mnc, lac, cid]):
            return {"lat": 0, "lon": 0, "score": 0.0, "error": "Missing cell tower parameters"}

        # Call OpenCellID API
        url = f"https://opencellid.org/cell/get?key={OPENCELLID_API_KEY}&mcc={mcc}&mnc={mnc}&lac={lac}&cid={cid}&format=json"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        lat = float(data.get("lat", 0))
        lon = float(data.get("lon", 0))
        accuracy = float(data.get("accuracy", 0))  # meters

        # Confidence score based on accuracy and signal (if provided)
        base_score = 0.8 if accuracy < 1000 else 0.5
        signal = reading.get("signal_strength", 0)
        if signal > 0:
            base_score *= (signal / 100)  # normalize

        return {
            "lat": lat,
            "lon": lon,
            "score": round(min(base_score, 1.0), 3),
            "accuracy_m": accuracy,
            "source": "opencellid"
        }

    except urllib.error.HTTPError as e:
        return {"lat": 0, "lon": 0, "score": 0.0, "error": f"API error: {e.code}"}
    except Exception as e:
        return {"lat": 0, "lon": 0, "score": 0.0, "error": str(e)}


# Register this sensor type
SENSOR_TYPES = {
    "celltower": score_celltower,
    # ... existing types will be merged in fusion_engine.py
}