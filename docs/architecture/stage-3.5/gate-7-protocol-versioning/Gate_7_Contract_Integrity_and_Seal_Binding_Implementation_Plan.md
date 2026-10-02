# **Gate 7 Targeted Implementation Plan — Contract Integrity and Seal Binding**

**Work Package:** G7-CI  
**Stage:** 3.5 — Protocol Versioning and Interoperability  
**Gate:** 7  
**Related ADR:** `ADR-G7-Contract-Integrity-and-Seal-Binding.md`  
**Status:** Implementation Draft

---

## **1\. Objective**

Implement the normative requirements established by `ADR-G7-Contract-Integrity-and-Seal-Binding.md`.

The implementation MUST establish that a published `ProtocolSemanticContract` has a verifiable binding between its semantic content and its stored seal, that conflicting contract content cannot replace an existing `(protocol_id, protocol_version)` identity, and that runtime consumers fail closed when contract integrity cannot be established.

This remediation is intentionally limited to **contract integrity and seal binding**.

It MUST NOT implement or redesign Gate 7 D-3 runtime semantic authority.

---

## **2\. Architectural Basis**

The implementation MUST preserve the following existing architectural boundaries:

* `(protocol_id, protocol_version)` remains the protocol semantic identity.  
* `ProtocolSemanticContract` remains the governed contract object.  
* `compute_seal()` remains authoritative for deriving the contract seal.  
* The `seal` field itself is excluded from the content used to derive the seal.  
* Frozen contract objects remain immutable after publication.  
* Existing five-field `IdentityTuple` behavior is unchanged.  
* Gate 6's `SchemeVerifier` boundary is unchanged.  
* Stage 3.4 verifier-visible public-input boundaries are unchanged.  
* C1, C2, C3, and C4 acceptance semantics are unchanged.  
* Existing protocol/scheme/policy admission semantics are unchanged except where required to enforce the explicit integrity requirements of this plan.

---

## **3\. Workstream A — Publication Seal Verification**

### **Objective**

Ensure that publication establishes a verified relationship between contract content and its seal.

### **Requirements**

1. `publish()` MUST independently recompute the contract seal using `compute_seal()`.  
2. If the publication interface accepts a caller-supplied seal, that value MUST be compared against the independently computed seal.  
3. A supplied seal that does not match the computed seal MUST be rejected.  
4. The caller-supplied seal MUST NOT be treated as authoritative without independent recomputation.  
5. Publication failure MUST fail closed.  
6. The existing content-derived seal mechanism MUST NOT be replaced with a different sealing mechanism as part of this work package.

### **Required adversarial cases**

* Valid contract \+ correct seal → accepted.  
* Valid contract \+ incorrect seal → rejected.  
* Modified contract \+ copied seal from a previously valid contract → rejected.  
* Modified contract \+ independently computed new seal under an already-bound identity → rejected according to Workstream B.

---

## **4\. Workstream B — Protocol Identity Immutability**

### **Objective**

Ensure that one protocol identity cannot be rebound to different contract content.

### **Requirements**

For a given:

`(protocol_id, protocol_version)`

the catalog MUST maintain exactly one contract binding.

1. First valid publication → accepted.  
2. Re-publication of identical contract content and seal → idempotent/no-op.  
3. Publication of different contract content under the same identity → rejected with `PROTOCOL_CONTRACT_IMMUTABLE`.  
4. A matching seal string MUST NOT be sufficient to establish contract equivalence.  
5. Contract equivalence MUST be established from the actual governed contract content and its validated seal relationship.  
6. Existing `frozen=True` object immutability MUST be preserved.

### **Required adversarial case**

Attempt to construct altered semantic content while reusing the original valid seal and publish it under the same `(protocol_id, protocol_version)`.

Expected result:

**FAIL CLOSED / `PROTOCOL_CONTRACT_IMMUTABLE`**

---

## **5\. Workstream C — Runtime Contract Integrity Verification**

### **Objective**

Ensure that runtime consumers do not trust a catalog contract without independently establishing its integrity.

### **Requirements**

Before a resolved catalog contract is trusted by its existing consumer:

1. Retrieve the contract.  
2. Recompute its seal using `compute_seal()`.  
3. Compare the recomputed seal against the stored seal.  
4. If the values differ, reject/fail closed.  
5. Only an integrity-valid contract may proceed to its existing consumer path.

Runtime integrity verification MUST NOT:

* redefine C1–C4;  
* change the acceptance conjunction;  
* implement D-3 semantic evaluation;  
* introduce scheme-specific logic;  
* alter the Gate 6 abstraction boundary;  
* alter Stage 3.4 public-input semantics.

---

## **6\. Workstream D — Regression and Boundary Preservation**

The remediation MUST preserve existing behavior outside the contract-integrity scope.

The following MUST remain unchanged:

### **Identity**

* Explicit five-field `IdentityTuple`.  
* No reintroduction of protocol or policy defaults.  
* Explicit protocol identity before registry admission.

### **Gate 6**

* `SchemeVerifier` remains the stable cryptographic substitution boundary.  
* Scheme adapters remain below the protocol semantic boundary.  
* No protocol/policy semantics are introduced into scheme-specific layers.

### **Stage 3.4**

* `Public means visible to the verifier`.  
* Verifier-visible public inputs remain unchanged.  
* Private witness remains outside the public-input boundary.  
* Data outside the proof boundary remains excluded from proof construction.

### **Acceptance**

The existing:

