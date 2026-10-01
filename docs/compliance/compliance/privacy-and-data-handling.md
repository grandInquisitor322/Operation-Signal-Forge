# Privacy and Data-Handling Policy — Operation Signal Forge

**Version:** 0.2 (Architecture Baseline)  
**Status:** Active  
**Applies to:** Sensor fusion runtime, detection storage, dashboard, alerts, optional SMS/subscription features, and related AWS services

This policy describes **what data Signal Forge handles**, **why**, **how long**, **who may access it**, and **operator obligations**. It complements `docs/architecture/security-assumptions.md`. Deploying organizations remain responsible for local law and incident-command rules.

---

## 1. Purpose and role of the system

Operation Signal Forge supports **search-and-rescue (SAR) triage** by combining sensor-derived signals into per-location confidence scores for authorized teams.

**Privacy principle:** Collect and retain only data needed for operational coordination and system reliability. Prefer aggregates and grid cells over person-level profiles unless a feature (e.g. SMS subscription) explicitly requires identifiers.

**Important limitation:** Fused scores and map cells are **decision-support**, not a declaration of identity, guilt, or confirmed presence. Human SAR protocols govern action on the ground.

---

## 2. Roles

| Role | Responsibility |
|------|----------------|
| **Deploying organization** | Legal authority to operate; staff access control; retention; subject requests |
| **System operators / command staff** | Use detections and alerts only for SAR coordination |
| **Field device operators** | Ensure devices publish only authorized sensor streams |
| **Platform maintainers** | Minimize data in design; secure configs; document processors |
| **Data subject** | Individual whose phone number or personal data may appear in subscription features |

Signal Forge maintainers do not automatically become the controller for every deployment; **the organization that runs the AWS account and enrolls users does**.

---

## 3. Categories of data

### 3.1 Operational / sensor data (core fusion)

| Category | Examples | Personal data? |
|----------|----------|----------------|
| Sensor readings | Radar void/Doppler features, thermal deltas, acoustic patterns | Usually **no** (device telemetry) |
| Grid location | `lat`, `lon`, `cell_id`, `site_id` | **Possibly** — precise location in an active incident can be sensitive |
| Scores | `radar_score`, `thermal_score`, `acoustic_score`, `starlink_score`, `fused_probability` | No (derived operational metrics) |
| Cell workflow | `status` (`unassigned`, `searching`, `cleared`, `confirmed`) | No |
| Timestamps | `created_at`, `updated_at`, `*_last_updated` | No |

### 3.2 External enrichment

| Source | Data | Notes |
|--------|------|-------|
| OpenCellID (or equivalent) | Approximate cell-tower / infrastructure location, accuracy | Not a guaranteed real-time handset location; subject to provider terms |
| Starlink module inputs | Pass/elevation/metadata, observer-associated coordinates | Module keeps detailed metadata encapsulated; Fusion stores scores + location |

### 3.3 Subscriber / messaging data (if SMS or notify features are enabled)

| Category | Examples | Personal data? |
|----------|----------|----------------|
| Contact identifiers | Phone numbers, opt-in status | **Yes (PII)** |
| Consent records | Time of opt-in/opt-out, channel | **Yes** |
| Message logs | Alert delivery metadata | Often **yes** |

Treat subscriber data as a **separate, higher-sensitivity** domain from grid scores.

### 3.4 Technical / security data

- Cloud logs (Lambda, API Gateway), request IDs, error traces
- API keys and secrets (never stored in application data tables)
- IoT device certificates / identities

---

## 4. Purposes of processing

Data may be processed only for:

1. **SAR triage** — compute and display per-cell confidence and status
2. **Team coordination** — dashboard map, cell assignment workflow
3. **Alerting** — high-confidence notifications to designated channels
4. **System reliability** — retries, DLQ, debugging (with minimization)
5. **Consent-based messaging** — only where subscription features are enabled and consented
6. **Compliance and audit** — retention of consent and access records as required by law

**Not permitted purposes (baseline):** advertising, sale of data, profiling unrelated to SAR, sharing detections with unauthorized third parties.

---

## 5. Legal and policy basis (framework)

Deployments must establish a lawful basis appropriate to jurisdiction. Common frames:

| Context | Typical basis (illustrative) |
|---------|------------------------------|
| Emergency SAR operations | Vital interests / public interest / official authority (varies by country) |
| Staff accounts and logs | Legitimate interest or contract (employment/volunteer agreement) |
| SMS alerts to the public or families | **Consent** (opt-in) plus regional telecom rules |
| US state privacy (e.g. CCPA/CPRA) | Disclose categories, purpose, no sale; honor deletion/opt-out where applicable |
| GDPR-style regimes | Document controller, basis, retention, DSR process |

**Assumption:** The deploying organization confirms authority to process location-related operational data in the incident theater. This repo does not replace legal advice.

---

## 6. Data minimization rules

1. Prefer **grid cells** over continuous raw tracks when Fusion only needs cell-level confidence.
2. Sensor modules should put vendor-specific detail in **metadata** and avoid copying unnecessary fields into DynamoDB.
3. Production logs must **not** print full payloads that contain phone numbers or unrestricted PII.
4. Daytona and other **test backends** must use synthetic data unless a controlled, approved fixture is required.
5. Do not send Starlink or OpenCellID raw responses to SNS alert bodies unless operationally required.

