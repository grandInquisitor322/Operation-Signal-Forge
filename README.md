# Operational Signal Forge

Ground-sensor fusion system for search-and-rescue (USAR) operations. Combines
**ground-penetrating radar**, **thermal/IR**, and **acoustic** sensor feeds
into a single per-location "probability a person is present" score, displayed
on a live geospatial dashboard for search team coordination.

This mirrors the sensor-fusion approach used by FEMA US&R / INSARAG teams in
real collapse-structure search operations — multiple independent signal
types corroborating each other is what turns a noisy single reading into an
actionable lead.

## How it works

```
Field sensor units (GPR / thermal / acoustic)
        │  MQTT (signal-forge/sensors/{id}/reading)
        ▼
   AWS IoT Core  ──rule──▶  Kinesis Data Stream
                                  │
                                  ▼
                       Lambda: fusion_engine.py
                  (scores each signal, fuses into
                   one probability per geohash cell)
                                  │
                                  ▼
                          DynamoDB (signal-forge-detections)
                          │                        │
                          ▼                        ▼
              Lambda: dashboard_api.py      SNS (high-confidence alert)
                          │                        │
                          ▼                        ▼
              API Gateway (HTTP API)        Email/SMS to team lead
                          │
                          ▼
           dashboard/index.html (S3 + CloudFront)
           Leaflet map, heatmap, cell status tracking
```

### Why geohash grid cells, not raw sensor pings

Multiple sensor passes over the same spot need to accumulate into one
combined score. Geohashing each reading's lat/lon (precision 8, ~19m × 19m)
gives every reading from that physical location the same DynamoDB key, so
new sensor sweeps update an existing cell's confidence instead of creating
disconnected points.

### Scoring logic (`lambda/fusion_engine.py`)

- **Radar** — flags a sub-surface void plus checks for micro-Doppler motion
  in the breathing band (0.15–0.6 Hz) or cardiac band (0.8–2 Hz). This is the
  actual physical basis real through-rubble radar systems use to find live
  victims vs. empty voids.
- **Thermal** — looks for a body-temperature delta (3–8°C above ambient) at
  a plausible body-part-sized area.
- **Acoustic** — rhythmic tapping or detected voice patterns, discounted in
  low signal-to-noise conditions.
- **Fusion** — weighted average of the three, **plus a corroboration bonus**
  when 2 or 3 modalities agree on the same cell. This is the most important
  design choice: a single strong radar return is much weaker evidence than a
  weaker radar return that's corroborated by thermal and acoustic.

These weights and thresholds are starting heuristics. Tune them against your
field units' actual calibration data — a different radar model or thermal
camera will have a different "true positive" signature, and you should
validate against any known historical detections before trusting the
high-confidence threshold in the field.

## Deploying

```bash
cd infra
sam build
sam deploy --guided
# Follow the prompts; set AlertEmail to your team-lead's email
```

After deploy:
1. Note the `DashboardApiUrl` output.
2. Edit `dashboard/index.html`: set `API_BASE` to that URL and `USE_SAMPLE_DATA = false`.
3. Upload the dashboard:
   ```bash
   aws s3 sync dashboard/ s3://signal-forge-dashboard-<account-id>/
   ```
4. Open the `DashboardUrl` output in a browser.

## Testing without real field hardware

```bash
cd lambda
pip install boto3 --break-system-packages
python simulate_sensors.py --site caracas-site-7 --duration 180
```

This pushes synthetic readings (with a couple of deliberate "hotspots") into
the Kinesis stream so you can watch detections accumulate on the dashboard
in real time.

## Wiring up real field sensor units

Each physical sensor unit (radar, thermal camera, acoustic listening device)
needs to publish MQTT messages to:

```
signal-forge/sensors/{sensor_id}/reading
```

with a JSON body matching the `reading` shape expected by `fusion_engine.py`
for that sensor type (see the docstrings in that file). If your hardware
vendor's units output a different format, write a thin adapter (a small
Lambda or edge script) that translates vendor output into this shape before
publishing to IoT Core — keep the fusion engine's input contract stable.

## Operational notes

- **This is a triage tool, not a replacement for trained search teams or
  canine units.** It should narrow where teams search first, not be the
  sole basis for declaring an area clear. Always follow your organization's
  USAR protocols (e.g. INSARAG guidelines) for confirming or ruling out a
  detection.
- The `status` field on each cell (`unassigned` → `searching` → `cleared`/
  `confirmed`) is meant to be updated by the team on the ground via the
  dashboard, so command staff have a live view of search progress, not just
  raw sensor confidence.
- Consider adding a structural engineer sign-off step before sending teams
  into a flagged cell — debris fields can be unstable, and the detection
  signal alone says nothing about secondary collapse risk.