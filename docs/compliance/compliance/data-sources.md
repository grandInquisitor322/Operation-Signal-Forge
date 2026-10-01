# Data Sources Register — Operation Signal Forge

**Version:** 0.2 (Architecture Baseline)  
**Status:** Active  
**Related:** `docs/compliance/privacy-and-data-handling.md`, `docs/architecture/security-assumptions.md`, ADRs under `docs/architecture/adr/`

This register lists **where operational data comes from**, **what is taken from each source**, **how it is used**, and **trust/quality limits**. It is a compliance and engineering inventory — not a guarantee of data accuracy.

---

## 1. Summary

| Source ID | Name | Type | Used by | Produces |
|-----------|------|------|---------|----------|
| SRC-FIELD-RADAR | Field GPR / through-rubble radar | Device telemetry | Fusion Engine scorers | `radar_score`, cell location |
| SRC-FIELD-THERMAL | Field thermal / IR | Device telemetry | Fusion Engine scorers | `thermal_score`, cell location |
| SRC-FIELD-ACOUSTIC | Field acoustic / listening | Device telemetry | Fusion Engine scorers | `acoustic_score`, cell location |
| SRC-OPENCELLID | OpenCellID (or configured cell DB) | External API | `celltower` module / Fusion path | Location + accuracy → `celltower_score` |
| SRC-STARLINK | Starlink-related observations | Application events | `lambda_sensors_starlink.process` | Standardized observation → `starlink_score` |
| SRC-OPERATOR | Operator dashboard actions | Human / UI | Dashboard API | Cell `status` workflow |
| SRC-SYSTEM | AWS platform & simulation tools | Infrastructure / test | Runtime, `simulate_sensors.py` | Logs, synthetic test events |

---

## 2. Field sensor sources

### 2.1 SRC-FIELD-RADAR

| Attribute | Detail |
|-----------|--------|
| **Description** | Ground-penetrating / through-rubble radar units reporting void and micro-Doppler features |
| **Transport** | MQTT (or gateway) → cloud ingest → queue/stream → Fusion Engine |
| **Topic pattern (baseline)** | `signal-forge/sensors/{sensor_id}/reading` |
| **Key payload fields** | `sensor_type: radar`, `lat`, `lon`, `site_id`, `reading` (e.g. `void_detected`, `doppler_periodicity_hz`, `doppler_amplitude`, `depth_m`) |
| **Owner of validation** | Fusion Engine radar scorer (until extracted to a dedicated module) |
| **Persisted outputs** | `radar_score`, cell geo, timestamps |
| **Trust level** | Untrusted input until validated; device identity assumed provisioned |
| **Quality limits** | Hardware- and environment-dependent; heuristics are starting points only |
| **PII** | No direct PII; location may be operationally sensitive |

### 2.2 SRC-FIELD-THERMAL

| Attribute | Detail |
|-----------|--------|
| **Description** | Thermal / IR sensors reporting temperature contrast and hotspot size |
| **Transport** | Same ingest path as other field sensors |
| **Key payload fields** | `sensor_type: thermal`, `lat`, `lon`, `site_id`, `reading` (e.g. `delta_t_celsius`, `hotspot_size_cm2`) |
| **Persisted outputs** | `thermal_score`, cell geo, timestamps |
| **Trust / quality** | Untrusted until validated; ambient conditions affect false positives |
| **PII** | No direct PII; location sensitive in-incident |

### 2.3 SRC-FIELD-ACOUSTIC

| Attribute | Detail |
|-----------|--------|
| **Description** | Acoustic sensors reporting tap patterns, voice likelihood, SNR |
| **Transport** | Same ingest path as other field sensors |
| **Key payload fields** | `sensor_type: acoustic`, `lat`, `lon`, `site_id`, `reading` (e.g. `tap_pattern_detected`, `voice_likelihood`, `snr_db`) |
| **Persisted outputs** | `acoustic_score`, cell geo, timestamps |
| **Trust / quality** | Noise and SNR heavily influence score; not a standalone identity claim |
| **PII** | Raw audio is **out of baseline** if ever captured — do not store continuous audio unless separately approved |

