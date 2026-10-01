# Security Assumptions — Operation Signal Forge

**Version:** 0.2 (Architecture Baseline)  
**Status:** Active  
**Scope:** Production architecture and supporting tooling (AWS runtime, sensor ingest, Fusion Engine, dashboard, external data sources, Daytona test backend)

This document records **what the system assumes is true** about trust, identity, networks, data, and operators. Controls and residual risks should be evaluated against these assumptions. When an assumption no longer holds, the design or deployment must change.

---

## 1. Purpose and posture

Operation Signal Forge is a **search-and-rescue triage aid**. It aggregates sensor-derived signals into per-cell confidence scores for operational coordination.

**Security posture assumptions:**

1. The system prioritizes **availability and integrity of detection records** during an incident over perfect confidentiality of non-PII sensor aggregates — except where phone numbers, subscriber data, or precise personal location are involved.
2. The system is **not** assumed to be internet-facing beyond deliberately exposed endpoints (API Gateway, CloudFront dashboard, IoT endpoints).
3. Field devices and operator clients are assumed to operate in **hostile or degraded physical environments** (disaster sites), but **logical** access to AWS accounts and API keys is assumed to be controlled.

---

## 2. Trust boundaries

| Zone | Trust level | Examples |
|------|-------------|----------|
| AWS account / VPC-equivalent services | High (operator-controlled) | Lambda, DynamoDB, SQS/Kinesis path, SNS, IAM |
| Field sensor units | Low–medium | GPR, thermal, acoustic devices publishing MQTT |
| External data providers | Low–medium | OpenCellID (or equivalent cell DB) |
| Starlink observation sources | Low–medium | Terminal / pass / RF-derived observations fed as events |
| Operator dashboard clients | Medium | Browser sessions to CloudFront / API |
| Daytona sandboxes | Low (ephemeral test only) | Module validation; **not** production data plane |
| Public internet | Untrusted | All inbound not authenticated at edge |

**Assumption:** Code inside the Fusion Engine and sensor modules is trusted once deployed from the controlled CI/repo path. Inputs from field units and external APIs are **untrusted** until validated.

---

## 3. Identity and access

1. **AWS IAM** is the primary authorization system for runtime services. Least-privilege roles are assumed for each Lambda (Fusion, dashboard API, gateway, DLQ replay, etc.).
2. **API keys and secrets** (Daytona, OpenCellID, optional third parties) are assumed to be stored in environment variables or a secrets manager — **never** committed to git.
3. **Dashboard / API access** is assumed to be restricted to authorized SAR operators (via API Gateway auth, IAM, or equivalent). Public anonymous write access to detections is **not** assumed.
4. **MQTT / IoT device identity** is assumed: only provisioned devices (or a trusted field gateway) can publish to `signal-forge/sensors/...` topics.
5. **Human operators** are assumed to follow USAR/command procedures; the system does not assume it can prevent misuse of high-confidence alerts by authorized users.

---

## 4. Data classification (assumed)

| Data class | Examples | Sensitivity |
|------------|----------|-------------|
| Operational sensor aggregates | Cell scores, fused probability, status | Moderate (operational) |
| Geolocation grids | lat/lon, cell_id, site_id | Moderate–high in active incidents |
| External enrichment | OpenCellID lookups, Starlink metadata | Moderate |
| Subscriber / SMS identities | Phone numbers, opt-in records | **High (PII)** |
| Credentials | API keys, AWS keys, IoT certs | **Critical** |

**Assumption:** Detection-table contents may include precise enough location data to be sensitive in an active search. Subscriber data is handled under a stricter privacy regime than sensor scores alone.

---

## 5. Network and transport

1. **AWS service-to-service** traffic is assumed protected by AWS platform controls (TLS to managed APIs).
2. **Field → cloud** ingest is assumed to use TLS (IoT Core / HTTPS gateway). Plaintext sensor publish over the public internet is **not** assumed safe.
3. **Outbound calls** from Lambda (e.g. OpenCellID) are assumed to use HTTPS; response data is treated as untrusted input.
4. **Daytona** is assumed used only for **isolated test execution** of sensor modules, not for production fusion or storage of live incident PII.
5. **Network allowlists** (e.g. Daytona domain allow lists) are assumed for non-production sandboxes when external calls are required.

---

## 6. Input validation and module boundaries

