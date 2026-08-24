# ADR: Risk-Based Verification Levels for Independent Verification (H1)

**Status:** Accepted

**Date:** 2026-08-19

**Project:** Operation Signal Forge

**Related:** Phase 2.7 — Identity Assurance & Governance Hardening (H1 Independent Verification control); Phase 2.8 Gap Analysis (independent-verification re-execution rigor)

**Lifecycle position:** This ADR defines assurance requirements *within* Step 4 — Tests & Validation of the Phase Engineering Lifecycle. It does not add, remove, or reorder any lifecycle step.

---

**Decision:** Isolated verifier-controlled execution is not mandatory for every phase. The required level of independent verification is instead determined by the risk and consequence of the phase's changes, using a three-tier model. Higher-risk changes require stronger verification.

---

## Context

Phase 2.7 established Independent Verification (H1) as a standing control within Step 4 — Tests & Validation of the Phase Engineering Lifecycle. The first H1 exercise (verification ID `cf9ed24a1a7cfd88`) created a persisted verification record and performed second-party repository/evidence spot-checking, but did not execute the regression suites inside an isolated, verifier-controlled CI environment. This limitation was disclosed in the record itself and carried forward as a known assurance gap rather than hidden or treated as resolved.

The Phase 2.8 Gap Analysis identified independent-verification re-execution rigor as the primary remaining assurance gap in the project, and raised an unresolved question: should isolated, verifier-controlled execution be mandatory for every future phase, or should it be triggered by a risk threshold?

The project wants to close this rigor gap where it matters without turning the Phase Engineering Lifecycle into unnecessary bureaucracy. A flat mandate — full isolated re-execution for every phase, regardless of what changed — would impose meaningful process cost on phases that don't need it (documentation updates, non-security config changes, low-impact refactors), while a flat non-mandate leaves exactly the gap Phase 2.7 disclosed unaddressed indefinitely.

## Problem

What level of independent verification rigor should be required for a given phase, and should that level be uniform across all phases or scaled to the risk of what the phase actually changes?

## Decision

**Isolated verifier-controlled execution is not mandatory for every phase.** Instead, the required level of independent verification is determined by the risk and consequence of the phase's changes, using a tiered model:

- **Level 1 — Evidence Review / Spot-Check**
- **Level 2 — Independent Test Re-Execution**
- **Level 3 — Isolated Verifier-Controlled Execution**

Higher-risk changes require stronger verification. The phase author (or the reviewer assigned under H1) selects the level at the start of Step 4 — Tests & Validation, based on the guidance below, and that selection — along with its justification — becomes part of the verification record.

This decision governs *what level of rigor H1 must meet*. It does not change what H1 is, where it sits in the lifecycle, or what the Architecture Audit does with its output.

## Verification Levels

### Level 1 — Evidence Review / Spot-Check

Appropriate for low-risk changes such as documentation-only changes, non-security configuration changes, or low-impact refactors where behavior is not materially altered.

At this level, a reviewer distinct from the implementer reviews the reported evidence and spot-checks the repository state against what's claimed, without re-executing suites. This is, functionally, what the first H1 exercise performed — appropriately so, if the change it covered was in fact low-risk. This ADR does not retroactively judge whether Phase 2.7's own risk level matched Level 1; see Out of Scope.

### Level 2 — Independent Test Re-Execution

Appropriate where the phase changes meaningful behavior but does not introduce especially high-risk security, identity, authorization, recovery, cryptographic, or compliance controls.

At this level, the reviewer independently re-runs the relevant regression suites (not necessarily in a fully isolated environment) rather than accepting the implementer's reported console output at face value. This directly closes the specific rigor gap Phase 2.7 disclosed.

### Level 3 — Isolated Verifier-Controlled Execution

Expected for high-consequence changes involving areas such as:

- identity/authentication,
- authorization/access control,
- credential lifecycle,
- identity recovery,
- cryptographic/security controls,
- audit/compliance infrastructure, or
- other changes where an incorrect PASS could materially compromise architectural or operational security.

This list is guidance, not an exhaustive enumeration. At this level, the reviewer executes the regression suites inside an environment they control end-to-end — separate from the implementer's environment, tooling, and configuration — so that a compromised or misconfigured implementation environment cannot itself produce a false PASS.

## Rationale

Verification requirements should scale with the security, architectural, and operational consequences of the changes being introduced. Mandatory isolated execution for every phase would impose unnecessary cost and complexity on low-risk changes, where the marginal assurance gained does not justify the process overhead. High-consequence phases justify stronger evidence because a false PASS on identity, authorization, credential, recovery, cryptographic, or audit infrastructure would have materially greater architectural or security impact than a false PASS on, say, a documentation update.

