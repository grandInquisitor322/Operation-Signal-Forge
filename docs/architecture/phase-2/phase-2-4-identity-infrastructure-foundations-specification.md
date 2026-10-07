# Phase 2.4 — Identity Infrastructure Foundations Specification

**Operation Signal Forge**  
**Phase:** 2.4  
**Status:** Architecture Specification  
**Predecessor:** Phase 2.3 — Trust Registry Governance  
**Purpose:** Establish the foundational identity infrastructure required for future decentralized identity and privacy-preserving authorization without disrupting the existing credential lifecycle.

## 1. Purpose

Phase 2.4 expands the Identity & Authorization Layer with the minimum infrastructure required to represent, manage, authenticate, and resolve decentralized identities.

The phase is intentionally **foundation-only**.

It establishes:

- A local DID document model.
- Holder key rotation.
- Subject binding and proof-of-possession at credential presentation.
- A distinction between persons, organizations, and roles.
- A local/in-repository DID resolution mechanism.

These capabilities provide the foundation for future interoperability, selective disclosure, and Zero-Knowledge Proof integration.

Phase 2.4 does **not** implement ZKP functionality.

## 2. Architectural Rule — Credential Lifecycle Must Remain Unchanged

**Phase 2.4 must not redefine the existing credential lifecycle.**

This is a mandatory architectural boundary.

The existing credential lifecycle has already been established through:

Issue

  ↓

Present

  ↓

Verify

  ↓

Renew

  ↓

Rotate

  ↓

Revoke

Phase 2.4 introduces **identity and key lifecycle capabilities alongside the credential lifecycle**.

It must not replace, merge, or redefine those mechanisms.

**Credential lifecycle **

Credential

├── issuance

├── expiration

├── renewal

├── rotation

└── revocation

**Identity lifecycle**

Identity

├── DID establishment

├── key management

├── key rotation

├── authentication

├── proof-of-possession

└── resolution

** **

These are related but distinct lifecycles.

A holder key rotation must not automatically be treated as credential rotation.

Likewise, credential rotation must not silently modify the holder's DID lifecycle.

## 3. Architectural Context

Phase 2.4 builds on the completed identity architecture:

Phase 2.1

Credential Revocation

        ↓

Phase 2.2

Credential Renewal & Rotation

        ↓

Phase 2.3

Trust Registry Governance

        ↓

Phase 2.4

Identity Infrastructure Foundations

The broader architecture remains:

Trust Registry

      ↓

Credential

      ↓

Credential Lifecycle

      ↓

Identity / Holder Binding

      ↓

Authorization Matrix

      ↓

Authorization Context

      ↓

Capability Layer

Phase 2.4 must preserve all existing boundaries.

## 4. Scope

Phase 2.4 contains five primary capabilities:

### 4.1 DID Document Model

Provide a local representation of DID documents including:

- DID identifier
- verification methods
- public keys
- authentication relationships
- key identifiers
- applicable verification relationships
- document metadata required by the implementation

The initial implementation should remain local.

### 4.2 Holder Key Rotation

Introduce identity-key rotation independently from credential rotation.

The system must be able to:

- identify the active holder verification key,
- add or replace an authorized key,
- retire an old key,
- preserve identity continuity,
- prevent an old compromised key from being treated as active.

Key rotation must not invalidate or rewrite credential lifecycle state by itself.

### 4.3 Subject Binding

Credential presentations must be capable of establishing that:

**The presenter controls the identity associated with the credential subject.**

This requires proof-of-possession of the appropriate subject key.

Conceptually:

Credential

    +

Presenter

    ↓

Proof of Subject-Key Control

    ↓

Verified Subject Binding

A valid credential alone must not automatically establish control of the subject identity where subject binding is required.

### 4.4 Person / Organization / Role Data Model

The identity model must distinguish between:

Person

Organization

Role

These concepts must not be collapsed into a single identity type.

Example:

Organization

     ↓

Person

     ↓

Role

     ↓

Credential

     ↓

Authorization

The initial implementation is a **data-model concern**, not an HR or organizational-management system.

