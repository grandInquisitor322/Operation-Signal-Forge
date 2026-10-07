# Phase 2.6 — Audit Governance & Identity Recovery Foundations Specification

*Operation Signal Forge*  
*Status: Architecture Specification*  
*Predecessor: Phase 2.5 — Identity Operational Hardening & Interoperability Foundations*  
*Date: August 15, 2026*

## 1. Purpose

Phase 2.6 addresses the highest-leverage confirmed gaps remaining after Phase 2.5. The scope is intentionally narrow and is based on the Phase 2.5 Gap Analysis, repository verification, Architecture Audit, and Compliance Impact Assessment.

Phase 2.6 prioritizes two workstreams:

G4 — Audit Log Governance

G2 — Identity Recovery Executor

G4 is addressed first because it closes a confirmed compliance/control gap and establishes the governance foundation required for sensitive identity events such as recovery. G2 follows as a bounded operational capability built under the recovery policy already established in Phase 2.5.

## 2. Source and Verification Basis

The Phase 2.6 scope is grounded in the following completed evidence:

Phase 2.5 Architecture Audit — PASS

Phase 2.5 combined validation — 50/50 PASS

Phase 2.5 Compliance Impact Assessment

Phase 2.6 Gap Analysis

Repository verification of G1–G8

## 3. Confirmed Gap Classification

| Gap | Classification | Phase 2.6 treatment |
| --- | --- | --- |
| G4 — Audit log governance | Foundation / MUST | Primary Phase 2.6 workstream |
| G2 — Recovery executor | Foundation / MUST | Secondary Phase 2.6 workstream |
| G3 — Centralized audit visibility | Hardening / SHOULD | Conditional; not required for core 2.6 closure |
| G1 — Shared nonce backend | Conditional | Only if multi-node identity deployment is committed |
| G6 — External-resolution review trigger | Light Foundation / SHOULD | Governance/process item; may be handled alongside policy documentation |
| G5 — Additional DID methods | Future / Conditional | Remain deferred without a concrete interoperability requirement |
| G7 — ZKP / selective disclosure | Future / Deferred | Remain explicitly out of scope |

## 4. Mandatory Architectural Rule

**Phase 2.6 must not redefine the existing credential lifecycle.**

Credential issuance, presentation, renewal, rotation, expiration, and revocation semantics established through Phases 2.1–2.5 remain unchanged.

Audit governance must govern identity audit artifacts without changing credential semantics.

Identity recovery must not become credential renewal or revocation.

Identity recovery must not silently restore authorization scopes.

Audit logging must not become a secondary credential/proof store.

## 5. Workstream G4 — Audit Log Governance

G4 is the primary Phase 2.6 workstream. The repository verification confirmed that presentation audit data exists, but formal retention, role-based access control, and tamper-evidence are largely absent beyond ordinary filesystem controls.

**G4 objective: make identity audit data explicitly governed, access-controlled, retained, and integrity-protected.**

### 5.1 Retention Policy

Define formal retention requirements for identity audit events.

Classify audit event categories.

Define retention duration for each category.

Define purge/archive behavior.

Define handling for expired audit records.

Ensure retention does not preserve raw authentication material unnecessarily.

### 5.2 Audit Access Control

Define who may read identity audit records and under what conditions.

Explicit role/scope for audit-log access.

Least-privilege read access.

Authorization of administrative/audit queries.

Denial behavior for unauthorized audit access.

Auditability of privileged access where appropriate.

### 5.3 Tamper-Evidence and Integrity

Define and implement an integrity mechanism appropriate to the current deployment architecture.

Detect unauthorized modification of audit records.

Define integrity verification behavior.

Define failure behavior when integrity verification fails.

Preserve the audit event itself without introducing reusable authentication material.

Avoid unnecessary coupling to a specific future SIEM provider.

### 5.4 Audit Data Boundary

Identity audit events remain within the identity/audit domain.

Operational sensor and detection telemetry remain separate.

Raw VCs, private keys, reusable proofs, and challenge secrets remain excluded unless a separately approved requirement exists.

### 5.5 G4 Success Criteria

Formal retention policy exists.

Audit-log read access is explicitly controlled.

Unauthorized audit access is denied.

Audit record integrity/tamper evidence is implemented or explicitly scoped to the approved deployment mechanism.

Retention and access behavior are tested.

No reusable authentication material is introduced into the audit store.

## 6. Workstream G2 — Identity Recovery Executor

G2 is the secondary Phase 2.6 workstream. Phase 2.5 already established recovery triggers, authority, audit shape, and key lifecycle primitives, but the recovery workflow is intentionally not executable today.

**G2 objective: provide a tightly bounded recovery executor without changing credential lifecycle or authorization policy.**

### 6.1 Recovery Boundary

Recovery restores or re-establishes control of an identity. It does not automatically restore credential authority or operational authorization.

Identity recovery ≠ credential renewal.

Identity recovery ≠ credential revocation.

Identity recovery ≠ automatic scope restoration.

### 6.2 Recovery Workflow

The implementation should follow the existing Phase 2.5 recovery policy:

Recovery Request
↓
Authorize / Approve
↓
Retire compromised or unavailable verification method
↓
Activate replacement identity key
↓
Record auditable recovery event
↓
Resume normal identity verification

### 6.3 Recovery Requirements

Accept only authorized recovery requests.

Preserve the DID identity where policy permits.

