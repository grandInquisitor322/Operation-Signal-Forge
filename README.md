# Operation Signal Forge

Ground-sensor fusion and decision-support stack for search-and-rescue (USAR) style operations. Multiple sensor modalities feed a **deterministic Fusion Engine**; optional **capability** and **identity** layers sit beside it without owning fusion, persistence, or alerting.

The platform is evolving toward **PANGEA** — an Uber-DApp style surface over Operation Signal Forge: Core Capability Layer, Trust Layer, and Identity Layer (AgentForge, authorization isolation, and bounded ZKP design).

**Current baseline (repo):** Phase **3.x** architecture in progress (context authority through Stage 3.5 abstraction / Gate 5 remediation workstreams). Zero-knowledge **proof validity is not authorization**; the **Authorization Matrix** remains the decision authority for actions.

---

## Accountable autonomous intelligence

Signal Forge is built so automation can assist operations **without becoming an unaccountable black box**.

| Principle | How the infrastructure supports it |
|-----------|-------------------------------------|
| **Deterministic fusion** | The Fusion Engine scores and fuses sensor inputs with fixed, inspectable logic. It does not “decide” who may act. |
| **Advisory capabilities** | AgentForge / capability layer produces briefs, investigations, and sensor recommendations as **decision support** — not commands and not writes to fusion state. |
| **Authorization isolation** | Actions require an explicit **authorization context** (and, where ZK is used, a **positive verified eligibility claim**). Failed or missing verification never defaults to allow. |
| **Proof ≠ permission** | Cryptographic or credential checks can support eligibility claims; **only the Authorization Matrix** grants operational permission. |
| **Audit & verification** | Identity runtime records presentations, trust-registry changes, and verification evidence so humans can reconstruct *why* a path was allowed or denied. |
| **Human command remains in the loop** | Cell status (`unassigned` → `searching` → `cleared` / `confirmed`) is updated by operators; the system narrows triage, it does not replace USAR command. |

In short: sensors and models may propose; **infrastructure enforces separation of fusion, advice, proof, and permission** so autonomy stays accountable.

## What it does

| Layer | Responsibility |
|-------|----------------|
| **Sensors → Fusion** | Radar, thermal, acoustic, celltower, Starlink → standardized scores → fused probability per geohash cell |
| **Capability layer** | Advisory workflows (briefs, investigate, recommend sensor) via ports — not fusion or authz |
| **Identity / AuthZ** | DIDs, VCs, trust registry, scopes → authorization **context** into capabilities |
| **DApp prototype** | UX for login, investigations, briefs, trust registry (Phase 1 mock → AuthZ-backed API) |
| **ZKP (Phase 3.x)** | Use case + authority model only through **3.2**; no proof circuit or verifier runtime in-tree yet |

**Invariant:** ZKP proof validity ≠ authorization. The **Authorization Matrix** remains the decision authority for actions.

---

## Core fusion path
```
Field sensor units (GPR / thermal / acoustic)
        │  MQTT (signal-forge/sensors/{id}/reading)
        ▼
   AWS IoT Core  ──rule──▶ 
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


### Why geohash cells

Multiple passes over the same place must accumulate. Geohashing lat/lon (e.g. precision 8, ~19 m × 19 m) gives a stable DynamoDB key so new readings update confidence instead of scattering points.

### Fusion design notes

- **Radar / thermal / acoustic** — modality-specific scoring; corroboration bonus when multiple modalities agree.
- **Starlink** — dedicated module (`lambda_sensors_starlink.process()`); Fusion only orchestrates.
- **Celltower** — optional OpenCellID enrichment; not ground-truth GNSS.
- Weights are **heuristics** — validate against field calibration before operational high-confidence thresholds.

This is a **triage aid**, not a substitute for trained teams, canine units, or structural safety protocols.

---

## Major components (repo map)

| Path | Role |
|------|------|
| `lambda/` | Fusion engine, sensor modules, dashboard API |
| `capability_layer/` | Advisory capabilities + ports/adapters |
| `identity_runtime/` | DID/VC presentation, trust, recovery policy, verification levels |
| `dapp/` + `dapp_api/` | Humanitarian DApp prototype + AuthZ API |
| `docs/architecture/` | ADRs, ZKP packages, identity, checklists/specs |
| `docs/compliance/` | Compliance assessments + ZKP carry-forward / checklists |
| `docs/milestones/` | Phase closure records |
| `Daytona/` | Non-prod sandbox tests |
| `infra/` | SAM/deploy templates |

**License:** Apache-2.0 (root `LICENSE`). See `docs/compliance/third-party-apis-and-licenses.md`.

---

## Architecture status (Phase 3.x)

| Phase | Outcome |
|-------|---------|
| **3.0** | Cryptographic objective & privacy/success boundary (definition only) |
| **3.1** | Single proof use case + design principles (min disclosure, context-bound, proof ≠ authz) |
| **3.2** | Authority model packaged (incident / qualification / assignment / Matrix / ZKP verifier); **SATISFIED** |
| **3.3+** | Context representation → witness/public inputs → protocol → runtime (not done) |

Standing compliance orientation: `docs/compliance/zkp-compliance-carry-forward.md`.

---

## Deploying (fusion baseline)

```bash
cd infra
sam build
sam deploy --guided
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

Uber Dapp: Core Capability Layer, Trust Layer, Identity Layer. Features: AgentForge, ZKP.