Phase 2.4 does not implement:

- employee management,
- organizational workflows,
- personnel databases,
- organizational hierarchy management,
- or automated employment decisions.

### 4.5 Local DID Resolution

Provide a resolver abstraction capable of resolving known DIDs from local/in-repository sources.

Initial resolution should use:

- local files,
- repository-managed DID documents,
- or another deterministic local mechanism.

External network resolution is **not required**.

The architecture should nevertheless preserve a resolver abstraction so that future external resolution mechanisms can be introduced without rewriting the Identity Runtime.

## 5. DID Document Requirements

The DID document model should support the minimum structures required for Phase 2.4.

At minimum, the model should represent:

DID

 ├── verificationMethod[]

 └── authentication[]

Each verification method should have an identifiable key relationship.

The implementation should make the relationship explicit rather than treating a public key as an unstructured string.

The model should also support future extension without requiring a redesign when additional verification relationships are introduced.

## 6. Verification Relationships

Phase 2.4 must distinguish between:

**A key existing on a DID document**

and

**A key being authorized for a particular verification purpose.**

For example:

verificationMethod

        ↓

authentication

A key listed in the DID document should not automatically be assumed to be valid for every identity operation.

This distinction is important for future separation of:

- authentication,
- assertion,
- key agreement,
- and other verification relationships.

Only relationships explicitly supported by the implementation should be accepted.

## 7. Holder Key Rotation

Holder key rotation must preserve the underlying DID identity.

Conceptually:

DID

 │

 ├── Key A

 │

 └── Key B

After rotation:

DID

 │

 └── Key B

The DID remains the same.

The key changes.

This distinction is mandatory.

### Key rotation must provide

- continuity of the DID,
- identification of the active key,
- retirement of the previous key,
- protection against continued use of a retired key,
- auditable state transition where appropriate.

### Key rotation must not

- create a new credential automatically,
- revoke every credential automatically,
- modify Trust Registry state,
- modify Authorization Matrix policy,
- or grant additional authority.

## 8. Subject Binding and Proof-of-Possession

Subject binding establishes a relationship between:

Credential Subject DID

        +

Presentation

        +

Subject Key

The verifier should be able to determine whether the presenter controls the key associated with the credential subject.

The proof should be:

- bound to the presentation,
- resistant to replay,
- associated with the intended verification context,
- and verifiable using the subject's active verification material.

The exact cryptographic mechanism should remain compatible with the existing identity runtime and should not require ZKP.

## 9. Replay Resistance

Subject-binding proofs must not be reusable indefinitely.

The presentation architecture should support an appropriate challenge mechanism, such as:

- nonce,
- verifier challenge,
- presentation-specific context,
- or equivalent replay-resistant mechanism.

The exact implementation should be selected during implementation planning.

The requirement is:

A captured valid presentation must not automatically become a reusable authorization artifact.

## 10. Identity Types

The data model should distinguish:

### Person

An individual identity.

### Organization

An institutional identity capable of issuing or holding organizational authority.

### Role

A relationship or function associated with an identity.

A role should not automatically become an independent person or organization.

For example:

Person: Alice

Organization: Humanitarian Organization A

Role: Humanitarian Analyst

The credential and authorization architecture may then establish:

Alice

  ↓

member of Organization A

  ↓

holds HumanitarianAnalyst role

  ↓

authorized capabilities

The exact organizational semantics remain subject to future specification.

## 11. DID Resolution

Phase 2.4 should introduce a resolver abstraction:

resolve(did)

    ↓

DID Document

The first implementation should resolve from local/in-repository sources.

This provides deterministic development and testing without introducing external network dependencies.

### Explicit non-goal

Phase 2.4 does **not** require:

- blockchain-based DID resolution,
- external DID networks,
- universal DID discovery,
- network consensus,
- or mandatory Internet connectivity.

## 12. Resolver Boundary

The Identity Runtime should interact with a resolver abstraction rather than directly depending on the physical storage mechanism.

Conceptually:

Identity Runtime

       ↓

   DID Resolver

       ↓

Local Resolver

       ↓