`C1 ∧ C2 ∧ C3 ∧ C4`

acceptance semantics MUST remain unchanged.

No contract-integrity change may weaken or bypass C1, C2, C3, or C4.

---

## **7\. Workstream E — Dedicated Contract Integrity Tests**

The implementation MUST add or update focused tests demonstrating the normative requirements.

### **Positive cases**

| Case | Expected |
| ----- | ----- |
| Valid contract with valid computed seal | PASS |
| Supplied seal equals recomputed seal | PASS |
| First publication of valid identity | PASS |
| Identical re-publication | Idempotent / PASS |
| Runtime resolution of intact contract | PASS |

### **Negative cases**

| Case | Expected |
| ----- | ----- |
| Supplied seal differs from computed seal | FAIL |
| Modified content \+ copied original seal | FAIL |
| Modified content \+ newly computed seal under existing identity | `PROTOCOL_CONTRACT_IMMUTABLE` |
| Tampered stored contract content | FAIL closed |
| Tampered stored seal | FAIL closed |

### **Regression cases**

Existing relevant tests MUST continue to pass for:

* Gate 7 interoperability/versioning.  
* Gate 6 substitution.  
* WP7 C/C4 wrapper.  
* Stage 3.5 ZK abstraction.  
* R1.1 targeted remediation.  
* Stage 3.4 visibility boundary.

---

## **8\. Implementation Constraints**

The implementation MUST:

* remain limited to this work package;  
* preserve the frozen Gate 7 candidate as historical evidence;  
* make no changes to the previously frozen failed candidate;  
* avoid unrelated refactoring;  
* avoid changing protocol semantic definitions;  
* avoid changing version-selection policy;  
* avoid introducing downgrade semantics;  
* avoid changing policy-version semantics;  
* avoid changing authorization semantics;  
* avoid changing cryptographic scheme behavior;  
* avoid reopening Gate 6 or Stage 3.4.

Any implementation discovery requiring a new architectural decision MUST stop implementation and return to architecture review rather than silently expanding scope.

---

## **9\. Verification Requirements**

### **Level 2 Verification**

The implementer MUST provide evidence that:

1. Workstreams A–E are implemented.  
2. All new contract-integrity positive and negative tests pass.  
3. Existing Gate 7 interoperability tests pass.  
4. Gate 6 substitution tests pass.  
5. Stage 3.4/C1–C4 regression tests pass.  
6. No unrelated tracked files are modified by test execution.  
7. The resulting tree is clean after verification.  
8. The implementation does not include D-3 semantic-authority changes.

Level 2 verification MUST occur against the implementation candidate before publication.

---

## **10\. Candidate Publication and Freeze**

After Level 2 PASS:

1. Publish the implementation commit.  
2. Record the exact candidate SHA.  
3. Freeze the candidate.  
4. Do not modify the frozen candidate during independent verification.

The frozen candidate becomes the sole subject of Level 3 verification.

---

## **11\. Level 3 Independent Verification**

An independent verifier MUST verify the frozen candidate against:

* `ADR-G7-Contract-Integrity-and-Seal-Binding.md`  
* this implementation plan  
* the original Gate 7 ADR  
* relevant Stage 3.4 and Gate 6 architectural constraints

The verifier MUST independently test:

* content/seal binding;  
* publication verification;  
* identity immutability;  
* runtime integrity verification;  
* fail-closed behavior;  
* regression boundaries.

The verifier MUST NOT modify the candidate.

Formal Gate 7 adjudication remains **OPEN** until Level 3 independently passes.

---

## **12\. Exit Criteria**

This work package is complete only when all of the following are demonstrated:

1. Every published contract has a seal independently derived from its governed content.  
2. Caller-supplied seals cannot establish integrity without recomputation.  
3. A copied seal cannot be used to publish altered contract content.  
4. A `(protocol_id, protocol_version)` identity cannot be rebound to different contract content.  
5. Identical re-publication remains idempotent.  
6. Runtime refuses to trust a contract whose stored seal does not match its content.  
7. Integrity failures fail closed.  
8. Gate 6 remains unchanged and substitution remains valid.  
9. Stage 3.4 visibility semantics remain unchanged.  
10. C1–C4 acceptance semantics remain unchanged.  
11. Dedicated integrity tests pass.  
12. Relevant regression suites pass.  
13. Level 2 verification passes.  
14. A new candidate SHA is published and frozen.  
15. Level 3 independently verifies the frozen candidate.

---

## **13\. Explicit Non-Goals**

The following are intentionally deferred:

* Gate 7 D-3 runtime semantic authority.  
* Protocol Catalog semantic execution.  
* Compatible/incompatible semantic-change enforcement beyond existing behavior.  
* Protocol-version downgrade policy.  
* Policy-version validation redesign.  
* Catalog persistence redesign.  
* Production cryptographic certification.  
* New ZK schemes.  
* Gate 6 architectural changes.  
* Stage 3.4 architectural changes.

These remain separate architectural or remediation items and MUST NOT be introduced through this implementation package.

---

## **14\. Traceability**

| ADR Requirement | Implementation Workstream |
| ----- | ----- |
| Content-derived seal | A |
| Publication verification | A |
| Identity immutability | B |
| Runtime integrity verification | C |
| Gate 6 / Stage 3.4 preservation | D |
| Dedicated integrity testing | E |
| Fail-closed behavior | A, B, C, E |
| D-3 remains separate | Constraints / Non-Goals |

**Implementation Package Status:** Ready for Review