1. **Sensor modules** (e.g. `lambda_sensors_starlink.process`) are assumed to validate their own payloads and reject invalid input with explicit errors.
2. **Fusion Engine** is assumed to orchestrate only: it must not embed vendor-specific parsing for Starlink (and should trend the same way for other modalities).
3. **Malformed SQS/Kinesis records** are assumed skippable without crashing the worker; transient AWS errors are assumed retryable; poison messages are assumed to reach a DLQ.
4. **Scores** written to DynamoDB are assumed to be numeric in a bounded range (e.g. 0–1) after module/engine processing.

---

## 7. Integrity and availability

1. **DynamoDB** is assumed the system of record for cell detections; lost messages without DLQ recovery may drop detections.
2. **Idempotency** is not fully assumed: repeated sensor events for the same cell **update** scores (last-write / merge semantics) rather than creating strict once-only delivery guarantees unless explicitly designed.
3. **High-confidence SNS alerts** are assumed to be operationally actionable; false positives are a safety/process risk, not only a security risk.
4. **Dashboard status fields** (`unassigned` → `searching` → …) are assumed to be updated by authorized operators; sensor ingest alone does not clear a cell.

---

## 8. External systems

### 8.1 OpenCellID (or equivalent)

- Assumed available over HTTPS with an API key.
- Assumed to return approximate infrastructure locations, not guaranteed real-time UE positions.
- Assumed subject to **provider terms, rate limits, and data-quality limits**; Signal Forge must not treat results as ground truth.

### 8.2 Starlink-related observations

- Assumed to arrive as **application events** (not as privileged satellite control).
- Module assumes observer-provided or derived lat/lon until orbital geolocation is implemented.
- Assumed **not** to require storing Starlink account credentials in Fusion.

### 8.3 Daytona

- Assumed **non-production**.
- Assumed API key is per-operator/org and rotated if exposed.
- Assumed sandboxes are ephemeral and must not hold long-lived production secrets.

---

## 9. Cryptography and secrets

1. TLS is assumed for all external HTTP/MQTT control-plane links.
2. Secret material is assumed rotated when staff leave or when leakage is suspected.
3. No assumption that client-side dashboard code can protect secrets; secrets stay server-side.

---

## 10. Logging and monitoring

1. Logs may include **cell_id, site_id, sensor_type, scores**; they should **minimize** raw PII (phone numbers, full subscriber payloads).
2. Assumed that CloudWatch (or equivalent) is available for Lambda failures and DLQ depth.
3. Assumed that debug logging of full payloads is disabled or redacted in production when payloads may contain sensitive fields.

---

## 11. Privacy-related assumptions (security-adjacent)

1. Lawful basis / operational authority for SAR use is assumed to be established by the deploying organization.
2. SMS/subscription flows (where enabled) are assumed to enforce **opt-in, opt-out, and regional rules** separately from sensor fusion.
3. Export of detection maps may reveal operational footprint; distribution is assumed limited to authorized command staff.

*(Detailed privacy policy should live in `docs/compliance/privacy-and-data-handling.md`.)*

---

## 12. Explicit non-assumptions (out of scope unless added)

The baseline does **not** assume:

1. Formal penetration test or continuous red-team coverage
2. Customer-managed encryption keys (CMK) on every store
3. Offline operation with no AWS dependency
4. Adversary-resistant field devices (tamper-proof hardware)
5. That fused probability alone is sufficient for life-safety decisions without human confirmation

---

## 13. Residual risks (accepted at v0.2)

| Risk | Why accepted (for now) | Direction |
|------|------------------------|-----------|
| Spoofed sensor events if device auth weak | Operational velocity | Strengthen IoT policies / gateway auth |
| External API poisoning (cell DB) | Enrichment only; multi-sensor fusion mitigates | Sanity bounds + multi-modality |
| Over-alerting via SNS | Operational tuning | Thresholds + human process |
| Secrets in env vars | Common AWS pattern | Prefer Secrets Manager |
| Docs incomplete vs. production reality | Baseline maturity | Close compliance doc gaps |

---

## 14. Review triggers

Revisit this document when any of the following occur:

- New sensor modality or external API
- Public internet exposure changes
- PII categories expand
- Multi-tenant or third-party org access
- Movement of Daytona (or similar) into a production path
- Incident or near-miss involving false data or unauthorized access

---

## 15. Related documents

- `docs/engineering/sensor-module-development-guide.md`
- `docs/engineering/execution-backend-guide.md`
- `docs/architecture/adr/` (OpenCellID, Starlink, execution backends)
- `README.md` (deploy and operational notes)
- Project `LICENSE`