# ZKP Compliance Carry-Forward

**Project:** Operation Signal Forge  
**Status:** Standing reference — **Stage 3.5 CLOSED / PASS** (Gates 5–7); residual deferred items below  
**Last aligned through:** Stage 3.5 formal closure (2026-10-01)  
**Formal closure record:** `docs/architecture/stage-3.5/gate-7-protocol-versioning/Stage_3_5_Formal_Closure_Adjudication.md`  
**Authoritative G7-CI implementation SHA:** `feedab71ab2ab0689b76e2492b25fc7283aa2283`  
**Parent Gate 7 candidate:** `adeef37508214fe1522f5941ac67539f1acd52a3`  
**Nature:** Technical compliance guardrails — **non-certifying** (no production cryptographic certification)

Use this sheet for Stage **3.6+**, D-3 work, production proving-stack adoption, or any change that touches proofs, protocol identity, context representation, or authorization inputs. Do **not** weaken these without a new ADR and an explicit compliance impact note.

---

## 1. Purpose of the proof (fixed)

**Use case (singular):**

> Prove that the presenter is an eligible emergency responder for a **specified active** disaster-response context, without revealing unnecessary credential or identity information.

- One end-to-end proof target — no silent second use case  
- Implementation-neutral at the objective layer; concrete protocol/runtime evolve under Stage 3.5+ controls  
- Privacy objective is part of the use case, not an optional add-on  

**Sources:** Phase 3.0 objective · Phase 3.1 use-case selection  

---

## 2. Non-negotiable boundaries

| Rule | Meaning for compliance |
|------|-------------------------|
| **Proof validity ≠ authorization** | A valid proof is an intermediate **claim/input**. The **Authorization Matrix** alone grants or denies actions. |
| **Active context from authority, not ZKP** | The ZKP layer does **not** declare a disaster active or resolve which authority is correct. |
| **Qualification ≠ incident activation** | Certification/role status is not the same as “this incident is on.” |
| **Assignment ≠ qualification** | Staffing a response does not silently assert every qualification attribute. |
| **Minimum necessary disclosure** | Do not imply the proof reveals attributes the eligibility decision does not need. |
| **Incident management outside ZKP** | No dispatch, C2, or incident lifecycle inside the proof system. |
| **Identity infra ≠ operational incident infra** | Keep identity/proof plumbing separate from ops incident systems. |
| **PROTO-2.1** | Protocol / policy governance metadata is **not** automatic public input solely because it appears on the identity tuple. |
| **Mock ≠ production crypto** | Scheme adapters in tree demonstrate architecture and fail-closed control flow only. |
| **Contract integrity (G7-CI)** | Published protocol contracts bind content to seal; runtime verifies integrity before trust. |

---

## 3. Authority model (roles, not org names)

| Role | May | Must not |
|------|-----|----------|
| **Authorized Incident Authority** | Activate / lifecycle the **context** | Act as ZKP verifier or Matrix |
| **Qualification Authority** | Establish responder qualification | Act as universal incident activator |
| **Operational Assignment Authority** | Assign qualified responders where used | Replace Matrix authorization |
| **Authorization Matrix** | Final allow/deny | Be bypassed by “proof verified” |
| **ZKP Verifier** | Verify proof → verified claim | Activate context, authorize, or adjudicate conflicts |

**Do not hard-code** FEMA, Red Cross, SAR, AHJ, or any body as a *universal* authority in code or schemas. Named orgs may appear later only as **deployment bindings** to these roles, via explicit config/policy—not as the model itself.

**Rejected (closed):** single universal authority; Red Cross as universal incident authority; SAR as universal incident authority; ZKP determines disaster status.

**Source:** Phase 3.2 ADR package  

---

## 4. Stage posture (carry-forward status)

| Topic | Posture | Notes |
|-------|---------|--------|
| Phase 3.0 — cryptographic objective / privacy / success boundary | **Closed (definition)** | Objective fixed |
| Phase 3.1 — use case + design principles | **Closed** | Singular use case |
| Phase 3.2 — authority & responder model | **SATISFIED** | Roles model in force |
| Stage 3.3 — context representation | **Closed (architecture)** | Context IDs / records / references |
| Stage 3.4 — witness / public-input / visibility boundary | **Closed (architecture)** | Verifier-visible allowlisting; outside-boundary fail-closed |
| Stage 3.5 — protocol / abstraction / gates | **CLOSED / PASS** | Gates 5–7 formal; see gate table |
| D-3 — Protocol Catalog semantic execution | **Deferred** | Explicit non-goal of G7-CI; not a Stage 3.5 exit criterion |
| Runtime proof path + Matrix integration evidence | **Not done** | Stage **3.6+** |
| Deployment precedence among conflicting authorities | **Not designed** | Required later |
| Trust/conflict *mechanisms* | **Requirements only** | Not a full mechanism design |
| Production proving / verifying libraries | **None on production path** | In-repo mocks only |

### Gate and stage status

