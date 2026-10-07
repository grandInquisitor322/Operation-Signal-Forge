# Phase 2.8 — Gap Analysis

*Operation Signal Forge*  
*Post-Phase 2.7 Planning Artifact*  
*Date: August 19, 2026*  
*Predecessor: Phase 2.7 — Identity Assurance & Governance Hardening (Closed)*

## 1. Purpose

This document identifies what remains open after Phase 2.7 so Phase 2.8 can be scoped deliberately. It is an analysis artifact, not an implementation plan or a commitment of work.

Phase 2.7 closed with Architecture PASS, a completed non-certifying compliance assessment, and a 64/64 validation result. Its first independent-verification exercise is recorded separately with an explicit re-execution-rigor limitation.

## 2. Evidence Baseline

| Baseline | Status |
| --- | --- |
| Phase 2.7 implementation / regression | 64/64 PASS |
| Phase 2.7 Architecture Audit | PASS with H1 re-execution-rigor limitation |
| Phase 2.7 Compliance Impact | ACCEPTABLE; H1 limitation carried forward |
| H1 verification record | Present; second-party, not isolated CI |
| H7 retention governance | Delivered |
| H2 privileged audit self-auditing | Delivered |
| H3 adversarial isolation tests | Delivered |
| H4 tamper-detection response | Delivered |

## 3. What Phase 2.7 Closed

Independent Verification process existence (H1 process control).

Retention governance ownership and change authority (H7).

Privileged audit self-auditing (H2).

Behavioral adversarial isolation testing (H3).

Minimal tamper-detection response (H4).

Recovery authority model explicitly settled through the H5 ADR.

## 4. What Remains Open

H1 — Independent verification re-execution rigor.

G1 — Multi-node NonceStore, conditional on deployment topology.

G3 — Centralized identity-security monitoring/SIEM, optional.

G5 — Additional DID methods, deferred.

G7 — ZKP/selective disclosure, deferred.

H6 — Holder recovery notification, deferred pending a trustworthy independent channel.

## 5. Gap I1 — Independent Verification Re-Execution Rigor

**Classification: FOUNDATION / HIGH PRIORITY**

The H1 process now exists and a verification record is persisted, but the first exercise relied on implementer-reported console PASS output plus repository spot-checking rather than verifier-controlled isolated execution.

Independent verifier-controlled test execution.

Clear evidence artifact showing verifier-run results.

Repeatable verification environment.

Explicit distinction between spot-check verification and full re-execution.

This is an assurance-process maturity gap, not evidence that the Phase 2.7 implementation controls failed.

## 6. H1 Process Governance — Standing Verification Threshold

**Classification: PROCESS DECISION**

Determine whether full verifier-controlled execution should be mandatory for every future Architecture Audit or triggered only by a risk/phase threshold.

Define when isolated verifier-run execution is mandatory.

Define when repository spot-checking is sufficient.

Define who is eligible to perform independent verification.

Keep the eight-step Phase Engineering Lifecycle unchanged; this remains a Step 4 control.

## 7. Gap G1 — Multi-Node NonceStore

**Classification: CONDITIONAL / DEFERRED**

The NonceStore remains single-host oriented. It is not a current correctness defect under the present topology but becomes important if identity presentation becomes multi-node.

Do not implement shared nonce storage unless multi-node identity deployment is explicitly committed.

## 8. Gap G3 — Centralized Identity Security Monitoring

**Classification: OPTIONAL / HARDENING**

Phase 2.7 added a narrow tamper-detection response but did not introduce full centralized SIEM/aggregation. Central monitoring remains optional.

## 9. Gap G5 — DID Method Expansion

**Classification: FUTURE-DEFERRED / CONDITIONAL**

The Identity Layer remains intentionally narrow with did:key as the accepted and managed baseline. No concrete interoperability requirement currently justifies expanding DID support.

## 10. Gap G7 — ZKP / Selective Disclosure

**Classification: FUTURE-DEFERRED**

ZKP and selective disclosure remain explicitly deferred. Their absence is not a Phase 2.7 defect and should not be promoted into Phase 2.8 without a separate scope decision.

## 11. Gap H6 — Holder Recovery Notification

**Classification: CONDITIONAL / DECISION**

Phase 2.7 deferred holder notification because no trustworthy independent channel was available.

Determine whether a trustworthy out-of-band channel exists.

Determine whether the legitimate holder would receive it.

Do not add a notification mechanism that creates false assurance.

## 12. Closed Gaps That Should Not Reopen

H7 retention governance ownership.

H2 privileged audit self-auditing.

H3 adversarial isolation testing baseline.

H4 minimal tamper-detection response.

H5 single designated recovery authority baseline.

Credential lifecycle separation.

Trust Registry / Authorization Matrix / Capability Layer boundaries.

## 13. Phase 2.8 Prioritization

| Gap / Decision | Classification | Treatment |
| --- | --- | --- |
| I1 — Independent verification re-execution rigor | Foundation / MUST CONSIDER | Primary candidate |
| H1 standing verification threshold | Process decision | Resolve before specification |
| H6 holder notification | Conditional | Only if trustworthy channel exists |
| G3 centralized monitoring/SIEM | Optional hardening | Conditional |
| G1 shared NonceStore | Conditional | Only with multi-node plan |
| G5 additional DID methods | Future-deferred | Concrete interoperability need required |
| G7 ZKP/selective disclosure | Future-deferred | Separate future scope decision |

## 14. Recommended Phase 2.8 Direction

1. Close the H1 independent-re-execution rigor gap.
2. Formalize the risk-based threshold for when full independent test execution is required.
3. Resolve H6 only if a trustworthy notification channel exists.
4. Reassess G3/G1 only when deployment topology or operational monitoring requirements justify them.
5. Keep G5 and G7 deferred until concrete requirements emerge.

## 15. Decision Questions Before Phase 2.8 Specification

Should full verifier-controlled CI execution be required for every future Architecture Audit?

If not, what risk/phase threshold triggers mandatory isolated execution?

Does Signal Forge have a trustworthy independent channel for holder recovery notification?

Is there a near-term plan for multi-node identity deployment?

Is there a concrete operational requirement for centralized identity-security monitoring?

Has a real counterparty/partner requirement emerged for another DID method?

## 16. Hard Boundaries

No credential lifecycle redesign.

No automatic credential mutation through recovery.

No automatic privilege restoration.

No Trust Registry redesign.

No Authorization Matrix redesign.

No Capability Layer redesign.

No mandatory external DID infrastructure.

No ZKP/selective-disclosure implementation without a separate scope decision.

## 17. Conclusion

Phase 2.7 substantially reduced governance and assurance gaps around the Identity Layer. The most important remaining issue is now assurance maturity: how independently and rigorously the project proves that its controls work.

**Phase 2.8 should therefore mature the assurance process before expanding the Identity Layer into new interoperability or privacy capabilities.**

This gap analysis does not commit Phase 2.8 to a specific implementation scope. It identifies evidence-backed gaps and the decisions required before the next specification.

**PHASE 2.8 GAP ANALYSIS — READY FOR ARCHITECTURAL REVIEW**
