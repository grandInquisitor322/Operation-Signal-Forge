"""
Operational Signal Forge - DynamoDB Seed Script
==================================================
Inserts a handful of realistic-looking test detection cells directly into
the DetectionsTable, bypassing Kinesis entirely. Useful for testing the
dashboard and API while the real sensor ingestion pipeline is blocked
(e.g. waiting on the Kinesis account activation issue).

This data is clearly fake test data, not real detections - the cell IDs
and site_id make that explicit, and this should never be run against a
table where real field data might already exist without checking first.

Usage:
    pip install boto3 --break-system-packages
    python seed_test_data.py --profile signal-forge
"""

import argparse
import time
from decimal import Decimal
import boto3

SITE_ID = "caracas-site-7"

# A handful of test cells with varying signal strength, spread around a
# sample site location. Designed to exercise different parts of the UI:
# one high-confidence cell ready to be marked confirmed, a couple of
# mid-confidence ones worth investigating, and a low one for contrast.
TEST_CELLS = [
    {
        "cell_id": "test-cell-001",
        "lat": 10.48065,
        "lon": -66.90362,
        "radar_score": 0.82,
        "thermal_score": 0.74,
        "acoustic_score": 0.68,
        "status": "unassigned",
    },
    {
        "cell_id": "test-cell-002",
        "lat": 10.48041,
        "lon": -66.90398,
        "radar_score": 0.55,
        "thermal_score": 0.61,
        "acoustic_score": 0.12,
        "status": "searching",
    },
    {
        "cell_id": "test-cell-003",
        "lat": 10.48088,
        "lon": -66.90341,
        "radar_score": 0.31,
        "thermal_score": 0.22,
        "acoustic_score": 0.40,
        "status": "unassigned",
    },
    {
        "cell_id": "test-cell-004",
        "lat": 10.48052,
        "lon": -66.90380,
        "radar_score": 0.15,
        "thermal_score": 0.18,
        "acoustic_score": 0.05,
        "status": "cleared",
    },
]


def fuse(radar, thermal, acoustic, weights=(0.4, 0.3, 0.3)):
    w_r, w_t, w_a = weights
    base = radar * w_r + thermal * w_t + acoustic * w_a
    active = sum(1 for s in (radar, thermal, acoustic) if s > 0.3)
    bonus = {1: 0.0, 2: 0.10, 3: 0.20}.get(active, 0.0)
    return round(min(base + bonus, 1.0), 3)


def main(profile, table_name):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    dynamodb = session.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(table_name)

    now = int(time.time())
    for cell in TEST_CELLS:
        fused = fuse(cell["radar_score"], cell["thermal_score"], cell["acoustic_score"])
        item = {
            "cell_id": cell["cell_id"],
            "site_id": cell.get("site_id", SITE_ID),
            "lat": Decimal(str(cell["lat"])),
            "lon": Decimal(str(cell["lon"])),
            "radar_score": Decimal(str(cell["radar_score"])),
            "thermal_score": Decimal(str(cell["thermal_score"])),
            "acoustic_score": Decimal(str(cell["acoustic_score"])),
            "fused_probability": Decimal(str(fused)),
            "status": cell["status"],
            "created_at": now,
            "updated_at": now,
        }
        table.put_item(Item=item)
        print(f"  inserted {cell['cell_id']}  fused={fused}  status={cell['status']}")

    print(f"\nDone. {len(TEST_CELLS)} test cells written to '{table_name}' "
          f"for site_id='{SITE_ID}'.")
    print("Refresh the dashboard to see them. Remember these are TEST cells "
          "- delete them before any real deployment.")


def delete_test_cells(profile, table_name):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    dynamodb = session.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(table_name)
    for cell in TEST_CELLS:
        table.delete_item(Key={"cell_id": cell["cell_id"]})
        print(f"  deleted {cell['cell_id']}")
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=None, help="AWS CLI profile to use")
    parser.add_argument("--table", default="signal-forge-detections")
    parser.add_argument("--delete", action="store_true",
                         help="Remove the test cells instead of inserting them")
    args = parser.parse_args()

    if args.delete:
        delete_test_cells(args.profile, args.table)
    else:
        main(args.profile, args.table)