---

## 7. Storage and location

| Store | Typical contents |
|-------|------------------|
| DynamoDB detections table | Cell scores, location, status, timestamps |
| SNS / email / SMS providers | Alert content to recipients |
| S3 / CloudFront | Static dashboard assets (not primary PII store) |
| CloudWatch Logs | Operational logs |
| Subscription data store (if any) | Phone numbers, consent |

**Assumption:** Primary processing occurs in the **AWS region** chosen at deploy time. Cross-region replication is out of baseline scope unless explicitly enabled and documented.

---

## 8. Retention

| Data class | Baseline retention guidance |
|------------|----------------------------|
| Active incident cell records | Duration of incident + short operational review window (org-defined) |
| Historical detections | Org-defined; prefer time-to-live (TTL) or archival if not needed |
| SNS delivery logs | Provider defaults unless longer retention required |
| Subscriber consent records | At least as long as required by applicable law after opt-out |
| Security logs | Org-defined (often 30–90 days minimum) |
| Secrets | Until rotation; not retained in app databases |

Organizations should set **numeric retention periods** in deployment runbooks; this policy requires that periods be **defined and enforced**, not left unbounded by default.

---

## 9. Access control

1. Only authorized operators may view live detections and update cell status.
2. AWS access uses IAM least privilege.
3. API endpoints that read/write detections assume authentication/authorization at the edge (API Gateway or equivalent).
4. Field devices publish only through provisioned IoT identities or a trusted gateway.
5. Sharing map screenshots or exports outside the command structure requires organizational approval.

---

## 10. Sharing and processors

Data may be processed by:

- **AWS** (compute, storage, messaging, logging) under the customer’s AWS agreement
- **OpenCellID / cell database provider** when lookups are performed
- **SMS/email providers** when alerts or subscriptions are enabled
- **Daytona** only for non-production module testing unless separately approved

No **sale** of personal or operational SAR data is authorized under this policy.

Third-party terms and licenses should be listed in `docs/compliance/third-party-apis-and-licenses.md`.

---

## 11. Security measures (privacy-supporting)

Aligned with security assumptions:

- TLS for external API and IoT control paths
- Secrets excluded from git; prefer secrets manager in production
- Validation at sensor-module and Fusion boundaries
- Separation of test (Daytona) from production data planes
- Minimized alert content

---

## 12. Individual rights (where personal data exists)

When PII is processed (especially subscriptions):

| Right / request type | Baseline expectation |
|----------------------|----------------------|
| Access | Provide data held about the requester where legally required |
| Deletion | Honor where required; retain only what law mandates (e.g. consent proof) |
| Opt-out of sale/share | Not applicable to sale (forbidden); honor marketing/SMS opt-out immediately |
| Correction | Correct inaccurate contact data |
| Withdraw consent | Stop non-essential messaging promptly |

**Operational SAR grids** may not map to a single data subject; requests must be assessed case by case (often no individual profile exists).

Point of contact for requests: **[Organization privacy contact — TBD by deployer]**.

---

## 13. SMS and telecommunications (if enabled)

1. **Prior express consent** before outbound SMS, except where law provides a narrower emergency exception (org legal review required).
2. Support **STOP / opt-out** and process it promptly.
3. Maintain consent timestamps and source.
4. Respect regional rules (examples of regimes teams often map to: TCPA-style consent expectations, CCPA/CPRA notices, GDPR-style consent, local telecom rules).
5. Do not use SAR contact lists for unrelated outreach.

---

## 14. Children

Baseline: Signal Forge is **not directed at children**. Subscription features must not knowingly collect contact data from children without verifiable parental authority where required by law.

---

## 15. Incident response (privacy)

On suspected unauthorized access, leakage of phone numbers, or bulk export of detection maps:

1. Contain (rotate keys, revoke sessions, isolate endpoints)
2. Assess scope (data categories, systems, time window)
3. Notify organization leadership and legal as required
4. Notify affected individuals / authorities when legally required
5. Record the incident and corrective actions

---

## 16. Operator obligations

Authorized users must:

- Use data only for SAR coordination and system operation
- Avoid posting live cell details on public social channels
- Report suspected misuse or leakage
- Follow local USAR / command privacy rules

---

## 17. Relationship to sensor modules

- Sensor modules may process vendor-specific fields in memory.
- **Persistent** store should favor standardized fields (`sensor_type`, scores, location, limited metadata).
- Starlink and OpenCellID details remain subject to this policy once stored or logged.

---

## 18. Document ownership and review

| Event | Action |
|-------|--------|
| New data category or vendor | Update this policy + data-sources register |
| New region or multi-tenant mode | Legal review + retention/access update |
| Annual review | Confirm retention and access still accurate |

**Owner:** [Deploying organization / project lead — TBD]  
**Last reviewed:** 2026-07-29

---

## 19. Related documents

- `docs/architecture/security-assumptions.md`
- `docs/engineering/sensor-module-development-guide.md`
- `docs/architecture/adr/` (OpenCellID, Starlink)
- `README.md`
- Forthcoming: `docs/compliance/data-sources.md`, `docs/compliance/third-party-apis-and-licenses.md`