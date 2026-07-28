"""
Regression: existing sensors still work after Starlink integration
-----------------------------------------------------------------
Checks radar, thermal, acoustic, and celltower paths through
process_reading() without Starlink-specific behavior leaking in.
"""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from decimal import Decimal

LAMBDA_DIR = Path(r"C:\Users\Samson\signal-forge\lambda")
sys.path.insert(0, str(LAMBDA_DIR))

mock_table = MagicMock()
mock_sns = MagicMock()
mock_dynamodb = MagicMock()
mock_dynamodb.Table.return_value = mock_table

_store = {}

def _get_item(Key):
    cell_id = Key["cell_id"]
    if cell_id in _store:
        return {"Item": dict(_store[cell_id])}
    return {}

def _put_item(Item):
    _store[Item["cell_id"]] = dict(Item)
    return {}

mock_table.get_item.side_effect = lambda **kw: _get_item(kw["Key"])
mock_table.put_item.side_effect = lambda **kw: _put_item(kw["Item"])

with patch("boto3.resource", return_value=mock_dynamodb), \
     patch("boto3.client", return_value=mock_sns):
    import fusion_engine as fe


def _reset():
    _store.clear()
    mock_table.reset_mock()
    mock_sns.reset_mock()
    mock_table.get_item.side_effect = lambda **kw: _get_item(kw["Key"])
    mock_table.put_item.side_effect = lambda **kw: _put_item(kw["Item"])


def _assert_common(result, cell, sensor_type):
    assert "cell_id" in result
    assert "fused_probability" in result
    assert 0.0 <= result["fused_probability"] <= 1.0
    assert cell["status"] == "unassigned"
    assert f"{sensor_type}_score" in cell
    assert float(cell[f"{sensor_type}_score"]) >= 0
    # Starlink must not be force-written by non-starlink sensors
    # (field may exist as 0 from get_or_create_cell — that is OK)
    if "starlink_score" in cell:
        # For a brand-new cell from a non-starlink sensor, score stays 0
        pass


def test_radar():
    print("\n[RADAR]")
    _reset()
    payload = {
        "sensor_type": "radar",
        "site_id": "site-radar",
        "lat": 10.50,
        "lon": -66.90,
        "reading": {
            "void_detected": True,
            "doppler_periodicity_hz": 0.3,
            "doppler_amplitude": 0.8,
            "depth_m": 2.0,
        },
    }
    result = fe.process_reading(payload)
    cell = _store[result["cell_id"]]
    score = float(cell["radar_score"])
    print(f"  radar_score={score} fused={result['fused_probability']}")
    assert score > 0.5  # breathing band + amplitude
    assert float(cell.get("starlink_score", 0)) == 0
    _assert_common(result, cell, "radar")
    print("  PASS")


def test_thermal():
    print("\n[THERMAL]")
    _reset()
    payload = {
        "sensor_type": "thermal",
        "site_id": "site-thermal",
        "lat": 10.51,
        "lon": -66.91,
        "reading": {
            "delta_t_celsius": 5.0,
            "hotspot_size_cm2": 400,
        },
    }
    result = fe.process_reading(payload)
    cell = _store[result["cell_id"]]
    score = float(cell["thermal_score"])
    print(f"  thermal_score={score} fused={result['fused_probability']}")
    assert score > 0.3
    assert float(cell.get("starlink_score", 0)) == 0
    _assert_common(result, cell, "thermal")
    print("  PASS")


def test_acoustic():
    print("\n[ACOUSTIC]")
    _reset()
    payload = {
        "sensor_type": "acoustic",
        "site_id": "site-acoustic",
        "lat": 10.52,
        "lon": -66.92,
        "reading": {
            "tap_pattern_detected": True,
            "voice_likelihood": 0.7,
            "snr_db": 12,
        },
    }
    result = fe.process_reading(payload)
    cell = _store[result["cell_id"]]
    score = float(cell["acoustic_score"])
    print(f"  acoustic_score={score} fused={result['fused_probability']}")
    assert score > 0.5
    assert float(cell.get("starlink_score", 0)) == 0
    _assert_common(result, cell, "acoustic")
    print("  PASS")


def test_celltower():
    print("\n[CELLTOWER]")
    _reset()
    payload = {
        "sensor_type": "celltower",
        "site_id": "site-cell",
        "reading": {
            "mcc": 734,
            "mnc": 1,
            "lac": 100,
            "cid": 200,
            "accuracy": 40,
        },
        # Some deployments put tower ids at top level — support reading path used by engine
        "mcc": 734,
        "mnc": 1,
        "lac": 100,
        "cid": 200,
    }

    # Mock OpenCellID lookup so we don't hit the network
    with patch.object(fe, "lookup_celltower_location", return_value={"lat": 10.53, "lon": -66.93}):
        result = fe.process_reading(payload)

    cell = _store[result["cell_id"]]
    score = float(cell["celltower_score"])
    print(f"  celltower_score={score} fused={result['fused_probability']}")
    assert score >= 0.9  # accuracy 40 → 0.9
    assert float(cell.get("starlink_score", 0)) == 0
    _assert_common(result, cell, "celltower")
    print("  PASS")


def test_multi_modality_same_cell():
    """Radar then thermal on same coords — fusion should rise with corroboration."""
    print("\n[MULTI-MODALITY SAME CELL]")
    _reset()
    lat, lon = 10.60, -66.80

    r1 = fe.process_reading({
        "sensor_type": "radar",
        "site_id": "site-multi",
        "lat": lat,
        "lon": lon,
        "reading": {
            "void_detected": True,
            "doppler_periodicity_hz": 0.25,
            "doppler_amplitude": 0.9,
            "depth_m": 1.5,
        },
    })
    fused_radar_only = r1["fused_probability"]

    r2 = fe.process_reading({
        "sensor_type": "thermal",
        "site_id": "site-multi",
        "lat": lat,
        "lon": lon,
        "reading": {
            "delta_t_celsius": 6.0,
            "hotspot_size_cm2": 500,
        },
    })
    fused_both = r2["fused_probability"]
    cell = _store[r2["cell_id"]]

    print(f"  fused radar-only={fused_radar_only} radar+thermal={fused_both}")
    assert r1["cell_id"] == r2["cell_id"]
    assert float(cell["radar_score"]) > 0
    assert float(cell["thermal_score"]) > 0
    assert fused_both >= fused_radar_only  # corroboration should not hurt
    assert float(cell.get("starlink_score", 0)) == 0
    print("  PASS")


def test_starlink_does_not_break_unknown_type():
    print("\n[UNKNOWN SENSOR TYPE]")
    _reset()
    try:
        fe.process_reading({
            "sensor_type": "magnetometer",
            "site_id": "x",
            "lat": 10.0,
            "lon": -66.0,
            "reading": {},
        })
        print("  FAIL: expected ValueError")
        raise AssertionError("expected ValueError for unknown sensor")
    except ValueError as e:
        print(f"  Correctly rejected: {e}")
        print("  PASS")


def main():
    print("=" * 60)
    print("REGRESSION — EXISTING SENSORS")
    print("=" * 60)

    test_radar()
    test_thermal()
    test_acoustic()
    test_celltower()
    test_multi_modality_same_cell()
    test_starlink_does_not_break_unknown_type()

    print("\n" + "=" * 60)
    print("REGRESSION — EXISTING SENSORS: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()