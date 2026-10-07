# Phase 2.5 — Identity Operational Hardening & Interoperability Foundations

**Operation Signal Forge**  
**Status:** Proposed Architecture Specification  
**Predecessor:** Phase 2.4 — Identity Infrastructure Foundations  
**Purpose:** Harden identity infrastructure and establish interoperability foundations before future ZKP/selective-disclosure work.

## 1. Production-grade challenge/nonce handling

- Move beyond the current process-local nonce model.
- Define expiration, uniqueness, replay protection, and lifecycle.
- Keep presentation semantics unchanged.

## 2. DID method policy & interoperability

- Explicitly define what DID methods Signal Forge supports.
- Establish validation and resolution boundaries.
- Keep local resolution as the current baseline.
- Avoid prematurely committing to an external DID network.

## 3. Identity recovery foundations

- Define what happens when a holder loses or compromises identity keys.
- Separate **identity recovery** from credential renewal/revocation.
- Establish recovery authority and audit requirements without building a full recovery service yet.

## 4. Presentation-proof logging & retention

- Define what proof events are logged.
- Minimize sensitive identity material in logs.
- Establish retention and audit requirements.
- Preserve the operational-data boundary.

## 5. ZKP / selective-disclosure readiness

- **Do not implement ZKP yet.**
- Identify the interfaces and data boundaries future selective-disclosure mechanisms will require.
- Make sure Phase 2.5 doesn't create architectural debt that blocks them later.

And the architectural rule carries forward:

**Phase 2.5 must not redefine the existing credential lifecycle.**

**Note:** classify each item as **Foundation, Hardening, or Future/Deferred**
