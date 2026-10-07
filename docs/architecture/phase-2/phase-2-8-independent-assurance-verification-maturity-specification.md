# Phase 2.8 — Independent Assurance & Verification Maturity Specification

*Operation Signal Forge*  
*Status: Architecture Specification*  
*Predecessor: Phase 2.7 — Identity Assurance & Governance Hardening*  
*Date: August 19, 2026*

## 1. Purpose

Phase 2.8 matures the Independent Verification control established in Phase 2.7. Its primary objective is to define and implement proportional verification rigor so that future Architecture Audit dispositions are supported by evidence appropriate to the risk and consequence of the changes being audited.

Phase 2.8 is an assurance-process phase, not a new Identity Layer feature phase. The existing eight-step Phase Engineering Lifecycle remains unchanged.

## 2. Scope Basis

Phase 2.7 — Identity Assurance & Governance Hardening milestone: closed.

Phase 2.7 Gap Analysis: independent-verification re-execution rigor identified as the primary remaining assurance gap.

ADR — Risk-Based Verification Levels for Independent Verification (H1): Accepted.

Phase 2.7 H1 record: second-party verification with repository spot-checking; isolated verifier-controlled execution not yet performed.

## 3. Architectural Decision Carried Forward

**Isolated verifier-controlled execution is not mandatory for every phase. Verification rigor is risk-based.**

The accepted H1 ADR establishes three verification levels and requires stronger verification as risk and consequence increase. When the appropriate level is ambiguous, the stronger level is selected.

## 4. Phase 2.8 Primary Workstream — I1: Verification Assurance Levels

**Classification: FOUNDATION / PRIMARY**

Phase 2.8 shall define the operational mechanism by which a phase is assigned and recorded at Verification Level 1, 2, or 3.

### 4.1 Level 1 — Evidence Review / Spot-Check

For low-risk changes such as documentation-only work, non-security configuration, or low-impact refactors.

Reviewer is distinct from the implementer.

Review reported evidence and spot-check repository state.

No mandatory suite re-execution.

### 4.2 Level 2 — Independent Test Re-Execution

For meaningful behavioral changes without especially high-risk identity, authorization, recovery, cryptographic, or compliance consequences.

Reviewer independently re-runs relevant regression suites.

Execution need not occur in a fully isolated environment.

Reported implementer console output cannot be the sole evidence.

### 4.3 Level 3 — Isolated Verifier-Controlled Execution

Expected for high-consequence changes involving identity/authentication.

Expected for authorization/access control.

Expected for credential lifecycle changes.

Expected for identity recovery.

Expected for cryptographic/security controls.

Expected for audit/compliance infrastructure.

Expected for any change where an incorrect PASS could materially compromise architectural or operational security.

The list is guidance rather than an exhaustive enumeration. The determining factor is consequence, not the component name alone.

## 5. Verification-Level Assignment

At the beginning of Step 4 — Tests & Validation, the phase author and/or assigned independent verifier shall record:

Selected verification level (1, 2, or 3).

Risk/consequence rationale.

Relevant changed domains and architectural boundaries.

Expected evidence.

Verifier identity/role.

**When the appropriate verification level is ambiguous, select the stronger level.**

## 6. Independent Verification Record

Each verification record shall contain, at minimum:

Unique verification identifier.

Verifier identity/role.

Implementer identity/role.

Phase and verification scope.

Verification level.

Suites/evidence reviewed or executed.

Verification result.

Evidence type.

Limitations.

Date/time of verification.

## 7. Level 3 Environment Requirements

Level 3 requires the verifier to control the execution environment end-to-end so that the implementation environment cannot itself create a false PASS.

Separate verifier-controlled execution context.

Independent configuration where practical.

Independent execution of the required regression suites.

Captured verifier-run results.

Explicit record of environment and material limitations.

## 8. Evidence Integrity and Separation

Verification records must remain separate from the governed identity audit trail.

The verification API must not require identity_audit:admin.

