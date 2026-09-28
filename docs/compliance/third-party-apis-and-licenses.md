# Third-Party APIs and Licenses — Operation Signal Forge

**Version:** 0.3 
**Status:** Active  
**Related:** `docs/compliance/data-sources.md`, `docs/compliance/privacy-and-data-handling.md`, `docs/architecture/security-assumptions.md`

This register records **external services and components** Signal Forge depends on, **how they are used**, and **license / terms obligations**. Deployers must confirm current provider terms before production use — URLs and terms change over time.

---

## 1. Project license (first party)

| Item | Detail |
|------|--------|
| **Component** | Operation Signal Forge source code (this repository) |
| **License** | Apache License 2.0 (see root `LICENSE`) |
| **Obligations (summary)** | Retain license/copyright notices; state modifications; patent grant terms apply; no warranty |
| **Does not cover** | Third-party APIs, cloud provider agreements, or data returned by external services |

---

## 2. Cloud and runtime platform

### 2.1 Amazon Web Services (AWS)

| Attribute | Detail |
|-----------|--------|
| **Services used (baseline)** | Lambda, DynamoDB, API Gateway, SQS and/or Kinesis (ingest path), SNS, S3, CloudFront, IoT Core (field ingest), IAM, CloudWatch |
| **Use** | Production compute, storage, messaging, authz, logging, static dashboard hosting |
| **Agreement** | AWS Customer Agreement + applicable service terms (account-specific acceptance) |
| **DPA** | AWS Data Processing terms as applicable to the deployer’s account |
| **Data processing** | Under deployer’s AWS account; AWS acts as processor/infrastructure provider per AWS terms where applicable |
| **Credentials** | IAM roles/keys; never commit long-lived access keys to git |
| **Compliance notes** | Region selection, logging retention, and encryption settings are deployer-controlled |
| **License type** | Commercial cloud services (not open-source) |
| **Region / account** | **Per deploy** — record account ID + primary region in the runbook |

---

## 3. External data APIs

