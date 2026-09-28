# ZKP Compliance Carry-Forward

**Project:** Operation Signal Forge  
**Status:** Standing reference (not a phase closure)  
**Last aligned through:** Phase 3.2 (Gate 3.2 → 3.3 SATISFIED)  
**Nature:** Technical compliance guardrails — **non-certifying**

Use this sheet when starting Stage **3.3+** or any phase that touches proofs, context representation, or authorization inputs. Do **not** weaken these without a new ADR and an explicit compliance impact note.

---

## 1. Purpose of the future proof (fixed)

**Use case (singular):**

> Prove that the presenter is an eligible emergency responder for a **specified active** disaster-response context, without revealing unnecessary credential or identity information.

- One end-to-end proof target — no silent second use case  
- Implementation-neutral until protocol stages  
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

## 4. What Stage 3.3+ must still supply (not done yet)

| Topic | Status |
|-------|--------|
| Context representation (IDs, records, references) | Stage **3.3** |
| Witness / public-input boundary | Stage **3.4** |
| Protocol / circuit | Stage **3.5** |
| Runtime proof path + Matrix integration evidence | Stage **3.6+** |
| Deployment precedence among conflicting authorities | Required later; not designed in 3.2 |
| Trust/conflict *mechanisms* | Requirements only today |

---

## 5. Verification (H1) guardrail

- Definition/packaging phases (3.0–3.2): Level **1–2** as justified — **not** automatic Level 3.  
- **A Level 2 PASS on a non-crypto phase does not justify skipping Level 3** when cryptographic runtime or proof-on-the-path work begins.  
- Prefer itemized `verifier_run_results` and explicit `limitations` on binding records.  
- Do not delete verification JSONL rows; supersede in notes if classification changes.  

---

## 6. Post-integration evidence checklist (fill later)

When a proof is actually on a critical path, compliance updates should be able to point to evidence for:

- [ ] Public/verifier-visible outputs match the privacy intent (min necessary)  
- [ ] Matrix can **deny** after a **valid** proof  
- [ ] Context binding respects activation / expiry / revocation semantics  
- [ ] Proof and verification logs classified (retention, re-identification risk)  
- [ ] No capability executes on verify-alone without Matrix  
- [ ] Dependencies / licenses for proving stack recorded  
- [ ] H1 level appropriate to crypto + authz-boundary risk  

---

## 7. Doc map (where the decisions live)

| Topic | Primary doc |
|-------|-------------|
| Cryptographic objective / privacy / success boundary | `docs/architecture/zkp/phase-3.0-cryptographic-objective-and-proof-use-case.md` |
| Use case + design principles 1–3 | `docs/architecture/zkp/phase-3.1-proof-use-case-selection.md` |
| Authority & responder model | `docs/architecture/zkp/phase-3.2-disaster-context-authority-and-responder-model.md` |
| This carry-forward | `docs/compliance/zkp-compliance-carry-forward.md` |

---

**Reminder:** This sheet is a **compliance orientation** for future phases. It is not legal advice, regulatory certification, or proof that a future ZKP construction is sound or privacy-preserving.