Verifier activity must not gain authority to purge or mutate the governed audit chain.

Verification records must not contain reusable authentication material.

## 9. Architecture Audit Relationship

The Architecture Audit consumes the verification record as evidence. It does not redefine the H1 model or retroactively upgrade weak evidence into stronger evidence.

The audit records whether the selected verification level was appropriate.

The audit confirms whether required evidence exists.

The audit records any verification limitation.

A verification failure or insufficient evidence is not silently converted into PASS.

## 10. Phase 2.8 Decision and Escalation Rules

Low-risk phases may use Level 1.

Meaningful behavioral phases may use Level 2.

High-consequence security, identity, recovery, authorization, credential, cryptographic, or compliance phases require Level 3 unless an explicit architectural decision records why a lower level is appropriate.

Uncertainty between levels escalates to the stronger level.

## 11. Non-Goals

Do not add a ninth Phase Engineering Lifecycle step.

Do not redesign the existing eight-step lifecycle.

Do not retroactively reopen Phase 2.6 or Phase 2.7.

Do not require a specific CI provider.

Do not require a permanent QA department.

Do not require isolated execution for documentation-only or otherwise demonstrably low-risk phases.

Do not redesign identity, credential, authorization, Trust Registry, Capability Layer, Fusion, or Sensor architecture.

## 12. Conditional / Deferred Items

G1 — Shared NonceStore remains conditional on multi-node identity deployment.

G3 — Centralized SIEM remains optional.

G5 — Additional DID methods remain future-deferred.

G7 — ZKP/selective disclosure remain future-deferred.

H6 — Holder recovery notification remains conditional on availability of a trustworthy independent channel.

## 13. Testing Requirements

Phase 2.8 shall test the verification control itself, including:

Verification-level assignment is recorded.

Ambiguous risk classifications escalate upward.

Level 1 records include evidence review/spot-check details.

Level 2 records include verifier-run suite results.

Level 3 records identify the verifier-controlled execution context.

Verification records are persisted and retrievable.

Verification records remain separate from the governed identity audit trail.

Verifier roles cannot mutate or purge the governed audit trail through the H1 API.

## 14. Regression Gate

The complete established regression baseline remains required for any Phase 2.8 implementation that changes repository behavior.

Phase 2.2 renewal / rotation.

Phase 2.3 Trust Registry governance.

Phase 2.4 identity infrastructure.

Phase 2.5 DID method policy.

Phase 2.5 recovery policy.

Phase 2.6 audit + recovery.

Phase 2.7 assurance tests.

## 15. Definition of Done

Risk-based verification levels are defined and implemented.

Each phase records a verification level and rationale.

The independent verification record captures the selected level and evidence.

Level 2 supports independent suite re-execution.

Level 3 supports verifier-controlled isolated execution.

Ambiguous cases escalate to the stronger level.

Verification records remain separated from the Identity Layer audit authority.

Architecture Audit consumes, but does not rewrite, verification evidence.

The eight-step Phase Engineering Lifecycle remains unchanged.

All required regression suites pass.

## 16. Architectural Invariants

Credential lifecycle remains unchanged.

Identity recovery remains distinct from credential renewal/revocation.

Identity recovery remains distinct from authorization restoration.

DID resolution remains distinct from issuer trust.

DID identity remains distinct from authorization.

Trust Registry governance remains distinct from holder authorization.

Identity infrastructure remains distinct from operational infrastructure.

Audit logs remain distinct from reusable authentication storage.

Verification process remains distinct from audit-trail authority.

## 17. Governance Principle

**The stronger the consequence of a false PASS, the stronger the evidence required before the architecture can be declared verified.**

## 18. Conclusion

Phase 2.8 establishes a proportional, repeatable assurance model for future phases. It closes the independent-verification rigor gap identified in Phase 2.7 without turning every change into a heavyweight audit exercise.

The result is a stable eight-step Phase Engineering Lifecycle in which verification rigor scales with risk, and Architecture Audit decisions are supported by explicit, traceable evidence.