Repository / File

Future implementations could then introduce:

External Resolver

Blockchain Resolver

Network Resolver

without changing the higher-level identity architecture.

## 13. Trust Registry Boundary

The Trust Registry remains responsible for issuer trust.

It answers:

**Is this issuer trusted to issue this credential type?**

Phase 2.4 must not move that responsibility into DID resolution.

A valid DID does not automatically mean:

trusted issuer.

Therefore:

DID Resolution

      ≠

Issuer Trust

DID resolution establishes identity information.

Trust Registry governance establishes issuer trust.

## 14. Authorization Boundary

Phase 2.4 must not redefine the Authorization Matrix.

The Authorization Matrix remains responsible for determining what authority a credential or identity context provides.

Therefore:

DID

 ↓

Identity

 ↓

Credential

 ↓

Authorization Matrix

 ↓

Capability Access

A DID alone must not grant operational capability access.

## 15. Capability Layer Boundary

The Capability Layer remains an application decision-support and workflow layer.

Phase 2.4 must not move identity implementation into capabilities.

Capabilities should continue receiving an appropriate authorization context rather than directly implementing:

- DID resolution,
- key rotation,
- credential verification,
- subject binding,
- Trust Registry governance,
- or identity recovery.

## 16. ZKP Boundary

Zero-Knowledge Proof functionality is explicitly **out of scope** for Phase 2.4.

The architecture should, however, avoid preventing future ZKP integration.

Phase 2.4 should establish the foundations required for future:

Credential

     ↓

Presentation

     ↓

Selective Disclosure

     ↓

ZKP

     ↓

Authorization

The implementation should not introduce a premature ZKP dependency.

## 17. Security Requirements

Phase 2.4 must preserve:

- least privilege,
- proof-of-possession,
- replay resistance,
- key lifecycle separation,
- explicit verification relationships,
- issuer trust separation,
- authorization separation,
- and auditability where identity state changes.

A key compromise must not silently create additional authorization.

A DID document must not be treated as an authorization policy.

A credential must not be treated as proof of current holder-key control unless the required subject-binding verification succeeds.

## 18. Privacy Requirements

The identity layer should follow:

**Minimum necessary disclosure.**

Phase 2.4 should avoid exposing unnecessary identity information during presentation.

However, full selective-disclosure and ZKP mechanisms are deferred.

The architecture should therefore prepare for privacy-preserving presentation without prematurely implementing the cryptographic privacy layer.

## 19. Operational Data Boundary

Phase 2.4 must not introduce sensor data into the Identity Layer.

The following remain outside identity infrastructure:

- raw sensor observations,
- fused sensor scores,
- detection evidence,
- operational locations,
- sensor tasking,
- Fusion Engine state,
- Capability Layer workflow state.

Identity infrastructure provides **identity and authorization context**, not operational data storage.

## 20. Persistence Requirements

Phase 2.4 may initially use local deterministic persistence consistent with the existing development architecture.

Production-grade distributed identity persistence is outside this phase.

The implementation should avoid creating unnecessary coupling between:

- DID storage,
- credential storage,
- Trust Registry storage,
- operational detection storage.

These remain separate concerns.

## 21. Testing Requirements

Phase 2.4 should include tests covering at minimum:

### DID Model

- DID document creation
- verification method representation
- authentication relationship
- invalid DID document rejection

### Resolution

- known DID resolution
- unknown DID rejection
- malformed DID document handling
- deterministic local resolution

### Key Rotation

- successful holder key rotation
- old key retirement
- new key activation
- DID continuity
- retired key rejection
- compromise scenario

### Subject Binding

- valid proof-of-possession
- invalid proof-of-possession
- wrong subject key
- wrong DID
- replay attempt
- missing proof
- retired key

### Identity Types

- person representation
- organization representation
- role representation
- valid relationships
- invalid type combinations

### Regression

All existing Phase 2.1–2.3 tests should remain passing.

## 22. Regression Requirement

Phase 2.4 must not regress:

- credential revocation,
- credential renewal,
- credential rotation,
- Trust Registry governance,
- issuer authorization,
- administrator authorization,
- or existing DApp authentication flows.

