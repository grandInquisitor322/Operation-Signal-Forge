# Phase 2.7 — Independent Verification & Audit Hardening Foundations

**Operation Signal Forge**  
**Status:** Proposed Architecture Specification  
**Predecessor:** Phase 2.6 — Audit Log Governance & Identity Recovery Foundations (Complete; Architecture audit: PASS; Regression: 57/57)  
**Basis:** Phase 2.7 Gap Analysis (2026-08-17); ADR — Recovery Authority Model (Accepted, 2026-08-17)  
**Lifecycle position:** This document is Step 1 — Phase Specification — of the Phase Engineering Lifecycle. It precedes and governs the Step 2 Implementation Prompt; nothing here is implementation detail.  
**Purpose:** Close the verification-independence and audit-hardening gaps the Phase 2.6 architecture audit and compliance impact assessment surfaced, without expanding scope into items the Phase 2.7 Gap Analysis marked conditional, deferred, or decision-pending.

## Scope summary

| **#** | **Workstream** | **Gap closed** | **Classification** |
| --- | --- | --- | --- |
| 1 | Independent verification process | H1 | Foundation |
| 2 | Audit log retention governance | H7 | Foundation (light) |
| 3 | Privileged audit access self-auditing | H2 | Hardening |
| 4 | Adversarial isolation testing for recovery | H3 | Hardening |
| 5 | Tamper-evidence alert path | H4 | Hardening (light) |

## 1. Independent verification process

- Establish a verification step, distinct from the implementation pass, that re-executes the regression suite and spot-checks cited evidence before a PASS disposition is accepted.
- Define who or what performs this role — it need not be a different individual for every phase, but it must be functionally separate from whoever authored the implementation being verified.
- Define what "independently verified" means in practice: re-running tests rather than trusting a reported count, and checking at least a sample of cited file/function evidence against the actual repository state.
- Apply this to future phase audits going forward. Do not retroactively re-open the Phase 2.6 PASS disposition — that stands as recorded, with its self-report caveat intact.
- Keep this lightweight. This is a process control, not new software.

## 2. Audit log retention governance

- Document the retention policy already implemented in Phase 2.6 (per-event-type defaults, environment-variable overrides) as a named, owned policy artifact.
- Identify who is authorized to change retention defaults and under what circumstances.
- No change to the retention mechanism itself. This is documentation and ownership, not engineering.

## 3. Privileged audit access self-auditing

- Confirm whether use of the identity_audit:admin scope is itself captured in the audit trail.
- If it is not, add logging of privileged audit-log access — who accessed the audit store with admin scope, when, and for what operation.
- This closes a narrow, specific trust gap: today, ordinary audit access is governed, but it is not confirmed that governing the governors is itself observable.

## 4. Adversarial isolation testing for recovery

- Add tests that deliberately attempt the prohibited calls the Phase 2.6 audit confirmed absent by static inspection only: an attempt to invoke a credential lifecycle API, a Trust Registry mutation, or an Authorization Matrix scope grant from within the recovery execution path.
- Each such test must assert rejection or absence of effect, not merely absence of a call in the current code.
- This converts a structural claim ("no such import exists today") into a tested boundary that would catch a future regression, including one introduced by refactoring that a static read wouldn't catch.
- No change to what recovery is permitted to do. This adds coverage; it does not alter behavior.

## 5. Tamper-evidence alert path

- Add a scheduled or triggered execution of the existing verify_chain integrity check.
- On failure, surface an alert through the simplest available notification path already in use elsewhere in the project. Do not introduce new alerting infrastructure to support this.
- This is explicitly narrower than full centralized SIEM (G3), which remains deferred. The objective here is only to ensure a broken audit chain doesn't go unnoticed indefinitely for lack of anyone thinking to check.

## Conditional — not committed in this phase

- **G1 — Shared NonceStore backend.** Remains conditional on multi-node identity deployment being planned. Not scoped here.
- **G3 — Centralized SIEM.** Remains optional. Item 5 above addresses the narrowest, most time-sensitive slice of this gap without committing to the full scope.

## Explicitly deferred — do not implement

- **G5 — Additional DID methods.** Remains deferred pending a concrete interoperability requirement.
- **G7 — ZKP / selective disclosure.** Remains deferred, out of scope, per every prior phase's non-goals.

## Resolved prior to this phase

- **H5 — Recovery authority model.** Resolved via ADR (Accepted, 2026-08-17): single designated recovery authority is the baseline model; multi-party approval is documented as a future hardening option. This is a settled input to Phase 2.7, not open scope.

## Open — requires a decision before scoping, not assumed as build work

- **H6 — Holder recovery notification.** Whether a recovery event should notify the affected holder through an out-of-band channel remains an open question, contingent on whether such a channel exists in the current deployment. This specification does not resolve it and does not assume an answer. If a decision is made to pursue it, it should be scoped as its own addition, not folded silently into any of the five workstreams above.

## Architectural rule carries forward

Phase 2.7 must not redefine the credential lifecycle, the recovery authority model settled by the H5 ADR, or any of the eleven invariants preserved through Phase 2.6. It must not redesign the recovery executor, the Trust Registry, the Authorization Matrix, the Capability Layer, or Fusion/sensor logic. It must not implement ZKP, additional DID methods, or external DID infrastructure.

**Note:** classify each item as Foundation, Hardening, or Future/Deferred, as shown in the scope summary table above.
