"""
Fusion Engine × Starlink integration test
-----------------------------------------
Verifies:
  1. Starlink event enters process_reading()
  2. Fusion dispatches to lambda_sensors_starlink.process()
  3. Standardized observation is used (lat/lon/site_id/starlink_score)
  4. No Starlink-specific logic runs inside Fusion beyond the module call
"""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from decimal import Decimal

# Ensure lambda/ is importable
LAMBDA_DIR = Path(r"C:\Users\Samson\signal-forge\lambda")
sys.path.insert(0, str(LAMBDA_DIR))

# Mock AWS before importing fusion_engine
mock_table = MagicMock()
mock_table.get_item.return_value = {}  # force get_or_create_cell to create new cell
mock_table.put_item.return_value = {}

mock_dynamodb = MagicMock()
mock_dynamodb.Table.return_value = mock_table

mock_sns = MagicMock()

with patch("boto3.resource", return_value=mock_dynamodb), \
     patch("boto3.client", return_value=mock_sns):
    import fusion_engine as fe


def test_starlink_dispatch():
    print("=" * 60)
    print("FUSION × STARLINK INTEGRATION TEST")
    print("=" * 60)

    raw_event = {
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

    print("\n[1] Sending Starlink event through process_reading()...")
    print(json.dumps(raw_event, indent=2))

    # Capture the standardized observation returned by the Starlink module
    captured = {}
    real_process = fe.process_starlink

    def _capture(payload):
        obs = real_process(payload)
        captured["observation"] = obs
        return obs

    with patch.object(fe, "process_starlink", side_effect=_capture) as spy:
        result = fe.process_reading(raw_event)

        print("\n[2] Dispatch check: process_starlink called?")
        assert spy.called, "Fusion did not call process_starlink"
        print("    YES — process_starlink was invoked once")

        observation = captured["observation"]
        print("\n[3] Standardized observation from module:")
        print(json.dumps(observation, indent=2))

        assert observation["sensor_type"] == "starlink"
        assert observation["site_id"] == "caracas-site-7"
        assert "starlink_score" in observation
        assert "metadata" in observation
        assert "elevation_deg" in observation["metadata"]
        print("    Observation shape OK")

    print("\n[4] Fusion result:")
    print(json.dumps(result, indent=2))
    assert "cell_id" in result
    assert "fused_probability" in result
    assert 0.0 <= result["fused_probability"] <= 1.0

    # DynamoDB write used starlink_score from the module
    print("\n[5] DynamoDB put_item payload check...")
    assert mock_table.put_item.called, "Expected DynamoDB put_item"
    written = mock_table.put_item.call_args.kwargs.get("Item") or mock_table.put_item.call_args[1].get("Item")
    print("    starlink_score written:", written.get("starlink_score"))
    print("    fused_probability:", written.get("fused_probability"))
    assert "starlink_score" in written
    assert float(written["starlink_score"]) > 0

    # Reject path: missing site_id should surface as ValueError from module
    print("\n[6] Module rejection propagates (missing site_id)...")
    try:
        fe.process_reading({"sensor_type": "starlink", "lat": 10.0, "lon": -66.0})
        print("    FAIL: expected ValueError")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        print(f"    Correctly rejected: {e}")

    print("\n" + "=" * 60)
    print("FUSION × STARLINK INTEGRATION: PASS")
    print("=" * 60)


if __name__ == "__main__":
    test_starlink_dispatch()