# Phase 2.7 — Gap Analysis

**Created by:** Claude  
**Model:** Sonnet 5  
**Time of record:** 2026-08-17  
**Predecessor:** Phase 2.6 — Audit Log Governance & Identity Recovery Foundations (Status: Closed, Architecture audit: PASS, Regression: 57/57)  
**Purpose:** Identify what remains open after Phase 2.6 so Phase 2.7 can be scoped deliberately. This is an analysis document, not an implementation plan or a commitment of work.

## Purpose & scope

Phase 2.6 closed two confirmed gaps from the post-2.5 analysis — G4 (audit log governance) and G2 (identity recovery executor) — with a PASS architecture audit, eleven preserved invariants, and a 57/57 regression result. It also closed carrying forward four residuals unchanged from before, and its own compliance impact assessment surfaced a further set of caveats specific to what G4/G2 actually delivered. This analysis treats both sources as raw material and asks, for each: **is this a candidate for Phase 2.7, or does it stay deferred?**

This document does not reopen Phase 2.6. The PASS disposition, the eleven invariants, and the 57/57 regression result are treated as settled and are not re-evaluated here. Gap IDs G1/G3/G5/G7 are carried forward unchanged from the post-2.5 analysis for traceability; new gaps surfaced by Phase 2.6 are numbered H1–H7.

## Inputs used

- Phase 2.6 milestone record (delivered artifacts, residuals, explicit non-goals, validation results)
- Phase 2.6 Architecture Audit — Final Verification (G4/G2 evidence, eleven-invariant checklist, cross-boundary checks)
- Phase 2.6 Compliance Impact Assessment (methodology caveat, access-observability open item, static-vs-dynamic verification distinction)

## Gap register

| **ID** | **Area** | **Gap** | **Source** |
| --- | --- | --- | --- |
| G1 | Nonce store | File-backed store remains single-host; no shared backend for multi-node deployment | Carried forward, unchanged since Phase 2.5 |
| G3 | Audit visibility | No centralized aggregation/alerting (SIEM); audit review remains manual/local | Carried forward, unchanged since Phase 2.5 |
| G5 | DID method coverage | Still did:key only; future-expansion criteria still unevaluated against any real need | Carried forward, unchanged since Phase 2.5 |
| G7 | ZKP / selective disclosure | Interfaces still unexercised; remains explicitly deferred | Carried forward, unchanged since Phase 2.5 |
| H1 | Verification independence | All Phase 2.6 evidence is implementation-pass reported; no independent party re-executed tests or reviewed evidence separately from the implementer | Phase 2.6 audit methodology note; compliance assessment constraint |
| H2 | Meta-audit | Privileged (admin-scope) access to the audit log is not confirmed to be itself logged/auditable | Compliance assessment — open item |
| H3 | Verification depth | Credential/authorization isolation was confirmed via static inspection (no imports, no API calls found) rather than adversarial/dynamic testing that actually attempts a boundary violation | Compliance assessment — flagged distinction |
| H4 | Tamper detection response | verify_chain can detect a broken integrity chain, but with G3 (SIEM) still deferred, nothing currently alerts anyone when it does — detection is manual-only | Derived from G3 residual + G4 tamper-evidence design |
| H5 | Recovery authority model | Implementation uses a single identity_recovery:approver scope; Phase 2.5 policy left open whether recovery authority should be self-attested, single-designated, or multi-party, and that choice was never explicitly revisited at implementation time | Derived from G2 implementation vs. Phase 2.5 policy scope |
| H6 | Recovery notification | No holder-facing notification exists when a recovery event occurs on their identity | Not previously addressed in any phase; surfaced by G2 now being executable |
| H7 | Retention governance | Retention durations are configurable via environment overrides with per-event defaults; no documented policy or approval authority governs what those defaults should be or who can change them | Derived from G4 retention implementation |

## Gap detail

**G1 — Nonce store scalability.**

Unchanged since the Phase 2.6 gap analysis: correct and durable for a single host, no shared backend. *Phase 2.7 candidate:* Hardening, only if multi-node deployment becomes concrete.

**G3 — No centralized audit visibility.**

Unchanged: audit events are governed and tamper-evident but not aggregated or alerted on. *Phase 2.7 candidate:* Hardening, optional — see also H4, which is a narrower, more urgent slice of this same gap.

**G5 — DID method coverage.**

Unchanged: did:key only, future-expansion criteria still sitting unused. *Phase 2.7 candidate:* Future-Deferred, conditional on an actual interoperability requirement appearing.

**G7 — ZKP readiness.**

Unchanged: deferred, interfaces unexercised. *Phase 2.7 candidate:* Future-Deferred, requires a separate explicit scoping decision to touch at all.

**H1 — No independent verification of audit evidence.**

Every PASS in the Phase 2.6 audit — the eleven invariants, the 57/57 regression, the G4/G2 gates — rests on evidence reported by the same party that built the implementation. This isn't a claim that anything is wrong; it's that nothing has been independently checked. For a phase whose entire purpose was governance and control strengthening, this is a notable gap: the strengthened controls have not themselves been verified by anyone other than their builder. *Impact if unaddressed:* the project's confidence in its own PASS verdicts rests entirely on self-report, indefinitely. *Phase 2.7 candidate:* Foundation — establish a lightweight independent-review step (a second party, human or otherwise, re-running the regression suite and spot-checking cited evidence) before future PASS dispositions are accepted at face value.

**H2 — Admin-scope audit access isn't confirmed to be self-auditing.**

