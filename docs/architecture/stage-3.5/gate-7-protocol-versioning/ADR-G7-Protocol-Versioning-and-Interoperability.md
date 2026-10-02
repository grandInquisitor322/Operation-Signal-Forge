# ADR-G7: Protocol Versioning and Interoperability

**Status:** Accepted (implemented; Gate 7 CLOSED / PASS)  
**Date:** 2026-09 (baseline implementation); reconstituted for repository custody 2026-10-02  
**Stage:** 3.5 — SF-3.5-PROTO  
**Supersedes:** None  
**Amended by:** ADR-G7-Contract-Integrity-and-Seal-Binding.md (G7-CI; seal/content binding only)

**Custody note:** An original standalone file under this name was not recovered from operator archives during C-1 hygiene. This document reconstitutes the governing Gate 7 requirements from committed formal adjudication text (Gate_7_Formal_Adjudication.md), Stage 3.5 closure records, and the implemented surfaces (protocol_catalog, C4 admission, identity tuple). It is the canonical PROTO ADR going forward. It does not reopen Gate 7.

---

## 1. Context

Stage 3.5 introduces a protocol identity and versioning layer so verification decisions are explicit about which protocol and version apply, independent of which scheme (cryptographic mechanism) is used.

Without this layer:

- Protocol or policy identity can be inferred or defaulted.
- Incompatible semantic changes can hide under the same version label.
- Scheme substitution (Gate 6) can be confused with protocol semantic change.
- Interoperability across verifiers becomes non-deterministic.

Gate 6 already isolates cryptographic mechanism behind SchemeVerifier. Gate 7 isolates protocol semantic identity and versioning.

---

## 2. Decision

Adopt an explicit protocol semantic contract model and a five-field identity tuple for all proof verification decisions.

### 2.1 Identity tuple (mandatory)

Every proof operation and verification decision MUST be qualified by:

    (protocol_id, protocol_version, scheme_id, scheme_version, policy_version)

All five fields MUST be explicit, carried through verification, and available for audit recording.

### 2.2 Protocol semantic contract

For each supported (protocol_id, protocol_version) there is exactly one ProtocolSemanticContract published in a ProtocolCatalog.

The contract binds opaque semantic surface labels (Stage 3.3 context semantics, Stage 3.4 visibility semantics, C1 through C4 profiles, acceptance conjunction) to that identity. Contract fields are labels/ids, not an execution engine for arbitrary semantics (see Non-goals / D-3).

### 2.3 Governing requirements (PROTO)

**PROTO-1 — Explicit identity tuple.** All five fields present; no silent omission.

**PROTO-2 — No inference.** No guessing, defaulting, heuristic reconstruction, or silent substitution of tuple elements.

**PROTO-2.1 — Metadata vs public input.** Protocol/policy governance metadata is not automatically a cryptographic public input solely because it appears on the identity tuple. policy_version MUST NOT be auto-inserted as a verifier-visible public input.

**PROTO-3 — Deterministic compatibility.** Identical inputs produce identical compatibility outcomes; no "latest", wildcards, or silent fallback.

**PROTO-4 — Supported and permitted.** Accept only when protocol, protocol version, scheme, scheme version, and contract are supported and policy permits.

**PROTO-5 — Semantic continuity.** Evolution preserves established contracts; incompatible meaning must not masquerade as a compatible version.

**PROTO-6 — Incompatible change requires new protocol_version.** New semantics require a new protocol version identity.

**PROTO-7 — Fail-closed.** Reject unsupported protocol/scheme versions and unauthorized compatibility/downgrade paths.

### 2.4 Admission (C4)

C4 evaluates whether the identity tuple is supported and permitted (catalog resolve/require, policy match as configured, registry operation validation). Failures are fail-closed.

### 2.5 Relationship to G7-CI

ADR-G7-Contract-Integrity-and-Seal-Binding supplements this ADR:

- Content-derived seals; publish() recomputes and verifies seals.
- (protocol_id, protocol_version) immutability is content-based.
- require() verifies integrity before trust.

G7-CI does not redefine PROTO-1 through PROTO-7 or implement D-3 semantic execution.

---

## 3. Boundary preservation

- **Gate 6:** SchemeVerifier / scheme substitution unchanged.
- **Stage 3.4:** Verifier-visible public-input boundary unchanged.
- **C1 and C2 and C3 and C4:** Acceptance conjunction unchanged.
- **Authorization:** Proof validity is not authorization; Matrix remains decision authority.

---

## 4. Consequences

**Positive**

- Explicit, auditable protocol identity on the verification path
- Clear separation of protocol versioning vs scheme agility
- Deterministic fail-closed admission behavior
- Foundation for multi-version coexistence without silent upgrade/downgrade

**Trade-offs / follow-ons**

- Callers must supply the full tuple (no convenience defaults on the trust path)
- Catalog is process-local unless persistence is designed later (D-5)
- Semantic execution of contract labels is deferred (D-3)
- Production cryptographic certification is out of scope

---

## 5. Non-goals

- D-3: runtime evaluation/execution of contract semantic strings
- Production zk-SNARK/STARK soundness or trusted setup
- Redesign of Authorization Matrix or credential lifecycle
- Mandatory multi-process catalog persistence
- Changing Gate 6 scheme adapter architecture

---

## 6. Implementation surfaces (informative)

- identity_runtime/zk_abstraction/protocol_catalog.py — ProtocolSemanticContract, ProtocolCatalog, seals (G7-CI)
- identity_runtime/zk_abstraction/c4_policy_wrapper.py — C4 admission; integrity fail-closed
- identity_runtime/tests/test_gate7_interoperability.py — PROTO / interoperability tests
- identity_runtime/tests/test_gate7_contract_integrity.py — G7-CI integrity tests

**Authoritative G7-CI implementation SHA:** feedab71ab2ab0689b76e2492b25fc7283aa2283

**Parent Gate 7 candidate:** adeef37508214fe1522f5941ac67539f1acd52a3

---

## 7. Evidence (closure)

- Gate 7 formal adjudication: Gate_7_Formal_Adjudication.md — CLOSED / PASS
- Stage 3.5 formal closure: Stage_3_5_Formal_Closure_Adjudication.md
- G7-CI L2 / L3: f39c9d4e2d9055d2 / 276d3506496b78e2
- Chain-of-Correction: Gate_7_Chain_of_Correction_Note.md

---

## 8. References

- ADR-G7-Contract-Integrity-and-Seal-Binding.md
- Gate_7_Contract_Integrity_and_Seal_Binding_Implementation_Plan.md
- docs/compliance/zkp-compliance-carry-forward.md
- Stage 3.4 visibility boundary decisions (public = verifier-visible)
- Gate 6 formal adjudication (SchemeVerifier boundary)