### 3.1 OpenCellID (Unwired Labs)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Map cell identifiers (`mcc`/`mnc`/`lac`/`cid`) to approximate coordinates and accuracy |
| **Source ID** | SRC-OPENCELLID (`docs/compliance/data-sources.md`) |
| **Integration** | `celltower` path / Fusion celltower handling |
| **Auth** | API key (env/secrets — not in git) |
| **Provider** | OpenCelliD (maintained by Unwired Labs) |
| **Project / data license** | Creative Commons Attribution-ShareAlike 4.0 International (**CC BY-SA 4.0**) for OpenCelliD project data |
| **Terms URL** | https://community.opencellid.org/tos |
| **Attribution / downloads** | https://www.opencellid.org/downloads.php |
| **Project site** | https://opencellid.org |
| **Commercial / API context** | Unwired Labs Location API: https://unwiredlabs.com/docs — confirm **your** plan’s API terms at signup |
| **API base URL** | Per Unwired Labs / OpenCelliD docs for your token (**record the exact URL you configure**) |
| **Attribution required?** | **Yes.** Visible credit to OpenCelliD with link to https://opencellid.org, per downloads page (CC BY-SA 4.0). Written exceptions only from Unwired Labs (`hello@opencellid.org`) |
| **Suggested attribution** | [OpenCelliD Project](https://opencellid.org) is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/) |
| **Rate limit / plan** | **Per account** — record free vs commercial tier after signup |
| **Key storage location** | **Per deploy** — AWS Secrets Manager or encrypted Lambda env (never git) |
| **Data ownership** | Lookup results subject to provider terms; Signal Forge does not claim ownership of the upstream cell database |
| **Operational rule** | Enrichment only — not ground-truth UE GNSS; multi-sensor fusion must not over-trust cell DB hits |
| **Failure handling** | Degrade/skip on timeout or error; do not block unrelated modalities |
| **Privacy** | Minimize logging of full request/response; cell IDs + time can be sensitive |

---

## 4. Optional messaging providers

### 4.1 Amazon SNS (baseline alerts)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | High-confidence detection notifications (email/SMS endpoints as configured) |
| **Agreement** | Covered under AWS terms + channel-specific rules |
| **SMS note** | If SMS is enabled, **telecom consent laws** apply in addition to AWS terms (see privacy policy) |
| **Data sent** | Cell id, site, coordinates, scores — minimize PII in message body |

### 4.2 Additional SMS gateways (if introduced)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Subscription or alert SMS outside SNS |
| **Requirement** | Add a full row to this register before production: vendor name, DPA, regions, consent tooling |
| **Baseline** | Not required if only SNS email is used |

---

## 5. Identity / ZKP stack (first-party)

| Attribute | Detail |
|-----------|--------|
| **Components** | `identity_runtime/` including `zk_abstraction/` (registry, C4 policy wrapper, protocol catalog, scheme verifiers, audit surfaces) |
| **Third-party proving / verifying libraries** | **None on the production path today** |
| **Scheme adapters in tree** | In-repository mocks only: `mock-bn254-sfg16a`, `mock-digest-v2` — architectural / fail-closed evidence only |
| **Not claimed** | Production zk-SNARK/STARK soundness, trusted setup, external verifier interoperability, or post-quantum security |
| **License impact** | First-party code under repository Apache-2.0; no extra third-party prover license until an external stack is adopted |
| **Rule before production crypto** | Before adding any production proving/verifying dependency, add a full register row (name, version, license, source URL, data handled) |
| **Compliance orientation** | `docs/compliance/zkp-compliance-carry-forward.md` |
| **Gate posture (pointer only)** | Gate 5 CLOSED; Gate 6 formal PASS (architecture); Gate 7 implementation candidate — formal adjudication OPEN; Level-3 pending |

---

## 6. Development and test platforms

### 6.1 Daytona

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Isolated sandbox execution for sensor-module tests (**non-production**) |
| **Provider** | Daytona Platforms Inc. |
| **Product** | Cloud sandboxes + Python SDK (`daytona` on PyPI) |
| **Auth** | `DAYTONA_API_KEY` |
| **Platform terms** | https://www.daytona.io/terms-of-service |
| **Privacy / DPA** | As offered on Daytona site for customers |
| **SLA** | https://www.daytona.io/sla |
| **Console / keys** | https://app.daytona.io — keys: https://app.daytona.io/dashboard/keys |
| **Docs** | https://www.daytona.io/docs/en/ |
| **SDK license (PyPI metadata)** | **Apache-2.0** |
| **Org / project id** | **Per deploy** |
| **Key storage** | **Per deploy** — local env / `.env` (gitignored) for dev; **not** used on the production Fusion path |
| **Data rule** | No production PII or live incident datasets in sandboxes unless explicitly approved |
| **Security** | Rotate keys if exposed; use domain allowlists when sandboxes need egress |

---

## 7. Client and UI dependencies

### 7.1 Dashboard front-end libraries

| Library | Version | License | Notes |
|---------|---------|---------|-------|
| Leaflet | **Pin from `dashboard/index.html` CDN URL** | **BSD-2-Clause** | https://github.com/Leaflet/Leaflet/blob/main/LICENSE — keep Leaflet credit in UI or docs |
| OpenStreetMap **data** | n/a | **ODbL** | https://www.openstreetmap.org/copyright — attribute “OpenStreetMap” with link |
| OSM.org **tiles** | n/a | OSMF Tile Usage Policy | https://operations.osmfoundation.org/policies/tiles/ — do not rely on unrestricted production use of `tile.openstreetmap.org`; prefer self-hosted or a commercial tile provider |

**Typical map attribution (adjust if tile provider changes):**

© [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors

---

## 8. Language and package dependencies (runtime)

| Package | Typical use | License |
|---------|-------------|---------|
| `boto3` / `botocore` | AWS API | **Apache-2.0** |
| `daytona` | Test sandboxes only | **Apache-2.0** (PyPI metadata) |
| Python stdlib | JSON, time, decimal | PSF License |

**Rule:** Production Lambdas should deploy with a **locked dependency set**. Attach an SBOM or pip freeze when hardening further.

---

## 9. Data returned by third parties — license vs. privacy

| Concern | Guidance |
|---------|----------|
| **Copyright / DB rights** | Upstream cell DB and map tiles remain under provider terms |
| **Privacy** | Location and identifiers handled under privacy-and-data-handling |
| **Export** | Do not republish bulk third-party datasets as Signal Forge open data unless terms allow |

---

## 10. Prohibited without new review

- Calling undocumented or scraped endpoints that violate provider ToS  
- Embedding third-party API keys in mobile/dashboard clients  
- Redistributing OpenCellID (or similar) bulk data contrary to license  
- Using Daytona or other test clouds as a production data plane  

---

## 11. Obligations checklist (deployer)

Before production:

- [ ] Apache-2.0 notices retained for Signal Forge distributions (root `LICENSE`)
- [ ] AWS account terms accepted; region + account ID recorded
- [ ] OpenCellID plan, attribution text, API base URL, and key storage documented
- [ ] SNS/SMS consent and content rules reviewed if SMS enabled
- [ ] Daytona limited to non-prod; keys rotated as needed
- [ ] Leaflet version pinned; map tile attribution correct for chosen provider
- [ ] Dependency versions recorded for the deployed build

---

## 12. Change log

| Date | Change |
|------|--------|
| 2026-07-29 | Initial register for v0.2 Architecture Baseline |
| 2026-07-29 | Filled OpenCellID, Daytona, Leaflet/OSM, boto3, AWS license fields |
| 2026-08-29 | Normalized to `docs/compliance/third-party-apis-and-licenses.md` |
| 2026-09-28 | Stage 3.x: identity/ZKP first-party mocks only; link zkp-compliance-carry-forward.md |

---

## 13. Related documents

- Root `LICENSE` (Apache-2.0)
- `docs/compliance/data-sources.md` (or `.docx` until converted)
- `docs/compliance/privacy-and-data-handling.md` (or `.docx` until converted)
- `docs/architecture/adr/` (OpenCellID, Starlink, execution backends)
- `docs/engineering/execution-backend-guide.md`
- `docs/compliance/README.md`
- `docs/compliance/zkp-compliance-carry-forward.md`