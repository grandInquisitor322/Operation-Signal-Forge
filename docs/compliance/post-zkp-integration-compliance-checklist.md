# Post-ZKP Integration Compliance Checklist

**Project:** Operation Signal Forge  
**Status:** Standing checklist (fill when proof is on a critical path)  
**Do not use to claim completion of Stage 3.0–3.2** — those phases intentionally have no cryptographic runtime  
**Nature:** Technical compliance evidence list — **non-certifying**

**Related:**  
- `docs/compliance/zkp-compliance-carry-forward.md`  
- `docs/compliance/verification-trail-conventions.md`  
- Phase 3.0–3.2 architecture packages under `docs/architecture/zkp/`

---

## How to use

1. Keep all Phase 3.0–3.2 **boundaries** intact (carry-forward sheet).  
2. As Stages **3.3 → 3.6+** land, check items when evidence exists — not before.  
3. Each checked item should cite **artifact + test or record id** (no bare “done”).  
4. H1 verification for crypto-on-path work should expect **Level 2–3**, not a free ride from packaging-phase Level 2.

---

## A. Purpose and scope still hold

| ID | Check | Evidence cite (path / test / verification id) | Status |
|----|--------|-----------------------------------------------|--------|
| A1 | Single use case unchanged unless a **new** scope ADR says otherwise | | ☐ |
| A2 | Proof still targets eligible emergency responder × **specified active** context | | ☐ |
| A3 | No second proof statement shipped “while we were here” without scope decision | | ☐ |
| A4 | Privacy intent still “unnecessary credential/identity not required for the decision” | | ☐ |

---

## B. Minimum necessary disclosure (Principle 1)

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| B1 | Documented list of **verifier-visible** outputs / public inputs | | ☐ |
| B2 | Each visible field justified as necessary for the eligibility decision | | ☐ |
| B3 | Attributes not on that list are not implied as revealed by “proof verified” | | ☐ |
| B4 | Proof is not used as a substitute for general credential presentation | | ☐ |
| B5 | Divergence from Phase 3.0 privacy statement is explicitly impact-assessed | | ☐ |

---

## C. Context binding (Principles 2 + Phase 3.2 lifecycle)

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| C1 | Proof/claim binds to a **specific** context reference (Stage 3.3 representation) | | ☐ |
| C2 | Success is not treated as eligibility for unrelated contexts | | ☐ |
| C3 | Success is not treated as open-ended eligibility after expiry/revocation | | ☐ |
| C4 | Context **activation** comes from Authorized Incident Authority model, not verifier inference | | ☐ |
| C5 | Expiry / revocation / supersession behavior documented and tested at the integration boundary | | ☐ |
| C6 | No hard-coded universal org (FEMA/Red Cross/SAR/AHJ) as the authority model in code | | ☐ |

---

## D. Authorization separation (Principle 3)

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| D1 | Verify path returns a **claim/result**, not a capability grant | | ☐ |
| D2 | Authorization Matrix can **deny** after a **valid** proof | | ☐ |
| D3 | No capability executes on proof-verify alone | | ☐ |
| D4 | Tests cover valid-proof + Matrix-deny | | ☐ |
| D5 | Logs/UI do not label “proof verified” as “authorized” | | ☐ |

---

## E. Qualification / assignment claims

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| E1 | Qualification claims remain distinct from assignment claims in data/API semantics | | ☐ |
| E2 | Assignment does not silently assert all qualification attributes | | ☐ |
| E3 | Qualification without assignment remains representable where product requires it | | ☐ |
| E4 | ZKP verifier is not modeled as qualification or assignment authority | | ☐ |

---

## F. Trust, conflict, and authority credentials

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| F1 | Authoritative context declarations distinguishable from unauthenticated assertions | | ☐ |
| F2 | Authority credential expiry/revocation rules documented for production path | | ☐ |
| F3 | Bounded delegation (if used) cannot exceed scope | | ☐ |
| F4 | ZKP verifier does **not** adjudicate conflicting authorities | | ☐ |
| F5 | Deployment precedence policy exists before multi-authority production reliance | | ☐ |

---

## G. Logging, retention, and data minimization

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| G1 | Proof material / public inputs / verify results classified (what is stored) | | ☐ |
| G2 | Retention period defined for verification logs | | ☐ |
| G3 | Re-identification risk of logs assessed (holder linkage) | | ☐ |
| G4 | Verification evidence store remains separate from G4 identity-audit authority abuse paths | | ☐ |
| G5 | No private keys or raw full credentials in verification or app logs | | ☐ |

---

## H. Cryptographic and dependency assurance

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| H1 | Proving system / library versions pinned and recorded | | ☐ |
| H2 | Third-party licenses recorded for proving stack | | ☐ |
| H3 | Setup/parameters governance documented (who may change verifying keys/params) | | ☐ |
| H4 | Failure modes documented (invalid proof, wrong context, stale context) | | ☐ |
| H5 | Soundness / ZK / binding claims are either evidenced or explicitly residual | | ☐ |

*H5 must not be checked as “done” on marketing language alone.*

---

## I. H1 independent verification (process)

| ID | Check | Evidence cite | Status |
|----|--------|---------------|--------|
| I1 | Binding verification record id for the integration phase | | ☐ |
| I2 | Level justified (expect 2–3 for proof-on-path); no free skip from 3.0–3.2 Level 2 | | ☐ |
| I3 | Itemized `verifier_run_results` with `runner: verifier` | | ☐ |
| I4 | Level 3 only with `execution_context` + non-empty limitations | | ☐ |
| I5 | Trail conventions followed (append-only; supersede in notes if needed) | | ☐ |

---

## J. Sign-off block (when used)

| Field | Value |
|-------|--------|
| Phase / stage | |
| Date | |
| Binding verification id | |
| Architecture audit disposition | |
| Compliance impact disposition | |
| Known residuals (short) | |
| Verifier role | |
| Implementer role | |

---

## Out of scope for this checklist

- Replacing the Authorization Matrix with proofs  
- Using ZKP as incident command or disaster declaration  
- Claiming regulatory certification  
- Completing this list during definition-only phases (3.0–3.2)

---

**Reminder:** Checking boxes requires **cited evidence**. This checklist is a work planner for integration-phase compliance updates, not a certificate of cryptographic or legal compliance.