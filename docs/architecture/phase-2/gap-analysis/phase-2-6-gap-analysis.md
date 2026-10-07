# Phase 2.6 — Gap Analysis

**Created by:** Claude  
**Model:** Sonnet 5  
**Time of record:** 2026-08-15  
**Predecessor:** Phase 2.5 — Identity Operational Hardening & Interoperability Foundations (Status: Complete, Architecture audit: PASS)  
**Purpose:** Identify what remains open after Phase 2.5 so Phase 2.6 can be scoped deliberately. This is an analysis document, not an implementation plan or a commitment of work.

## Purpose & scope

Phase 2.5 closed with a PASS architecture audit, a 50/50 regression suite, and a recorded (non-certifying) compliance impact assessment. It also closed carrying three named residuals and four explicit non-goals. This analysis takes those residuals, non-goals, and the compliance assessment's flagged open items as its raw material, and asks a single question for each: **is this now a candidate for Phase 2.6, or should it remain deferred?**

This document does not reopen Phase 2.5. The credential lifecycle, the nine preserved invariants, and the architecture audit's PASS verdict are treated as settled and are not re-evaluated here.

## Inputs used

- Phase 2.5 milestone record (delivered artifacts, residuals, explicit non-goals, validation results)
- Phase 2.5 Architecture Audit — Final Verification (workstreams A–E, nine invariants, cross-boundary checks)
- Phase 2.5 Compliance Impact Assessment (flagged open items on retention, audit-log access control, and tamper-evidence)

## Gap register

| **ID** | **Area** | **Gap** | **Source** |
| --- | --- | --- | --- |
| G1 | Nonce store | File-backed store is single-host; no shared backend for multi-node deployment | Residual |
| G2 | Recovery | Policy and approver role defined; no working executor — recovery cannot actually be performed today | Residual |
| G3 | Audit logging | In-process append only; no centralized aggregation, alerting, or SIEM integration | Residual |
| G4 | Audit log governance | Retention duration, access control over audit logs, and tamper-evidence are undefined | Compliance assessment — open item |
| G5 | DID method coverage | Accepted = managed = did:key only; no other method has been evaluated against the Phase 2.5 future-expansion criteria | Non-goal boundary, not yet revisited |
| G6 | External resolution | No process exists for deciding when to move beyond local resolution; criteria were defined but never triggered or reviewed | Non-goal boundary, not yet revisited |
| G7 | ZKP / selective disclosure | Interfaces were confirmed extensible on paper; nothing has exercised that extensibility in practice | Non-goal, explicitly deferred |
| G8 | Recovery execution risk | No automated recovery or reissue exists; for a system supporting time-sensitive field operations, this is an operational exposure worth a deliberate decision, not just a residual | Non-goal, flagged for decision |

## Gap detail

**G1 — Nonce store scalability.**

The current store is correct and durable on a single host but has no shared backend. If Signal Forge identity infrastructure ever runs across more than one node, nonce state will fragment and replay protection will weaken across nodes. *Impact if unaddressed:* low today (single-host), becomes a correctness gap the moment horizontal scaling is introduced elsewhere in the system. *Phase 2.6 candidate:* Hardening — swap backend behind the existing interface; no interface redesign implied.

**G2 — Recovery cannot be executed.**

Phase 2.5 deliberately built policy, not execution. That was correct scope discipline for 2.5, but it means that today, a holder who loses or compromises identity keys has no actual recovery path — only a defined policy for what recovery would look like. *Impact if unaddressed:* an operational identity system without a working recovery path is a real gap, not just a documentation gap. *Phase 2.6 candidate:* Foundation-level build, tightly scoped to the existing policy boundary (no auto-reissue, no auto-privilege-restoration) established in 2.5.

**G3 — No centralized audit visibility.**

Presentation-proof events are logged, but only in-process. There is no aggregation point and no alerting. *Impact if unaddressed:* a security-relevant event (e.g., repeated nonce-replay attempts) would currently go unnoticed unless someone manually inspects logs. *Phase 2.6 candidate:* Hardening — ship existing audit events to a centralized sink; does not require changing what's logged.

**G4 — Audit log governance undefined.**

The compliance assessment could not classify retention duration, access control, or tamper-evidence as compliant, because the audit didn't address them — not because they failed. *Impact if unaddressed:* this stays an open item indefinitely and will resurface in any future compliance review. *Phase 2.6 candidate:* Foundation — this is policy definition, not new engineering, and is comparatively low-cost to close.

**G5 — DID method coverage is narrow by design, not yet reconsidered.**

did:key was the correct, conservative starting choice. Phase 2.5 defined criteria for adding methods later but did not evaluate them against any real interoperability need. *Impact if unaddressed:* none currently — this is only a gap if an actual counterparty or ecosystem requires a different method. *Phase 2.6 candidate:* Conditional — only pursue if a concrete interoperability requirement exists; otherwise remains Future-Deferred.