The existing identity architecture is considered a stable foundation.

New functionality must be additive unless explicitly approved by a later architecture decision.

## 23. Explicit Non-Goals

Phase 2.4 does **not** implement:

- Zero-Knowledge Proofs
- blockchain identity
- external DID networks
- mandatory external DID resolution
- decentralized consensus
- organizational HR workflows
- full identity recovery infrastructure
- credential lifecycle redesign
- Trust Registry redesign
- Authorization Matrix redesign
- Capability Layer redesign
- Fusion Engine changes
- sensor data migration

## 24. Architectural Invariants

The following invariants must remain true after Phase 2.4.

### Invariant 1

**DID identity does not equal authorization.**

### Invariant 2

**DID resolution does not equal issuer trust.**

### Invariant 3

**Holder key rotation does not equal credential rotation.**

### Invariant 4

**Credential rotation does not equal holder identity rotation.**

### Invariant 5

**Trust Registry governance does not equal holder authorization.**

### Invariant 6

**Identity infrastructure does not become operational infrastructure.**

### Invariant 7

**Phase 2.4 must not redefine the existing credential lifecycle.**

## 25. Target Architecture

At completion, the architecture should resemble:

                 ┌──────────────────────┐

                 │    Trust Registry    │

                 │  Issuer Governance   │

                 └──────────┬───────────┘

                            │

                            ▼

┌──────────────┐     ┌──────────────┐

│ DID Resolver  │────▶│ Identity     │

│ Local / Repo │     │ Runtime      │

└──────────────┘     └──────┬───────┘

                            │

                    ┌───────┴────────┐

                    │                │

                    ▼                ▼

              Holder Identity   Credential

              + Key State       Lifecycle

                    │                │

                    └───────┬────────┘

                            ▼

                     Subject Binding

                     / Proof of Possession

                            │

                            ▼

                    Authorization Matrix

                            │

                            ▼

                   Authorization Context

                            │

                            ▼

                    Capability Layer

## 26. Future ZKP Architecture

Phase 2.4 should leave room for a future architecture such as:

DID

 ↓

Credential

 ↓

Presentation

 ↓

Selective Disclosure

 ↓

Zero-Knowledge Proof

 ↓

Verified Claims

 ↓

Authorization Matrix

 ↓

Capability Access

But **no ZKP implementation belongs in Phase 2.4.**

## 27. Success Criteria

Phase 2.4 is complete when:

- DID documents have a defined local model.
- Verification methods are represented explicitly.
- Authentication relationships are represented explicitly.
- Holder keys can be rotated independently of credentials.
- Retired holder keys cannot authenticate as active keys.
- DID identity remains continuous through key rotation.
- Credential presentations can establish subject-key possession.
- Subject-binding proofs resist replay.
- Person, organization, and role are distinct identity concepts.
- Known DIDs can be resolved locally.
- Unknown or malformed DIDs fail safely.
- Trust Registry responsibilities remain unchanged.
- Authorization Matrix responsibilities remain unchanged.
- Capability Layer responsibilities remain unchanged.
- Credential lifecycle remains unchanged.
- All Phase 2.1–2.3 regression tests remain passing.
- No ZKP or external network dependency is introduced.

## 28. Engineering Principle

The purpose of Phase 2.4 is not to make Signal Forge maximally decentralized.

It is to establish a **clean identity infrastructure foundation** that can eventually support decentralized identity and privacy-preserving authorization without forcing premature architectural commitments.

The guiding principle is:

**Foundation first. Privacy-preserving cryptography second.**

And the most important implementation constraint remains:

**Phase 2.4 must not redefine the existing credential lifecycle.**

## Phase 2.4 Definition

**Phase 2.4 — Identity Infrastructure Foundations**

**Scope:**

- Local DID document model
- Holder key rotation
- Subject binding / proof-of-possession
- Person / organization / role data model
- Local DID resolution

**Explicitly deferred:**

**ZKP, external DID networks, blockchain infrastructure, and credential lifecycle redesign.**