---

## 3. External enrichment sources

### 3.1 SRC-OPENCELLID

| Attribute | Detail |
|-----------|--------|
| **Description** | External cell-identifier → approximate coordinates lookup (OpenCellID or configured equivalent) |
| **ADR** | `docs/architecture/adr/` — OpenCellID Sensor Integration |
| **Transport** | HTTPS outbound from Lambda / celltower path |
| **Typical inputs** | `mcc`, `mnc`, `lac`, `cid` (and related reading fields) |
| **Typical outputs** | `lat`, `lon`, `accuracy` (or equivalent) → `celltower_score` |
| **Used for** | Coarse infrastructure-associated location enrichment — **not** guaranteed real-time handset GNSS |
| **Trust level** | Third-party; subject to rate limits, coverage gaps, stale records |
| **License / terms** | Provider terms apply; record in `third-party-apis-and-licenses.md` |
| **Failure mode** | Lookup failure should not crash Fusion; skip or degrade score per module design |
| **PII** | Cell IDs can be sensitive in combination with time/location; minimize logging |

### 3.2 SRC-STARLINK

| Attribute | Detail |
|-----------|--------|
| **Description** | Starlink-related observations supplied as application events (terminal / pass / RF-associated context) |
| **ADR** | Starlink Sensor Module ADR |
| **Module** | `lambda/lambda_sensors_starlink.py` → `process()` |
| **Transport** | Same operational ingest (e.g. SQS record with `sensor_type: starlink`) |
| **Required inputs (module)** | `site_id`; `lat`/`lon` **or** future pass context; optional elevation, quality, satellite_id, etc. |
| **Module outputs (standardized)** | `sensor_type`, `site_id`, `lat`, `lon`, `starlink_score`, `metadata`, `created_at` |
| **Fusion use** | Orchestration only — stores `starlink_score`, participates in generic fusion weights |
| **Trust level** | Untrusted event source until `process()` validation |
| **Quality limits** | Score is heuristic; orbital geolocation from pass geometry may be incomplete |
| **PII** | No Starlink account credentials in baseline; coordinates may be sensitive |
| **Non-goals** | Not satellite command/control; not a Starlink service account integration in v0.2 |

---

## 4. Human and system sources

### 4.1 SRC-OPERATOR

| Attribute | Detail |
|-----------|--------|
| **Description** | Authorized operators updating cell workflow via dashboard / API |
| **Data** | `status` transitions (`unassigned` → `searching` → `cleared` / `confirmed`) |
| **Trust level** | Medium — authenticated operators assumed |
| **PII** | Operator identity may appear in auth logs; avoid storing personal notes with PII in cell records without policy |

### 4.2 SRC-SYSTEM

| Attribute | Detail |
|-----------|--------|
| **Description** | Platform-generated data and non-production simulators |
| **Examples** | CloudWatch logs, DLQ messages, `simulate_sensors.py` synthetic hotspots |
| **Production rule** | Synthetic generators must not write realistic personal contact data |
| **Daytona** | Test execution backend only; not a production data source |

---

## 5. Derived data (not a third-party source)

| Derived artifact | Produced by | From sources |
|------------------|-------------|--------------|
| `cell_id` | Fusion Engine | lat/lon grid |
| `fused_probability` | `fuse_scores()` | modality scores |
| SNS alert content | Fusion Engine | cell + scores + site |
| Dashboard heatmap | Dashboard API + UI | detections table |

Derived data inherits the **sensitivity of its inputs** (especially precise location during live incidents).

---

## 6. Data flow (logical)

```text
Field sensors / Starlink events / Celltower events
        │
        ▼
   Ingest (IoT / gateway / queue)
        │
        ▼
   Fusion Engine
        ├─ starlink → lambda_sensors_starlink.process()
        ├─ celltower → lookup + score
        └─ radar/thermal/acoustic → in-engine scorers
        │
        ▼
   DynamoDB detections  ──►  Dashboard API  ──►  Operators
        │
        └─ high confidence ──► SNS / notify channels
```