| Gate / stage | Status | Compliance reading |
|--------------|--------|-------------------|
| **Gate 5** | **CLOSED / PASS** | Fail-closed acceptance, R1.1, taxonomy |
| **Gate 6** | **CLOSED / PASS** | `SchemeVerifier` agility; mocks only; not production crypto |
| **Gate 7** | **CLOSED / PASS** | Protocol versioning + G7-CI seal binding (`feedab71`) |
| **Stage 3.5** | **CLOSED / PASS** (conditions C-1–C-6 on formal record) | Abstraction + protocol identity closed |

### Stage 3.5 / Gate 7 references

| Field | Value |
|-------|--------|
| Formal Stage 3.5 closure | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Stage_3_5_Formal_Closure_Adjudication.md` |
| Gate 7 formal adjudication | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Gate_7_Formal_Adjudication.md` |
| Gate 7 Chain-of-Correction | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Gate_7_Chain_of_Correction_Note.md` |
| G7-CI implementation SHA | `feedab71ab2ab0689b76e2492b25fc7283aa2283` |
| Originally recorded candidate SHA | `5f7523bf3865dce519ccd87a82fe897f665bd123` *(not a repo object; historical only)* |
| Parent Gate 7 candidate | `adeef37508214fe1522f5941ac67539f1acd52a3` |
| G7-CI L2 / L3 | `f39c9d4e2d9055d2` · `276d3506496b78e2` |

**Scheme adapters in tree (architecture only):** `mock-bn254-sfg16a`, `mock-digest-v2`.

---

## 5. Verification (H1) guardrail

- Definition/packaging phases (3.0–3.2): Level **1–2** as justified — **not** automatic Level 3.  
- Gate 6 and Gate 7 formal PASS **do not** replace Level-3 discipline for *future* high-consequence changes.  
- Prefer itemized `verifier_run_results` and explicit `limitations` on binding records.  
- Do not delete verification JSONL rows; supersede in notes if classification changes.  
- Preserve Gate 7 SHA custody: historical `5f7523b…` and authoritative `feedab71…` are separate artifacts.  

---

## 6. Post-integration evidence checklist (Stage 3.6+)

When a proof is actually on a critical path, compliance updates should be able to point to evidence for:

- [ ] Public/verifier-visible outputs match the privacy intent (min necessary)  
- [ ] Matrix can **deny** after a **valid** proof  
- [ ] Context binding respects activation / expiry / revocation semantics  
- [ ] Proof and verification logs classified (retention, re-identification risk)  
- [ ] No capability executes on verify-alone without Matrix  
- [ ] Dependencies / licenses for proving stack recorded in third-party register  
- [ ] H1 level appropriate to crypto + authz-boundary risk  
- [ ] Protocol contract identity `(protocol_id, protocol_version)` integrity (G7-CI) holds under deployment topology  
- [ ] D-3 addressed or explicitly re-deferred with ADR if semantic execution is required  

---

## 7. Doc map

| Topic | Primary doc / surface |
|-------|------------------------|
| Cryptographic objective / privacy / success boundary | `docs/architecture/zkp/phase-3.0-cryptographic-objective-and-proof-use-case.md` |
| Use case + design principles | `docs/architecture/zkp/phase-3.1-proof-use-case-selection.md` |
| Authority & responder model | `docs/architecture/zkp/phase-3.2-disaster-context-authority-and-responder-model.md` |
| Gate 6 formal adjudication | `docs/architecture/stage-3.5/gate-6-cryptographic-agility/Gate_6_Formal_Adjudication.md` |
| Gate 7 formal adjudication | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Gate_7_Formal_Adjudication.md` |
| Stage 3.5 formal closure | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Stage_3_5_Formal_Closure_Adjudication.md` |
| Third-party / first-party ZKP register | `docs/compliance/third-party-apis-and-licenses.md` |
| G7-CI catalog / tests | `identity_runtime/zk_abstraction/protocol_catalog.py`, `identity_runtime/tests/test_gate7_contract_integrity.py` |
| This carry-forward | `docs/compliance/zkp-compliance-carry-forward.md` |

---

## 8. Explicit non-claims

This sheet does **not** assert:

1. Production zk-SNARK/STARK soundness, trusted-setup, or post-quantum security  
2. That D-3 runtime semantic authority is implemented  
3. Legal, regulatory, or operational certification for field deployment  
4. That mock scheme adapters are production verifiers  
5. That Stage 3.6+ runtime proof path or Matrix integration evidence is complete  

---

## 9. Document control

| Version | Date | Change |
|---------|------|--------|
| 3.2 baseline | (prior) | Phase 3.2 orientation |
| 2026-09-30 | 2026-09-30 | Gate 7 CLOSED / PASS (G7-CI) |
| 2026-10-01 | 2026-10-01 | Stage 3.5 formal CLOSED / PASS; full posture realignment |

**Reminder:** This sheet is a **compliance orientation**. It is not legal advice, regulatory certification, or proof that a ZKP construction is sound or privacy-preserving.