# ADR: Recovery Authority Model — Single Designated Authority Baseline

**Status:** Accepted

**Date:** 2026-08-17

**Project:** Operation Signal Forge

**Resolves:** Phase 2.7 Gap Analysis — Gap H5 (Recovery authority model)

**Related:** Phase 2.5 Identity Recovery Foundations (policy), Phase 2.6 G2 Identity Recovery Executor (implementation)

---

**Decision:** Use a single designated recovery authority as the baseline recovery model for Signal Forge. Multi-party approval is reserved for higher-risk deployments or future hardening.

---

## Context

Phase 2.5 established identity recovery policy — trigger conditions, an approver role, an audit shape, and key-lifecycle primitives — but deliberately left the recovery *authority model* open. Three options were on the table at a policy level: self-attested recovery, a single designated approver, or multi-party approval.

Phase 2.6 implemented the G2 Identity Recovery Executor. That implementation used a single `identity_recovery:approver` scope. This was the simplest option to build against the existing policy, but it was not accompanied by an explicit decision record — it was an implementation choice, not an architectural one.

The Phase 2.7 Gap Analysis (Gap H5) flagged this: the single-approver model may well be correct, but treating an unreviewed implementation default as a settled architectural position is itself a gap. For a recovery path — the mechanism by which control of an identity is re-established after compromise or loss — the authority model deserves an explicit, on-the-record decision rather than an inherited default.

## Problem

Should Signal Forge's identity recovery mechanism require approval from a single designated authority, or from multiple parties, in order to execute a recovery?

This decision matters because it defines where trust concentrates in the one identity workflow explicitly designed to restore access after something has already gone wrong. Getting it wrong in either direction has cost: too much friction (multi-party coordination) can make recovery unusable when it's needed most; too little (a single unreviewed approver) creates a concentrated trust point without anyone having deliberately accepted that tradeoff.

## Decision

**Single designated recovery authority is the baseline recovery model.**

Multi-party recovery approval is reserved for:

- higher-risk deployments,
- environments with stronger operational/security requirements, or
- a future hardening phase.

This decision formally accepts and ratifies the model Phase 2.6 already implemented (`identity_recovery:approver`). It does not change the recovery executor, the credential lifecycle, or any authorization behavior. It resolves the open architectural question the implementation left unanswered, so Phase 2.7 can proceed without H5 sitting open.

## Rationale

The primary reason for choosing a single designated recovery authority is **operational simplicity**. Signal Forge needs a recovery mechanism that is understandable, deployable, and operationally usable without immediately introducing the coordination and availability complexity of multi-party approval — quorum logistics, approver availability, tie-breaking, and the operational overhead of keeping multiple approvers current and reachable.

For the project's current operational maturity and deployment model, a single-authority baseline is the right complexity level: it is simple enough to reason about, test, and operate correctly, and it maps directly onto the policy Phase 2.5 already established without requiring new coordination infrastructure that nothing else in the system yet needs.

## Tradeoffs

**This decision explicitly acknowledges: a single designated recovery authority creates a concentrated trust point.** If that authority is compromised, coerced, or makes an error, there is no second party positioned to catch it before a recovery executes.

This is an accepted architectural tradeoff for the current baseline, not an oversight. It is explicitly **not** being treated as proof that single-approver recovery is universally sufficient, for all deployments, indefinitely. It is the appropriate baseline for where the project is now — operational simplicity is being deliberately prioritized over the additional assurance multi-party approval would provide, with that tradeoff on the record rather than implicit.

## Security Implications

This decision preserves every recovery security boundary already established in Phase 2.5 and Phase 2.6. None of the following change as a result of this ADR:

- Recovery authority can approve identity recovery.
- Recovery may retire compromised or unavailable identity verification material.
- Recovery may activate replacement identity keys.
- Recovery must remain auditable.
- Recovery must not automatically reissue credentials.
- Recovery must not automatically renew or revoke credentials.
- Recovery must not automatically restore Authorization Matrix scopes.
- Recovery must not bypass Trust Registry governance.

The single-authority model concentrates trust in whoever holds the `identity_recovery:approver` scope. That concentration is bounded by the isolation guarantees above — a compromised or misused approval can retire and replace a key, but it cannot, by itself, touch credential issuance, renewal, revocation, or Authorization Matrix scopes. The blast radius of a single-authority failure is limited to identity key control, not the full identity or authorization surface.

## Operational Implications

- Recovery can proceed with a single approver's action, which keeps the operational path short and dependency-light — relevant given Signal Forge's field-operations context, where recovery may need to happen without access to a distributed set of approvers.
- The project takes on the operational responsibility of protecting and provisioning the `identity_recovery:approver` scope carefully, since it is now a formally acknowledged concentrated trust point rather than an incidental one.
- No new infrastructure, coordination process, or quorum mechanism is introduced by this decision.

## Future Evolution / Reassessment Conditions

Multi-party recovery approval is documented here as a **future hardening option**, not a requirement for the current phase. This ADR does not design or implement that mechanism.

Higher-risk deployments may eventually require stronger recovery controls, such as multi-party approval. Conditions that should trigger a reassessment of this decision include (illustrative, not exhaustive):

- A deployment context with materially higher risk than Signal Forge's current operational profile.
- Evidence or a credible threat model indicating single-approver compromise is a realistic attack path worth defending against specifically.
- Regulatory, contractual, or partner requirements that mandate multi-party control over identity recovery.
- A deliberate decision to pursue recovery hardening as its own scoped phase.

Any of these should prompt a new ADR that supersedes this one — not a silent change to the recovery executor.

## Consequences

**Positive:**
- Resolves Phase 2.7 Gap H5; the recovery authority model is now an explicit, on-the-record architectural decision rather than an inherited implementation default.
- Keeps the recovery path operationally simple and consistent with Phase 2.5 policy and the Phase 2.6 implementation already in place.
- Establishes clear, named conditions under which the decision should be revisited, so future hardening isn't ad hoc.

**Negative / accepted risk:**
- A single point of trust exists in the recovery path. Compromise, coercion, or error at that single point is not caught by a second approver.
- This risk is deliberately accepted for the current baseline and documented rather than mitigated in this ADR.

**Explicitly out of scope for this ADR:**
- No redesign of the recovery executor.
- No change to the credential lifecycle.
- No introduction of multi-party recovery.
- No new authorization behavior.
- No expansion of Phase 2.7 scope beyond resolving this one architectural question.

This ADR exists solely to formally resolve H5 so the Phase 2.7 specification can proceed with the recovery authority model explicitly settled.