**G6 — No trigger process for external resolution.**

Local resolution remains correct as a baseline, but there is no defined checkpoint or owner for revisiting that decision. *Impact if unaddressed:* the decision could be made informally or under time pressure later, without going through the criteria Phase 2.5 already defined. *Phase 2.6 candidate:* Light Foundation item — formalize the review trigger itself, not the resolver.

**G7 — ZKP extensibility unexercised.**

Nothing has been built against the interfaces Phase 2.5 confirmed as ZKP-ready. Extensibility confirmed on paper is not the same as extensibility proven under an actual integration attempt. *Impact if unaddressed:* the gap is invisible until someone actually tries to build selective disclosure against these interfaces — at which point any misjudgment surfaces late. *Phase 2.6 candidate:* Future-Deferred — explicitly out of scope per Phase 2.5 non-goals; do not pull forward without a separate, explicit scoping decision.

**G8 — Recovery-execution risk for field operations.**

This is flagged as a decision point, not a build item. Operation Signal Forge supports time-sensitive search-and-rescue detection; an identity holder locked out during an active operation has no recovery path today. Whether that risk is acceptable, or whether it justifies prioritizing G2 above other Phase 2.6 candidates, is a judgment call outside the scope of this analysis. *Phase 2.6 candidate:* Not a work item — an open question to resolve before scoping.

## Hard boundaries carried forward (not gaps — do not reopen)

- No ZKP or selective-disclosure implementation (G7 stays Future-Deferred unless separately re-scoped)
- No mandatory external DID resolver, universal resolver, or blockchain identity network
- No automated identity recovery, automatic credential reissuance, or automatic privilege restoration as a side effect of recovery
- No redesign of the credential lifecycle, Trust Registry, Authorization Matrix, Capability Layer, or Fusion logic

Any Phase 2.6 scope that touches these must be treated as a new, explicit decision — not an extension of a Phase 2.5 residual.

## Candidate Phase 2.6 scope (prioritized, non-binding)

| **Gap** | **Recommended classification** | **Rationale** |
| --- | --- | --- |
| G4 — Audit log governance | Foundation | Confirmed control gap; closes standing compliance open items before introducing a more invasive recovery workflow. |
| G2 — Recovery executor | Foundation | Confirmed operational gap; prioritize after audit governance establishes retention, access, integrity, and evidence controls. |
| G6 — External-resolution review trigger | Foundation (light) | Low-cost governance process; prevents informal future DID-resolution decisions. |
| G3 — Centralized audit sink | Hardening | Useful monitoring improvement without changing the event data already being logged. |
| G1 — Shared nonce backend | Hardening (conditional) | Only needed when multi-node identity deployment is actually planned. |
| G5 — Additional DID methods | Future-Deferred (conditional) | Only when a concrete interoperability requirement is identified. |
| G7 — ZKP interface exercise | Future-Deferred | Explicitly deferred; requires a separate scoping decision. |

## Open questions requiring a decision before Phase 2.6 is scoped

- Does G8 (recovery-execution risk during field operations) justify elevating G2 above all other candidates, or is the current manual/out-of-band fallback acceptable for now?
- Is there an actual counterparty or ecosystem requirement driving G5, or is did:key-only sufficient for the foreseeable operational scope?
- Who owns the review trigger proposed in G6 — is that a standing responsibility or a per-phase checkpoint?
- What retention duration and access-control model should close G4 — is there an existing organizational policy to align to, or does one need to be authored from scratch?

## Closing statement

This gap analysis is derived entirely from Phase 2.5's own residuals, non-goals, and compliance-assessment open items. It introduces no new invariants, does not reopen the architecture audit, and does not commit Phase 2.6 to any specific scope — it is intended to make the next scoping conversation informed rather than open-ended.

**Phase 2.6 Prioritization Decision — G4 Before G2**

Following independent review of the gap register and repository verification, G4 — Audit Log Governance should be prioritized before G2 — Recovery Executor. This does not reject G2; it establishes the governance and evidentiary controls that should surround subsequent recovery execution.

Rationale:

G4 is a confirmed present control gap: formal retention, audit-log access control, and tamper-evidence are largely absent.

G4 closes an explicit compliance open item identified after the Phase 2.5 audit.

G4 is comparatively contained and can be addressed without changing identity lifecycle semantics.

G2 is a confirmed operational gap, but it is a more invasive workflow spanning identity state, recovery evidence, authorization boundaries, and audit behavior.

Completing G4 first creates a stronger governance and audit foundation for implementing G2 safely.

G1 remains conditional on multi-node deployment; G3 and G6 remain secondary hardening/process items; G5 and G7 remain deferred by design.

Decision gate for Phase 2.6 scope:

Do not begin G2 implementation until G4 policy and control requirements are defined sufficiently to establish retention, access, integrity, and auditability for recovery-related identity events.
