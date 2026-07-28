"""
Detection pipeline checks for Starlink → Fusion
------------------------------------------------
Verifies:
  1. New cell is created with expected fields and status
  2. starlink_score is populated from the module
  3. fused_probability is computed
  4. A second event updates the same cell (score + timestamps)
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

# First call: no existing cell. Later we simulate an existing cell.
_existing = {}

def _get_item(Key):
    cell_id = Key["cell_id"]
    if cell_id in _existing:
        return {"Item": dict(_existing[cell_id])}
    return {}

def _put_item(Item):
    _existing[Item["cell_id"]] = dict(Item)
    return {}

mock_table.get_item.side_effect = lambda **kw: _get_item(kw["Key"])
mock_table.put_item.side_effect = lambda **kw: _put_item(kw["Item"])

with patch("boto3.resource", return_value=mock_dynamodb), \
     patch("boto3.client", return_value=mock_sns):
    import fusion_engine as fe


def _starlink_event(**overrides):
    base = {
        "sensor_type": "starlink",
        "site_id": "caracas-site-7",
        "lat": 10.4806,
        "lon": -66.9036,
        "elevation_deg": 45,
        "azimuth_deg": 120,
        "satellite_id": "STARLINK-1234",
        "signal_quality": 0.85,
        "observation_source": "field_terminal",
        "constellation": "starlink",
    }
    base.update(overrides)
    return base


def test_detection_pipeline():
    print("=" * 60)
    print("DETECTION PIPELINE — STARLINK")
    print("=" * 60)

    _existing.clear()
    event = _starlink_event()

    # --- Create path ---
    print("\n[1] First event → create detection record")
    result1 = fe.process_reading(event)
    cell_id = result1["cell_id"]
    print(f"    cell_id: {cell_id}")
    print(f"    fused_probability: {result1['fused_probability']}")

    assert cell_id in _existing
    cell = _existing[cell_id]

    print("\n[2] Record fields after create:")
    print(json.dumps({k: str(v) for k, v in cell.items()}, indent=2))

    # Required identity / geo
    assert cell["cell_id"] == cell_id
    assert cell["site_id"] == "caracas-site-7"
    assert float(cell["lat"]) == 10.4806
    assert float(cell["lon"]) == -66.9036

    # Starlink score from module (not zero)
    starlink_score = float(cell["starlink_score"])
    print(f"\n[3] starlink_score: {starlink_score}")
    assert starlink_score > 0
    assert starlink_score <= 1.0

    # Fusion output
    fused = float(cell["fused_probability"])
    print(f"[4] fused_probability: {fused}")
    assert fused == result1["fused_probability"]
    assert 0.0 <= fused <= 1.0
    # Starlink-only: fuse uses starlink weight → should be > 0
    assert fused > 0

    # Status default
    print(f"[5] status: {cell['status']}")
    assert cell["status"] == "unassigned"

    # Timestamps present
    assert "created_at" in cell
    assert "updated_at" in cell
    assert "starlink_last_updated" in cell

    # Other modality scores start at 0
    assert float(cell.get("radar_score", 0)) == 0
    assert float(cell.get("thermal_score", 0)) == 0
    assert float(cell.get("acoustic_score", 0)) == 0

    # --- Update path (second event, higher elevation) ---
    print("\n[6] Second event → update same cell")
    event2 = _starlink_event(elevation_deg=55, signal_quality=0.95)
    result2 = fe.process_reading(event2)
    assert result2["cell_id"] == cell_id

    cell2 = _existing[cell_id]
    score2 = float(cell2["starlink_score"])
    fused2 = float(cell2["fused_probability"])
    print(f"    starlink_score: {score2} (was {starlink_score})")
    print(f"    fused_probability: {fused2} (was {fused})")

    assert score2 >= starlink_score  # higher elev/quality should not drop score
    assert cell2["status"] == "unassigned"  # status unchanged by sensor ingest
    assert int(cell2["starlink_last_updated"]) >= int(cell["starlink_last_updated"])
    assert int(cell2["updated_at"]) >= int(cell["updated_at"])
    # created_at preserved on update
    assert cell2["created_at"] == cell["created_at"]

    print("\n" + "=" * 60)
    print("DETECTION PIPELINE — STARLINK: PASS")
    print("=" * 60)


if __name__ == "__main__":
    test_detection_pipeline()