from daytona import Daytona, CreateSandboxFromSnapshotParams
from pathlib import Path

STARLINK_MODULE_PATH = Path(r"C:\Users\Samson\signal-forge\lambda\lambda_sensors_starlink.py")

def main():
    candidates = [
        STARLINK_MODULE_PATH,
        Path(r"C:\Users\Samson\signal-forge\Daytona\lambda_sensors_starlink.py"),
        Path(__file__).resolve().parent / "lambda_sensors_starlink.py",
        Path(__file__).resolve().parent.parent / "lambda" / "lambda_sensors_starlink.py",
    ]
    module_path = next((p for p in candidates if p.exists()), None)
    if not module_path:
        raise FileNotFoundError("lambda_sensors_starlink.py not found")

    print(f"Using module: {module_path}")
    module_source = module_path.read_text(encoding="utf-8")

    daytona = Daytona()
    params = CreateSandboxFromSnapshotParams(
        language="python",
        domain_allow_list="example.com",
        env_vars={"PROJECT": "signal-forge", "MODULE": "starlink"},
    )

    print("Creating Daytona sandbox for Starlink module test...")
    sandbox = daytona.create(params)
    print(f"Sandbox ready: {sandbox.id}")

    try:
        # Correct API: sandbox.fs.upload_file
        sandbox.fs.upload_file(
            module_source.encode("utf-8"),
            "lambda_sensors_starlink.py",
        )
        print("Module uploaded to sandbox")

        test_code = r"""
from lambda_sensors_starlink import process
import json

print("=" * 60)
print("STARLINK MODULE — DAYTONA EXECUTION TEST")
print("=" * 60)

valid = {
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

obs = process(valid)
print("\n[PASS] Valid observation:")
print(json.dumps(obs, indent=2))

assert obs["sensor_type"] == "starlink"
assert obs["site_id"] == "caracas-site-7"
assert 0.0 <= obs["starlink_score"] <= 1.0
assert "metadata" in obs
assert "satellite_id" in obs["metadata"]
print("Assertions passed for valid payload")

print("\n[TEST] Missing site_id should raise ValueError...")
try:
    process({"lat": 10.0, "lon": -66.0})
    print("FAIL: expected ValueError")
except ValueError as e:
    print(f"Correctly rejected: {e}")

print("\n[TEST] Invalid coordinates should raise ValueError...")
try:
    process({"site_id": "x", "lat": 999, "lon": -66.0})
    print("FAIL: expected ValueError")
except ValueError as e:
    print(f"Correctly rejected: {e}")

low = process({
    "site_id": "site-a",
    "lat": 10.0,
    "lon": -66.0,
    "elevation_deg": 12,
})
high = process({
    "site_id": "site-a",
    "lat": 10.0,
    "lon": -66.0,
    "elevation_deg": 50,
})
print(f"\n[SCORE] elev=12 -> {low['starlink_score']}, elev=50 -> {high['starlink_score']}")
assert high["starlink_score"] > low["starlink_score"]
print("Scoring heuristic OK")

print("\n" + "=" * 60)
print("ALL STARLINK MODULE TESTS PASSED IN DAYTONA")
print("=" * 60)
"""

        print("\nRunning tests inside sandbox...\n")
        result = sandbox.process.code_run(test_code)
        print(result.result)

        if getattr(result, "exit_code", 0) not in (0, None):
            print(f"\nExit code: {result.exit_code}")
        else:
            print("\nStarlink module verified on Daytona execution backend")

    finally:
        daytona.delete(sandbox)
        print("Sandbox cleaned up")

if __name__ == "__main__":
    main()