A risk-based model preserves the purpose of H1 — real, disclosed, second-party-or-stronger verification — while allowing the lifecycle to remain lightweight and practical for the majority of changes that don't carry that level of risk.

## Tradeoffs

**Benefits:**
- Stronger assurance is applied precisely where it matters most — high-risk phases get the rigor Phase 2.7's disclosed gap was missing.
- Verification effort is proportionate to actual risk rather than uniformly maximal or uniformly minimal.
- Lower process overhead for low-risk work preserves the lifecycle's practicality.
- The model scales as the project matures and as more phases accumulate, without requiring renegotiation of the lifecycle itself.

**Costs / risks:**
- Risk classification can itself be subjective — two reasonable reviewers could disagree on whether a given phase is Level 1, 2, or 3.
- Insufficiently conservative classification could result in under-verification, silently reintroducing the exact gap this ADR exists to close.
- The project therefore needs explicit escalation criteria for phases where risk is ambiguous, rather than leaving the judgment call entirely to case-by-case discretion.

## Escalation Rule

**When the appropriate verification level is ambiguous, select the stronger level.**

This is a deliberately conservative default: uncertainty about whether a phase is Level 1 or Level 2, or Level 2 or Level 3, resolves upward, not downward. This directly addresses the subjectivity risk noted above — the cost of over-verifying an ambiguous phase is process overhead; the cost of under-verifying one is a false PASS on something that mattered.

## Evidence and Audit Requirements

Each phase must record, as part of its H1 verification:

- the selected verification level (1, 2, or 3),
- the reason for selecting it,
- what evidence was independently reviewed or executed,
- any limitations, and
- the resulting verification disposition.

The Architecture Audit for that phase consumes this evidence as an input. It does not redefine the verification model itself — the Architecture Audit's role remains what it has always been: evaluating whether the phase matches its specification and preserved invariants, now informed by a verification record that states its own rigor level explicitly rather than leaving it implicit.

## Important Architectural Boundary

This decision:

- **does not** create a ninth Phase Engineering Lifecycle step,
- **does not** change the existing eight-step lifecycle,
- keeps Independent Verification inside **Step 4 — Tests & Validation**, exactly where Phase 2.7 placed it, and
- only defines the assurance level required within that step.

## Consequences

**Positive:**
- Closes the primary assurance gap the Phase 2.8 Gap Analysis identified, by giving future phases a concrete mechanism (Level 2 or 3) to close the rigor gap Phase 2.7 disclosed, scaled to where it actually matters.
- Gives reviewers and implementers a shared, explicit vocabulary for what "verified" means on a given phase, rather than an implicit, uniform assumption.
- Establishes a conservative default (the escalation rule) that prevents the tiering itself from becoming a way to systematically under-verify.

**Negative / accepted risk:**
- Risk classification introduces a judgment call into the process that a flat mandate would not have. This is accepted as a reasonable cost for avoiding unnecessary process overhead on low-risk work, and is bounded by the escalation rule.
- Level 1 and Level 2 phases remain, by design, less rigorously verified than Level 3 phases. This is the intended tradeoff, not an oversight.

## Future Reassessment Conditions

This model should be revisited if:

- Risk classification proves contentious or inconsistent in practice across multiple phases, suggesting the guidance needs sharper criteria.
- A Level 1 or Level 2 phase is later found to have concealed a consequence that, in hindsight, warranted Level 3 — indicating the classification guidance itself needs revision, not just the individual call.
- The project's operational risk profile changes materially (for example, a move toward higher-stakes deployments), which could justify raising the floor for one or more categories.
- The project matures to a point where isolated verifier-controlled execution becomes cheap enough that the cost/benefit tradeoff underlying this ADR no longer holds.

Any such reassessment should produce a new ADR that supersedes this one, not a silent change in practice.

## Out of Scope

This ADR does not:

- redesign the Phase Engineering Lifecycle,
- mandate a particular CI provider, infrastructure platform, reviewer organization, or tooling implementation,
- retroactively reopen Phase 2.6 or Phase 2.7 — the Phase 2.7 disclosure of the H1 re-execution rigor gap stands as recorded, and this ADR resolves how *future* phases handle that gap, not how Phase 2.7 is judged in hindsight,
- judge whether Phase 2.7's actual risk level warranted a different verification tier than what it received,
- or design the multi-party recovery, SIEM, external DID, or ZKP mechanisms referenced elsewhere as unrelated residuals.
