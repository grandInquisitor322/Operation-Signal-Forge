"""
Operation Signal Forge — Starlink Sensor Module
================================================
Translates Starlink-specific observations into a standardized
observation the Fusion Engine can consume.

Owns: parsing, validation, Starlink-specific scoring, metadata.
Does NOT own: fusion, DynamoDB, alerts, orchestration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Public entry point (one per sensor module)
# ---------------------------------------------------------------------------

def process(raw: dict) -> dict:
    """
    Validate and transform a raw Starlink event into the standard
    observation shape expected by the Fusion Engine.

    Raises ValueError on invalid input (caller decides skip vs DLQ).
    """
    validated = _validate(raw)
    score = _score_starlink(validated)
    lat, lon = _resolve_location(validated)

    return {
        "sensor_type": "starlink",
        "site_id": validated["site_id"],
        "lat": lat,
        "lon": lon,
        "starlink_score": score,
        "metadata": _build_metadata(validated),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("Starlink payload must be a dict")

    if not raw.get("site_id"):
        raise ValueError("Starlink payload requires site_id")

    # Minimum: either explicit lat/lon OR enough context to geolocate later
    has_coords = "lat" in raw and "lon" in raw
    has_pass_context = any(
        k in raw for k in ("elevation_deg", "azimuth_deg", "satellite_id", "pass_timestamp")
    )
    if not has_coords and not has_pass_context:
        raise ValueError(
            "Starlink payload needs lat/lon or pass context "
            "(elevation_deg / azimuth_deg / satellite_id / pass_timestamp)"
        )

    if has_coords:
        lat, lon = float(raw["lat"]), float(raw["lon"])
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError(f"Invalid coordinates: ({lat}, {lon})")

    return raw


# ---------------------------------------------------------------------------
# Starlink-specific scoring (0.0 – 1.0)
# Encapsulated — Fusion Engine never sees these heuristics
# ---------------------------------------------------------------------------

def _score_starlink(obs: dict) -> float:
    """
    Heuristic confidence that a Starlink observation supports presence
    / localization at the reported location.

    Factors (tunable against field data later):
      - elevation (higher passes = stronger / more reliable)
      - reported signal quality if present
      - observation_source reliability
    """
    score = 0.35  # base when we have a valid observation

    elev = obs.get("elevation_deg")
    if elev is not None:
        elev = float(elev)
        if elev >= 40:
            score += 0.35
        elif elev >= 20:
            score += 0.20
        elif elev >= 10:
            score += 0.10

    # Optional link quality (0–1 or dB-style; normalize if present)
    quality = obs.get("signal_quality")
    if quality is not None:
        try:
            q = float(quality)
            if q > 1.0:  # assume dB-ish scale, clamp roughly
                q = min(q / 20.0, 1.0)
            score += 0.25 * max(0.0, min(q, 1.0))
        except (TypeError, ValueError):
            pass

    source = str(obs.get("observation_source", "")).lower()
    if source in ("field_terminal", "ground_station", "rf_sniffer"):
        score += 0.05

    return round(min(score, 1.0), 3)


def _resolve_location(obs: dict) -> tuple[float, float]:
    """Prefer explicit coordinates; placeholder for future orbital geolocation."""
    if "lat" in obs and "lon" in obs:
        return float(obs["lat"]), float(obs["lon"])

    # Future: orbital prediction → ground footprint.
    # For now require coords so Fusion always gets a cell.
    raise ValueError(
        "Starlink geolocation from pass geometry not implemented yet; "
        "provide lat/lon on the observation"
    )


def _build_metadata(obs: dict) -> dict[str, Any]:
    """Keep Starlink-specific detail out of the Fusion Engine contract."""
    keys = (
        "satellite_id",
        "pass_timestamp",
        "elevation_deg",
        "azimuth_deg",
        "range_km",
        "constellation",
        "observation_source",
        "signal_quality",
    )
    return {k: obs[k] for k in keys if k in obs}