Retire compromised or unavailable verification methods.

Activate a replacement verification method.

Record the recovery event using governed audit controls.

Fail safely if authorization or evidence requirements are not satisfied.

Preserve existing credential state unless a separate credential lifecycle operation is intentionally invoked.

### 6.4 Explicit Recovery Prohibitions

No automatic credential reissuance.

No automatic privilege restoration.

No automatic Authorization Matrix changes.

No hidden recovery authority.

No bypass of Trust Registry governance.

### 6.5 Recovery Failure and Security Behavior

Unauthorized recovery requests must be denied.

Recovery of a compromised identity key must not allow the compromised key to remain active.

A failed recovery must not partially restore identity control.

Recovery actions must be auditable.

### 6.6 G2 Success Criteria

Authorized recovery request succeeds through the defined workflow.

Unauthorized recovery request fails.

Old/compromised key is retired.

Replacement key becomes active.

DID continuity is preserved where applicable.

No credential or authorization-policy mutation occurs as an automatic recovery side effect.

Recovery events are recorded through the governed audit path.

## 7. Conditional Workstreams

### 7.1 G3 — Centralized Audit Visibility

Centralized audit aggregation, alerting, or SIEM integration is not required for core Phase 2.6 closure. It may be added if deployment requirements justify it.

If implemented, it must consume the existing governed audit events and must not increase the amount of sensitive identity material logged merely to support monitoring.

### 7.2 G1 — Shared Nonce Backend

The existing NonceStore is correct for the current single-host topology. A shared backend becomes a Phase 2.6 requirement only if multi-node identity deployment is explicitly planned.

The existing NonceStore interface should remain the abstraction boundary.

### 7.3 G6 — External-Resolution Review Trigger

A lightweight governance/process mechanism may formalize when the project reviews its did:key-only DID method and local-resolution policy. This must remain a policy process rather than automatic activation of external resolution.

## 8. Explicitly Deferred

### 8.1 G5 — Additional DID Methods

Additional DID methods remain deferred unless a concrete interoperability requirement emerges.

### 8.2 G7 — ZKP / Selective Disclosure

Zero-Knowledge Proofs and full selective disclosure remain explicitly deferred. They require a separate, explicit architecture and scope decision.

## 9. Operational and Architectural Boundaries

No Fusion Engine changes.

No Sensor Module changes.

No DetectionReadPort redesign.

No Capability Layer identity logic.

No Trust Registry redesign.

No Authorization Matrix redesign.

No credential lifecycle redesign.

No movement of operational sensor/detection data into identity infrastructure.

## 10. Privacy and Compliance Requirements

Audit retention must follow minimum-necessary data principles.

Audit access must be least-privilege.

Tamper-evidence must not require retaining reusable authentication material.

Recovery evidence must be limited to what is required to authorize and audit recovery.

Identity audit records remain distinct from humanitarian operational telemetry.

## 11. Testing Requirements

Phase 2.6 must include tests for:

Retention policy behavior.

Audit-log access authorization and denial.

Audit-record integrity/tamper detection.

Recovery authorization and denial.

Key retirement and replacement during recovery.

Recovery audit events.

Credential lifecycle regression.

Trust Registry governance regression.

Identity infrastructure regression.

## 12. Regression Gate

Phase 2.6 is not complete unless the established Phase 2.2, Phase 2.3, and Phase 2.4 regression suites continue to pass.

Phase 2.2 renewal / rotation

Phase 2.3 Trust Registry governance

Phase 2.4 identity infrastructure

## 13. Definition of Done

G4 retention policy is defined and implemented.

G4 audit-log access control is defined and implemented.

G4 audit integrity/tamper-evidence is defined and implemented or explicitly approved for the deployment model.

G2 recovery executor is implemented within the existing policy boundary.

Recovery does not automatically modify credentials or authorization.

G3 is either explicitly deferred or implemented without expanding sensitive audit collection.

G1 remains deferred unless multi-node identity deployment is committed.

G6 review trigger is documented if retained in Phase 2.6 scope.

G5 and G7 remain deferred unless separately re-scoped.

All established regression suites remain passing.

Architecture boundaries remain intact.

Architecture audit and compliance impact assessment are updated.

## 14. Phase 2.6 Decision Summary

| Item | Classification | Phase 2.6 Treatment | Decision |
| --- | --- | --- | --- |
| G4 — Audit Log Governance | Foundation / MUST | Primary workstream | IN |
| G2 — Identity Recovery Executor | Foundation / MUST | Secondary workstream | IN |
| G3 — Centralized Audit Visibility | Hardening / SHOULD | Conditional | OPTIONAL |
| G1 — Shared Nonce Backend | Conditional | Only with multi-node plan | DEFER |
| G6 — Resolution Review Trigger | Light Foundation | Process/governance | OPTIONAL |
| G5 — Additional DID Methods | Future / Conditional | Concrete interoperability trigger required | DEFER |
| G7 — ZKP / Selective Disclosure | Future / Deferred | Separate future scope decision | DEFER |

## 15. Architectural Principle

**Make the identity system governable and auditable first; then make it recoverable.**

Phase 2.6 should strengthen the controls around existing identity infrastructure rather than expanding the Identity Layer into unrelated interoperability, privacy, or operational domains.

**PHASE 2.6 SPECIFICATION — READY FOR IMPLEMENTATION PLANNING**