G4 built read/admin scopes for audit-log access, but the audit evidence doesn't confirm that using the admin scope itself generates an audit record. If privileged access to the audit trail isn't itself tracked, someone with identity_audit:admin could read or purge audit data without leaving a trace of having done so. *Impact if unaddressed:* a single-point trust gap in an otherwise governed system. *Phase 2.7 candidate:* Hardening — confirm or add logging of privileged audit-log access specifically.

**H3 — Isolation was verified structurally, not behaviorally.**

The claim "recovery doesn't touch credential lifecycle APIs" was confirmed by inspecting the module surface (no imports, no calls found) rather than by a test that deliberately tries to make recovery invoke a credential API and confirms it's rejected. Static absence-of-evidence is weaker than a tested boundary. *Impact if unaddressed:* a future refactor could accidentally introduce a coupling that static inspection wouldn't have caught if it isn't re-run, and no regression test would catch it either. *Phase 2.7 candidate:* Hardening — add adversarial/negative tests that actively attempt the prohibited calls and assert rejection, rather than relying on their current absence.

**H4 — Tamper detection has no response path.**

verify_chain exists and is tested, but nothing currently runs it proactively or alerts anyone on failure. Detecting a tampered audit chain today requires someone to manually invoke verification. *Impact if unaddressed:* the tamper-evidence mechanism is real but passive — it can prove tampering occurred after the fact, but won't surface that fact on its own. *Phase 2.7 candidate:* Light Hardening — a scheduled or triggered verification check with a minimal alert path, well short of full G3 SIEM scope.

**H5 — Recovery authority model was narrowed without an explicit decision.**

Phase 2.5's recovery policy deliberately left the authority model open (self-attested, single-designated approver, or multi-party). Phase 2.6 implemented a single-approver scope. That may be the right choice, but it doesn't appear to have been revisited as a decision at implementation time — it reads as the simplest option rather than a deliberate one. *Impact if unaddressed:* for a security-recovery path, an un-reviewed single point of approval authority is exactly the kind of choice that deserves an explicit sign-off. *Phase 2.7 candidate:* Not a build item — a decision to confirm or revise before treating the current model as settled.

**H6 — No holder notification on recovery.**

When a recovery event completes today, there's no mechanism notifying the affected holder through an independent channel. This matters most as a fraud-detection signal: if someone else triggers a recovery on a holder's identity, the legitimate holder currently has no way to find out except by noticing their own access changed. *Impact if unaddressed:* reduces the chance of catching an abused recovery approval quickly. *Phase 2.7 candidate:* Conditional — depends on whether an out-of-band notification channel is even available in the current deployment; flagged as a decision point, not an assumed build item.

**H7 — Retention durations lack a documented governance owner.**

The retention mechanism (per-event defaults, environment-variable overrides) is real and functional, but nothing says who is authorized to change those defaults or on what basis. *Impact if unaddressed:* retention could silently drift over time via configuration changes with no policy trail. *Phase 2.7 candidate:* Foundation (light) — document the retention policy and its approval authority; no code change implied.

## Hard boundaries carried forward (not gaps — do not reopen)

- No ZKP or selective-disclosure implementation (G7 stays Future-Deferred unless separately re-scoped)
- No mandatory external DID resolver, universal resolver, or blockchain identity network
- No automated identity recovery, automatic credential reissuance, or automatic privilege restoration as a side effect of recovery
- No redesign of the credential lifecycle, Trust Registry, Authorization Matrix, Capability Layer, or Fusion logic
- No change to the eleven invariants preserved through Phase 2.6

Any Phase 2.7 scope that touches these must be treated as a new, explicit decision — not an extension of a residual or a compliance open item.

## Candidate Phase 2.7 scope (prioritized, non-binding)

| **Gap** | **Recommended classification** | **Rationale** |
| --- | --- | --- |
| H1 — Independent verification step | Foundation | Addresses a standing self-report gap across every prior PASS, not just Phase 2.6's |
| H7 — Retention governance documentation | Foundation (light) | Policy-only, low cost, closes a clean accountability gap |
| H2 — Admin-scope self-auditing | Hardening | Closes a specific, narrow trust gap in an otherwise governed system |
| H3 — Adversarial isolation tests | Hardening | Converts a structural claim into a tested one; moderate cost |
| H4 — Minimal tamper-alert path | Hardening (light) | Narrower and cheaper than full G3; addresses the most time-sensitive part of that residual |
| G3 — Centralized SIEM | Hardening | Broader version of H4; remains optional |
| G1 — Shared nonce backend | Hardening | Only urgent if multi-node deployment is planned |
| H5 — Recovery authority model review | Decision, not a work item | Must be resolved before being treated as settled |
| H6 — Holder recovery notification | Conditional / decision | Depends on available out-of-band channel |
| G5 — Additional DID methods | Future-Deferred (conditional) | Only if a real interoperability need is identified |
| G7 — ZKP interface exercise | Future-Deferred | Explicitly out of scope per prior non-goals |

## Open questions requiring a decision before Phase 2.7 is scoped

- Should H1 (independent verification) become a standing process for all future phases, not just a one-time Phase 2.7 item — and who performs it?
- Does H5's single-approver recovery model reflect a deliberate choice, or should multi-party approval be considered given how sensitive the recovery path is?
- Should recovery trigger holder notification (H6), and if so, through what channel that the real holder — not an attacker who triggered the recovery — would actually receive?
- Is manual-only tamper detection (H4) acceptable for the current operational risk profile, or does it need to move ahead of the broader G3 SIEM item?

## Closing statement

This gap analysis is derived entirely from Phase 2.6's own audit evidence, its compliance assessment's flagged caveats, and residuals carried forward unchanged from Phase 2.5. It introduces no new invariants, does not reopen the architecture audit, and does not commit Phase 2.7 to any specific scope — it is intended to make the next scoping conversation informed rather than open-ended.
