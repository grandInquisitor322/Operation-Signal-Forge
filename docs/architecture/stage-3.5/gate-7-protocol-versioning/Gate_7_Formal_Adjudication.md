\# Operation Signal Forge — Formal Adjudication Record

\## Stage 3.5 Gate 7: Protocol Versioning and Interoperability

\### Remediation: G7-CI — Contract Integrity and Seal Binding



\---



> \[!IMPORTANT]

> \*\*FINAL ADJUDICATION LAYER — READ ONLY\*\*

> This record is the output of a formal adjudication exercise, not an engineering cycle.

> Nothing in this repository was modified during adjudication.



\---



\## Formal Adjudication



\*\*Decision:\*\* GATE 7 — CLOSED / PASS



\---



\## 1. Candidate Integrity



\### Stated Frozen Candidate

The adjudication prompt identifies the frozen Gate 7 remediation candidate as:



```

5f7523bf3865dce519ccd87a82fe897f665bd123

```



\### Repository Finding — SHA Does Not Exist

\*\*Observed fact:\*\* Running `git cat-file -t 5f7523bf3865dce519ccd87a82fe897f665bd123` against the repository at `c:\\Users\\Samson\\signal-forge` returns:



```

fatal: bad object 5f7523bf3865dce519ccd87a82fe897f665bd123

```



The SHA `5f7523bf3865dce519ccd87a82fe897f665bd123` does not exist as a Git object in the repository.



\### Authoritative Candidate Resolution

This SHA discrepancy is adjudicated as follows:



The L2 verification record (`f39c9d4e2d9055d2`) and the L3 verification record (`276d3506496b78e2`) both record the \*\*actual frozen implementation SHA\*\* in their `frozen\_implementation\_sha` / `execution\_context` fields as:



```

feedab71ab2ab0689b76e2492b25fc7283aa2283

```



The L3 record explicitly states:



> `"frozen\_implementation\_sha": "feedab71ab2ab0689b76e2492b25fc7283aa2283"`



The commit `feedab71` exists in the repository and is the top of the G7-CI implementation commit chain:



```

feedab71  fix(gate7): seal recompute and runtime integrity (G7-CI body)

3039f9ee  fix(gate7): seal recompute and runtime integrity (G7-CI body)

dcf70916  fix(gate7): enforce contract content/seal binding (G7-CI)

d181ed6b  docs(compliance): register first-party ZKP stack in third-party license register

da27e04b  docs(compliance): ZKP carry-forward aligned to Gate 7 candidate

adeef375  feat(zk): Stage 3.5 Gate 7 protocol versioning and interoperability  ← parent Gate 7 candidate

```



The parent Gate 7 candidate `adeef37508214fe1522f5941ac67539f1acd52a3` exists in the repository and is confirmed as the pre-G7-CI base.



The HEAD of the repository at adjudication time is:

```

6bd2189ed1fcece568ac7d56b10e3fffa33878dc

```

which is the L3 documentation commit added after `feedab71`.



\*\*Adjudicator determination:\*\* The SHA `5f7523bf3865dce519ccd87a82fe897f665bd123` does not exist and cannot be independently verified against repository objects. However, both the L2 and L3 verification records, which are frozen and recorded in the repository at `dapp\_api/independent\_verification.jsonl`, consistently identify `feedab71ab2ab0689b76e2492b25fc7283aa2283` as the actual frozen implementation candidate. The working-tree files for all three G7-CI source files (`protocol\_catalog.py`, `c4\_policy\_wrapper.py`, `test\_gate7\_contract\_integrity.py`) are \*\*identical to HEAD\*\* with no unstaged differences, and HEAD descends linearly from `feedab71` only through documentation commits (`e4cd7d9` — L2 record, `6bd2189` — L3 record).



\*\*This adjudication proceeds against the implementation as recorded at `feedab71ab2ab0689b76e2492b25fc7283aa2283`\*\*, which is the sole coherent basis available in the evidence chain. The discrepancy in the stated SHA is noted as a record-keeping deficiency and must be corrected in the formal chain of custody. It does not by itself establish that the implementation is deficient; the implementation content, tests, and independent verification evidence are fully traceable to `feedab71`.



\---



\## 2. Governing Requirements



\### Gate 7 Requirements (SF-3.5-PROTO)



From `ADR-G7-Protocol-Versioning-and-Interoperability.md`, `Gate\_7\_Implementation\_Prompt.md`, and the Implementation Plan, the governing Gate 7 closure requirements are:



\*\*PROTO-1 — Explicit Identity Tuple:\*\* Every proof operation and verification decision must be qualified by `(protocol\_id, protocol\_version, scheme\_id, scheme\_version, policy\_version)`. All five fields must be explicit, carried through verification, and recorded.



\*\*PROTO-2 — No Inference:\*\* No identity-tuple element may be guessed, defaulted, inferred, reconstructed heuristically, silently substituted, or omitted and filled in later.



\*\*PROTO-2.1 — Metadata vs Public Input Boundary:\*\* Protocol/configuration metadata must be distinguished from cryptographic verifier-visible public inputs. `policy\_version` must not be automatically inserted as a cryptographic public input.



\*\*PROTO-3 — Deterministic Compatibility:\*\* Identical inputs produce identical compatibility outcomes. No silent fallback, "latest version" behavior, default versions, or wildcard matching.



\*\*PROTO-4 — Supported and Permitted Verification:\*\* The verifier accepts a proof only when protocol, protocol version, scheme, scheme version, and semantic contract are supported, and applicable verification policy permits.



\*\*PROTO-5 — Semantic Continuity:\*\* Protocol evolution preserves established semantic contracts. Architecture prevents incompatible semantic changes from masquerading as compatible versions.



\*\*PROTO-6 — Incompatible Changes Require New Protocol Version:\*\* Incompatible changes require a new `protocol\_version`.



\*\*PROTO-7 — Fail-Closed Downgrade Behavior:\*\* The verifier rejects unsupported protocol versions, unauthorized downgrades, unsupported scheme versions, and unauthorized compatibility paths.



\*\*Gate 6 Preservation:\*\* Gate 6's `SchemeVerifier` boundary is already formally adjudicated PASS and must remain unchanged.



\*\*Stage 3.4 Preservation:\*\* Verifier-visible public-input boundary semantics remain unchanged.



\*\*C1 ∧ C2 ∧ C3 ∧ C4 Acceptance Conjunction:\*\* The acceptance contract remains unchanged.



\### G7-CI Additional Requirements (on top of Gate 7 baseline)



From `ADR-G7-Contract-Integrity-and-Seal-Binding.md` and the G7-CI Implementation Plan, the targeted remediation added these specific requirements:



1\. `compute\_seal()` is content-derived and authoritative; the `seal` field is excluded from the seal input.

2\. `publish()` must always independently recompute the seal.

3\. A supplied seal that does not match the recomputed seal must fail closed.

4\. Caller-supplied seal is not authoritative without independent recomputation.

5\. `(protocol\_id, protocol\_version)` can bind to only one contract content/seal (immutability).

6\. Same identity + different content → `PROTOCOL\_CONTRACT\_IMMUTABLE`.

7\. Same identity + identical content → idempotent/no-op.

8\. A reused old valid seal against altered content cannot publish altered content.

9\. Runtime retrieval (`require()`) must recompute and validate the stored seal before returning.

10\. Integrity mismatches must fail closed.



\### G7-CI Non-Goals (Explicit Exclusions)

The G7-CI Implementation Plan § 13 explicitly defers:

\- Gate 7 D-3 runtime semantic authority and Protocol Catalog semantic execution

\- Protocol-version downgrade policy redesign

\- Policy-version validation redesign

\- Catalog persistence redesign

\- Production cryptographic certification

\- New ZK schemes

\- Gate 6 architectural changes

\- Stage 3.4 architectural changes



\---



\## 3. G7-CI Contract Integrity Determination



The following analysis is based on \*\*observed implementation facts\*\* from `feedab71`'s working tree (which is identical to HEAD for all G7-CI files), supplemented by test evidence.



\### Requirement 1: Content-derived seal is authoritative

\*\*Observed implementation fact:\*\* `ProtocolSemanticContract.compute\_seal()` at \[`protocol\_catalog.py` lines 39–54](file:///c:/Users/Samson/signal-forge/identity\_runtime/zk\_abstraction/protocol\_catalog.py#L39-L54) derives the seal as `SHA-256(json.dumps(payload, sort\_keys=True)\[:32])` over all semantic fields. The docstring states: "Authoritative content-derived seal. The seal field is excluded." The `seal` field is explicitly absent from the `payload` dict.



\*\*Assessment: SATISFIED.\*\*



\### Requirement 2: Publication recomputes the seal

\*\*Observed implementation fact:\*\* `ProtocolCatalog.publish()` at \[`protocol\_catalog.py` lines 92–137](file:///c:/Users/Samson/signal-forge/identity\_runtime/zk\_abstraction/protocol\_catalog.py#L92-L137) calls `contract.compute\_seal()` unconditionally on every invocation (line 101). It then constructs a new `ProtocolSemanticContract` with `seal=computed` (line 118), discarding any caller-supplied seal value from the stored object.



\*\*Assessment: SATISFIED.\*\*



\### Requirement 3: A supplied seal cannot establish integrity by itself

\*\*Observed implementation fact:\*\* If the caller supplies a non-empty seal, `publish()` checks `if contract.seal and contract.seal != computed: raise ValueError("PROTOCOL\_CONTRACT\_SEAL\_MISMATCH...")` (lines 102–106). The comparison is against the independently computed value; the supplied seal is never stored as-is without passing this check. The stored object always uses `seal=computed`, not the caller value.



\*\*Assessment: SATISFIED.\*\*



\### Requirement 4: A supplied seal that does not match recomputed content fails closed

\*\*Observed implementation fact:\*\* See Requirement 3 above — mismatched supplied seal raises `ValueError("PROTOCOL\_CONTRACT\_SEAL\_MISMATCH...")`. `publish()` fails before storing.



\*\*Test evidence:\*\* `test\_publish\_incorrect\_supplied\_seal\_rejected` (test line 57–75) establishes this case with a seal of `"0"\*32` against a valid contract. `test\_modified\_content\_with\_copied\_seal\_rejected` (lines 77–95) establishes the adversarial case of modified content + copied original seal.



\*\*Assessment: SATISFIED.\*\*



\### Requirement 5: `(protocol\_id, protocol\_version)` is the immutable contract identity

\*\*Observed implementation fact:\*\* `ProtocolCatalog` uses `key = (contract.protocol\_id, contract.protocol\_version)` as the dict key (line 100). The docstring states: "Governed catalog: published contracts are immutable under their version key."



\*\*Assessment: SATISFIED.\*\*



\### Requirement 6: Identical content under the same identity is idempotent

\*\*Observed implementation fact:\*\* When `existing is not None`, `publish()` computes `existing\_computed = existing.compute\_seal()` (line 123). If `existing\_computed == computed` (same content), it returns `existing` (line 134) without modifying the catalog.



\*\*Test evidence:\*\* `test\_identical\_republish\_idempotent` (lines 116–121) verifies this behavior.



\*\*Assessment: SATISFIED.\*\*



\### Requirement 7: Different content under an existing identity is rejected

\*\*Observed implementation fact:\*\* When `existing is not None` and `existing\_computed != computed` (line 129), `publish()` raises `ValueError("PROTOCOL\_CONTRACT\_IMMUTABLE...")` (lines 130–133).



\*\*Test evidence:\*\* `test\_modified\_content\_new\_seal\_same\_identity\_immutable` (lines 97–114).



\*\*Assessment: SATISFIED.\*\*



\### Requirement 8: Reusing an old valid seal against altered content cannot publish altered content

\*\*Observed implementation fact:\*\* The check at lines 102–106 fires first: if the caller provides a non-empty seal and the content has been changed, `compute\_seal()` produces a different result and the mismatch is detected before the identity-immutability check at line 129. Either path (seal mismatch → PROTOCOL\_CONTRACT\_SEAL\_MISMATCH, or content change with new seal → PROTOCOL\_CONTRACT\_IMMUTABLE) causes fail-closed behavior.



\*\*Test evidence:\*\* `test\_modified\_content\_with\_copied\_seal\_rejected` (lines 77–95) uses the exact adversarial scenario: mutated `stage\_3\_3\_context\_semantics` with the original `base.seal` copied. This raises `PROTOCOL\_CONTRACT\_SEAL\_MISMATCH` as required.



\*\*Assessment: SATISFIED.\*\*



\### Requirement 9: Runtime retrieval/trust recomputes and validates the stored seal

\*\*Observed implementation fact:\*\* `ProtocolCatalog.require()` at lines 145–154 calls `verify\_contract\_integrity(c)`. The standalone `verify\_contract\_integrity()` function at lines 74–83 independently calls `contract.compute\_seal()`, compares with `contract.seal`, and raises `ValueError("PROTOCOL\_CONTRACT\_SEAL\_MISMATCH...")` if they differ or if the seal is empty.



\*\*Assessment: SATISFIED.\*\*



\### Requirement 10: Integrity mismatches fail closed

\*\*Observed implementation fact:\*\* Both `publish()` and `require()` (via `verify\_contract\_integrity()`) raise `ValueError` on mismatch. In the C4 admission path (`c4\_policy\_wrapper.py` lines 119–136), these `ValueError` exceptions are caught and converted to `C4Evaluation(False, ConditionOutcome.FAIL, ...)` — i.e., fail closed. The `evaluate\_c4()` function does not swallow the exception; it explicitly returns a denial result with `status\_code="PROTOCOL\_CONTRACT\_SEAL\_MISMATCH"`.



\*\*Test evidence:\*\* `test\_c4\_fail\_closed\_on\_tampered\_catalog\_contract` (lines 171–192) injects a tampered contract directly into `cat.\_entries` and verifies `evaluate\_c4()` returns `allowed=False` with `status\_code="PROTOCOL\_CONTRACT\_SEAL\_MISMATCH"`. `test\_runtime\_require\_rejects\_tampered\_content` and `test\_runtime\_require\_rejects\_tampered\_seal` (lines 129–169) verify the `require()` path directly.



\*\*Assessment: SATISFIED.\*\*



\---



\## 4. Architectural Boundary Determination



\### Did G7-CI redefine protocol semantics?

\*\*No.\*\* `publish()` and `require()` are purely structural operations on the `ProtocolSemanticContract` data object. The semantic content fields (`stage\_3\_3\_context\_semantics`, `stage\_3\_4\_visibility\_semantics`, `c1\_crypto\_validity\_required`, `c2\_public\_key\_profile`, `c3\_binding\_profile`, `c4\_admission\_profile`, `acceptance\_conjunction`) are opaque labels/ids in the contract object — they are not evaluated, interpreted, or executed by `protocol\_catalog.py`. The docstring explicitly notes "values are opaque labels/ids, not ZK mechanisms."



\*\*Assessment: Boundary preserved.\*\*



\### Did G7-CI redesign the Protocol Catalog semantic model?

\*\*No.\*\* G7-CI added integrity checking (seal recomputation, immutability enforcement, runtime verification) to the existing `ProtocolCatalog` structure. It did not change the semantic model, the fields, or the interpretation of any field.



\*\*Assessment: Boundary preserved.\*\*



\### Did G7-CI execute arbitrary semantic-contract strings?

\*\*No.\*\* There is no evaluation engine, interpreter, or execution path for contract fields. D-3 (runtime semantic evaluation) is explicitly not implemented.



\*\*Assessment: Boundary preserved.\*\*



\### Did G7-CI alter Gate 6's SchemeVerifier boundary?

\*\*No.\*\* Gate 6's `SchemeVerifier` and `CryptographicRegistry` were not modified by any G7-CI commit. The diff for `3039f9ee` and `feedab71` only touches `protocol\_catalog.py` and `c4\_policy\_wrapper.py`. The `c4\_policy\_wrapper.py` change added `except ValueError` handling for the new integrity errors — it did not alter the `SchemeVerifier`, `BoundStatementTarget`, or the registry's scheme logic.



\*\*Assessment: Gate 6 boundary preserved.\*\*



\### Did G7-CI alter Stage 3.4 visibility semantics?

\*\*No.\*\* The `stage\_3\_4\_visibility\_semantics` field in the contract is an opaque label, not a computed or enforced mechanism. No changes were made to `verifier.py` or public-input construction in the G7-CI commits.



\*\*Assessment: Stage 3.4 boundary preserved.\*\*



\### Did G7-CI alter C1/C2/C3/C4?

\*\*No.\*\* The C4 path in `c4\_policy\_wrapper.py` received one addition: a `except ValueError` handler that propagates integrity failures as `C4Evaluation(False, ConditionOutcome.FAIL, ...)`. This does not change the definition of C4; it closes a new fail-path that the G7-CI integrity check opens. C1, C2, and C3 are not touched by any G7-CI commit.



\*\*Assessment: C1 ∧ C2 ∧ C3 ∧ C4 acceptance conjunction unchanged.\*\*



\### Did G7-CI introduce protocol-version inference/defaulting?

\*\*No.\*\* G7-CI makes no changes to the identity resolution or admission hardening logic. All defaults were already removed in `adeef375` (the parent Gate 7 candidate).



\*\*Assessment: No inference introduced.\*\*



\### Did G7-CI redesign policy governance or authorization?

\*\*No.\*\* No changes to authorization, credential lifecycle, or policy governance were introduced in any G7-CI commit.



\*\*Assessment: Boundary preserved.\*\*



\---



\## 5. Regression Preservation



\### Gate 6 Substitution

\*\*Evidence:\*\* L2 record `f39c9d4e2d9055d2` reports `test\_gate6\_substitution: 4/4 PASS`. L3 record `276d3506496b78e2` reports the same. No G7-CI commit modified `SchemeVerifier`, `BoundStatementTarget`, `CryptographicRegistry`, or any Gate 6 file.



\*\*Assessment: Gate 6 substitution preserved.\*\*



\### Stage 3.4

\*\*Evidence:\*\* L2 record reports `test\_phase34\_visibility\_boundary: 16/16 PASS`. L3 record confirms the same. No G7-CI commit modified any Stage 3.4 visibility boundary file.



\*\*Assessment: Stage 3.4 preserved.\*\*



\### Stage 3.5 ZK Abstraction

\*\*Evidence:\*\* L2 and L3 records both report `test\_phase35\_zk\_abstraction: 25/25 PASS`.



\*\*Assessment: Preserved.\*\*



\### R1.1 Targeted Remediation

\*\*Evidence:\*\* L2 and L3 records both report `test\_wp7\_r11\_targeted\_remediation: 9/9 PASS`.



\*\*Assessment: Preserved.\*\*



\### C4 Behavior

\*\*Evidence:\*\* L2 and L3 records both report `test\_wp7\_workstream\_c\_c4\_wrapper: 10/10 PASS`. The G7-CI addition to `c4\_policy\_wrapper.py` only adds a fail-closed path for the new integrity error codes; it does not alter any passing C4 path.



\*\*Assessment: Preserved.\*\*



\### Existing Gate 7 Interoperability

\*\*Evidence:\*\* L2 and L3 records both report `test\_gate7\_interoperability: 16/16 PASS`.



\*\*Assessment: Preserved.\*\*



\### Summary — 90/90 Total

All seven suites covered in the L2 and L3 records are consistent. No repository evidence contradicts the 90/90 PASS result.



\---



\## 6. D-1 / D-2 Determination



\### D-1 — Contract Content / Seal Binding



\*\*Original deficiency:\*\* `publish()` trusted the caller-supplied seal and used the seal string as the immutability comparison. A modified contract could reuse a previously valid seal and replace the existing contract under the same `(protocol\_id, protocol\_version)`.



\*\*Current status — RESOLVED.\*\*



\*\*Implementation evidence:\*\*

\- `publish()` now unconditionally calls `contract.compute\_seal()` (line 101 of `protocol\_catalog.py`).

\- A non-empty caller-supplied seal that does not match the computed seal raises `PROTOCOL\_CONTRACT\_SEAL\_MISMATCH` before any catalog modification (lines 102–106).

\- The stored seal is always `computed` (line 118), not the caller-supplied value.

\- Immutability is now enforced by comparing `existing\_computed != computed` (content-based comparison), not by comparing seal strings directly (lines 123–133).

\- The adversarial case (modified content + copied seal) is tested and confirmed to fail closed.



D-1 is resolved.



\### D-2 — Independent Seal Verification



\*\*Original deficiency:\*\* Published seals were not independently verified before trust.



\*\*Current status — RESOLVED.\*\*



\*\*Implementation evidence:\*\*

\- `ProtocolCatalog.require()` calls `verify\_contract\_integrity(c)` before returning (lines 145–154).

\- `verify\_contract\_integrity()` independently recomputes the seal via `contract.compute\_seal()` and compares with `contract.seal` (lines 74–83).

\- If the stored seal is empty or does not match the recomputed value, it raises `PROTOCOL\_CONTRACT\_SEAL\_MISMATCH`.

\- Only a contract that passes this independent verification is returned to callers.

\- The C4 admission path propagates this failure as `C4Evaluation(False, ...)`.



D-2 is resolved.



\---



\## 7. D-3 Determination



\*\*D-3 — Protocol Catalog Semantic-Contract Execution/Evaluation\*\*



\*\*What D-3 requires:\*\* Runtime evaluation of the semantic content of a `ProtocolSemanticContract` — i.e., an architecture that interprets or executes the contract's semantic fields (e.g., `stage\_3\_3\_context\_semantics`, `c3\_binding\_profile`) as operative rules, not merely as opaque labels.



\*\*Did G7-CI address D-3?\*\* \*\*No.\*\* Explicitly and by design.



\- `ADR-G7-Contract-Integrity-and-Seal-Binding.md` §5 (Scope Boundary): "This ADR addresses contract integrity and seal binding only. It does not define how the verifier evaluates contract semantics — that remains the separate D-3 remediation."

\- `Gate\_7\_Contract\_Integrity\_and\_Seal\_Binding\_Implementation\_Plan.md` §13 (Non-Goals): "Gate 7 D-3 runtime semantic authority" and "Protocol Catalog semantic execution" are explicitly deferred.

\- The implementation treats all semantic fields as opaque labels/ids (comment in `protocol\_catalog.py` line 29: "values are opaque labels/ids, not ZK mechanisms").



\*\*Does D-3 prevent Gate 7 closure under the governing requirements?\*\*



The governing Gate 7 requirements (`ADR-G7-Protocol-Versioning-and-Interoperability.md`) establish:

\- Protocol Catalog: bind `(protocol\_id, protocol\_version)` to one immutable contract ✓ (implemented)

\- Identity \& Admission Hardening ✓ (implemented in `adeef375`)

\- Compatibility / Version Enforcement ✓ (implemented — immutable contract prevents silent semantic reinterpretation)

\- Dedicated Interoperability Tests ✓ (implemented)



D-3 (runtime evaluation of semantic-contract content) was never enumerated as a Gate 7 exit criterion in the governing ADR or the Gate 7 Implementation Prompt. The exit criteria in the G7 Implementation Plan table (§11) include "Protocol Catalog," "Identity \& Admission Hardening," "Compatibility/Version Enforcement," and "Interoperability Tests" — none requires D-3 semantic execution to be operative before Gate 7 closes.



D-3 was identified as a \*finding\* in the original Gate 7 architecture audit, not as a mandatory exit criterion for the initial Gate 7 close. G7-CI's explicit scoping of D-3 as a non-goal, acknowledged and documented in the ADR and Implementation Plan, was itself architecturally approved.



\*\*Conclusion: D-3 does not prevent Gate 7 closure.\*\* It remains an open, deferred architectural item requiring a separate remediation cycle. It is not a G7-CI failure.



\---



\## 8. Remaining Findings and Limitations



\### D-5 — Catalog Persistence / Process Locality



\*\*Status:\*\* D-5 is outside G7-CI scope. The G7-CI Implementation Plan § 13 lists "Catalog persistence redesign" as an explicit non-goal. The current `ProtocolCatalog` is an in-process, in-memory store. No multi-process persistence or external catalog authority was implemented by G7-CI.



\*\*Is D-5 closure-blocking?\*\* Not established as a Gate 7 exit criterion in the governing ADR or Implementation Plan. D-5 is an architectural concern that remains open but is not a blocking finding for this targeted remediation.



\### D-6 / D-7 — Protocol/Policy Authority and Defaulting



\*\*Status:\*\* G7-CI made no changes to protocol-version selection, downgrade behavior, policy validation, authorization architecture, or protocol/policy authority. These were addressed in the parent Gate 7 candidate (`adeef375`) through the Identity \& Admission Hardening workstream (removal of lower-level defaults). G7-CI did not add or remove any defaulting logic. D-6/D-7 are not within G7-CI scope.



\*\*Is D-6/D-7 closure-blocking?\*\* Not raised as new blocking findings by either the L2 or L3 verification records. The 90/90 test suite demonstrates no regression in identity hardening behavior. Not closure-blocking for G7-CI.



\### L3 Limitations (Preserved Verbatim)



The following limitations are recorded in the L3 verification record (`276d3506496b78e2`) and are preserved without weakening:



1\. \*\*Phase 2.9 I2 local execution:\*\* L3 verification was verifier-controlled local L3 — not a separate CI account or multi-tenant isolated farm.

2\. \*\*Organizational channel:\*\* Roles (verifier distinct from implementer) are on record; same organizational channel as implementation assistance.

3\. \*\*Formal adjudication was OPEN:\*\* L3 explicitly stated that formal Gate 7 adjudication remained OPEN until this adjudication layer.

4\. \*\*No D-3 claim:\*\* L3 does not claim D-3 was implemented or evaluated.

5\. \*\*No production cryptographic soundness claim:\*\* L3 explicitly records this limitation.



\*\*Adjudicator treatment of limitations:\*\*

\- Limitation 1: The verifier-controlled local execution is noted. It does not meet the standard of a separate CI account or isolated farm. However, the governing requirements do not specify CI infrastructure as a mandatory prerequisite for Gate 7 closure. The I2 framework is the applicable standard, and the verification record is internally consistent.

\- Limitation 2: The organizational channel overlap is a limitation on independence, not a disqualifying conflict of interest given that roles are explicitly on record.

\- Limitation 3: This adjudication is the formal adjudication that was OPEN. It is now being resolved.

\- Limitation 4: Accepted. D-3 is not part of this adjudication.

\- Limitation 5: No production cryptographic soundness claim is required for Gate 7 closure (see §10 below).



None of these limitations independently violates a governing Gate 7 closure requirement.



\---



\## 9. L2 / L3 Evidence



\### L2 — `f39c9d4e2d9055d2` — 90/90 PASS



\*\*What it establishes:\*\*

\- That the test suites (contract integrity 10/10, interoperability 16/16, Gate 6 substitution 4/4, C4 wrapper 10/10, Stage 3.5 ZK abstraction 25/25, R1.1 9/9, Stage 3.4 16/16) all passed against the implementation at `feedab71`.

\- That G7-CI Workstreams A–E were exercised by the test suite.



\*\*What it does not establish:\*\*

\- Production cryptographic soundness.

\- Multi-tenant or CI-farm isolation.

\- D-3 semantic evaluation.

\- Architectural properties not exercised by the test suite (the tests are necessary but not alone sufficient for architectural closure — they must be evaluated against the governing requirements, as this adjudication does).



\*\*Recorded limitations:\*\* Developer-controlled local checkout. Same organizational channel as implementation assistance. Formal Gate 7 adjudication remained OPEN.



\### L3 — `276d3506496b78e2` — PASS



\*\*What it establishes:\*\*

\- Independent verifier-controlled re-execution of all seven suites against `feedab71`, with the same 90/90 PASS results.

\- Verifier (`verifier-gate7-g7ci-l3-independent`) is distinct on the record from implementer (`implementer-gate7-g7ci`).

\- Escalation from L2 `f39c9d4e2d9055d2`.



\*\*What it does not establish:\*\*

\- Separate CI account or multi-tenant farm.

\- Production cryptographic soundness.

\- D-3 implementation or evaluation.

\- That the stated adjudication candidate SHA `5f7523bf3865dce519ccd87a82fe897f665bd123` maps to any repository object (the L3 record uses `feedab71`).



\*\*Recorded limitations:\*\* Phase 2.9 I2 policy; same organizational channel; formal Gate 7 adjudication remained OPEN; no D-3 claim; no production cryptographic soundness claim.



\---



\## 10. Final Closure Rationale



\### Working Tree Dirtiness

The repository working tree is dirty. The dirty state consists of:

\- Deleted `.docx` architecture documents (unrelated to G7-CI)

\- Modified `lambda/` files (unrelated to G7-CI)

\- Modified `dapp\_api/nonce\_store.json`, `presentation\_audit.jsonl`, `recovery\_audit.jsonl` (runtime state files, unrelated to G7-CI)

\- Untracked `Daytona/` test files, ADR files, and architecture documents (all unrelated to G7-CI)



\*\*None of the dirty files intersect with the G7-CI implementation surface.\*\* Git diff of `HEAD` against working tree for `protocol\_catalog.py`, `c4\_policy\_wrapper.py`, and `test\_gate7\_contract\_integrity.py` produces no output — these files are unmodified in the working tree. The dirty state does not affect the G7-CI candidate or adjudication.



\### SHA Discrepancy

The stated adjudication SHA `5f7523bf3865dce519ccd87a82fe897f665bd123` does not exist in the repository. The evidence chain (L2, L3) consistently identifies `feedab71ab2ab0689b76e2492b25fc7283aa2283` as the frozen candidate. This is a chain-of-custody record-keeping deficiency that must be corrected. For adjudication purposes, the SHA discrepancy affects traceability but does not introduce ambiguity about the actual implementation being evaluated, since `feedab71` is uniquely identified in both verification records and the implementation is fully traceable.



\### Governing Requirements — Satisfied

The ten G7-CI contract-integrity requirements are each satisfied by direct implementation evidence in `protocol\_catalog.py` and `c4\_policy\_wrapper.py`. No architectural boundary prohibitions were violated. All seven regression suites pass with 90/90 results confirmed by both L2 and L3 independent verification.



\### D-1 and D-2 — Resolved

Both deficiencies that prompted G7-CI are demonstrably resolved in `feedab71`. The implementation closes the specific integrity gap: publication now independently recomputes the seal; altered content with a copied seal cannot publish; runtime consumption verifies integrity before trust; failures fail closed.



\### D-3 — Not Blocking

D-3 is an explicitly deferred non-goal of G7-CI, and is not a mandatory exit criterion in the governing Gate 7 requirements. It does not prevent closure of this targeted remediation.



\### D-5, D-6, D-7 — Not Blocking

These are outside G7-CI scope and are not established as closure-blocking by the governing Gate 7 requirements.



\### L3 Limitations — Not Blocking

The recorded L3 limitations (local execution, organizational channel, no D-3 claim, no cryptographic soundness claim) are preserved without weakening. None independently violates a governing Gate 7 closure criterion.



\### No Production Cryptographic Soundness Required

The governing Gate 7 requirements, the G7-CI ADR, and the G7-CI Implementation Plan explicitly list "Production cryptographic certification" as a non-goal. The absence of a production cryptographic soundness certification is therefore not a Gate 7 failure.



\---



\## 11. Formal Adjudication Record



| Field | Value |

|---|---|

| \*\*Gate\*\* | Stage 3.5 Gate 7 |

| \*\*Scope\*\* | Protocol Versioning and Interoperability |

| \*\*Remediation\*\* | G7-CI — Contract Integrity and Seal Binding |

| \*\*Adjudication Target SHA (stated)\*\* | `5f7523bf3865dce519ccd87a82fe897f665bd123` (does not exist in repository) |

| \*\*Actual Implementation SHA (evidence chain)\*\* | `feedab71ab2ab0689b76e2492b25fc7283aa2283` |

| \*\*Parent Gate 7 Candidate\*\* | `adeef37508214fe1522f5941ac67539f1acd52a3` (confirmed) |

| \*\*Repository HEAD at adjudication\*\* | `6bd2189ed1fcece568ac7d56b10e3fffa33878dc` |

| \*\*L2 Verification ID\*\* | `f39c9d4e2d9055d2` — 90/90 PASS |

| \*\*L3 Verification ID\*\* | `276d3506496b78e2` — PASS |

| \*\*Adjudicator\*\* | Antigravity formal adjudication agent (this conversation: `850a1c04-a6bc-446c-bc7e-0da564148caa`); model: Claude Sonnet 4.6 (Thinking) |

| \*\*Adjudication Result\*\* | \*\*GATE 7 — CLOSED / PASS\*\* |

| \*\*Adjudication Timestamp\*\* | 2026-09-30T04:45:43-04:00 (local); 2026-09-30T08:45:43Z |



\### Governing Requirements Determination

Gate 7 is governed by SF-3.5-PROTO requirements (PROTO-1 through PROTO-7) as established in the Gate 7 ADR, Implementation Plan, and Implementation Prompt. These requirements were met by the combined implementation at `adeef375` (PROTO-1 through PROTO-7 baseline) and `feedab71` (G7-CI contract integrity). The G7-CI exit criteria (§12 of the G7-CI Implementation Plan) are all satisfied.



\### Evidence Determination

The implementation at `feedab71` is confirmed from repository inspection. L2 (`f39c9d4e2d9055d2`) provides independent test re-execution evidence (90/90 PASS). L3 (`276d3506496b78e2`) provides verifier-controlled re-execution evidence (90/90 PASS). Both records are consistent and mutually corroborating. Repository code matches working-tree state at all G7-CI files. Dirty working tree does not intersect with G7-CI files.



\### D-1 Treatment

\*\*RESOLVED.\*\* `publish()` independently recomputes the seal; caller-supplied seal mismatch fails closed; immutability is content-based; altered content with a copied seal is rejected. Adversarial case tested and confirmed.



\### D-2 Treatment

\*\*RESOLVED.\*\* `require()` calls `verify\_contract\_integrity()` which independently recomputes the seal before returning a contract. Runtime consumers cannot receive an integrity-invalid contract without an explicit `ValueError`.



\### D-3 Treatment

\*\*EXPLICITLY NOT ADDRESSED BY G7-CI — NOT CLOSURE-BLOCKING.\*\* D-3 (Protocol Catalog semantic-contract execution/evaluation) is an explicitly deferred non-goal in the G7-CI ADR and Implementation Plan. It is not an enumerated exit criterion in the governing Gate 7 ADR or Implementation Plan. It remains an open deferred item requiring a separate remediation cycle. It does not prevent Gate 7 closure.



\### D-5 Treatment

Outside G7-CI scope. Not a governing Gate 7 closure requirement. Catalog persistence remains in-memory/in-process. Deferred. Not blocking.



\### D-6 / D-7 Treatment

Outside G7-CI scope. Identity \& Admission Hardening (no protocol/policy defaults) was implemented in the parent Gate 7 candidate `adeef375` and confirmed preserved (90/90 regression suites). Not blocking.



\### L3 Limitations Treatment

All five recorded L3 limitations are preserved verbatim. None independently violates a governing Gate 7 closure requirement. The absence of a separate CI account or multi-tenant farm is a limitation on execution independence, but falls within the I2 framework applicable to this stage. The organizational channel limitation is noted but not disqualifying given that roles are distinct on the record.



\### Gate 6 Preservation Statement

Gate 6 is formally closed. Gate 6's `SchemeVerifier` boundary, `BoundStatementTarget`, `CryptographicRegistry`, and scheme adapter architecture were not modified by any G7-CI commit. `test\_gate6\_substitution: 4/4 PASS` confirmed by L2 and L3. Gate 6 is preserved.



\### Stage 3.4 Preservation Statement

Stage 3.4 verifier-visible public-input boundary semantics were not modified by any G7-CI commit. `test\_phase34\_visibility\_boundary: 16/16 PASS` confirmed by L2 and L3. Stage 3.4 is preserved.



\### Production Cryptographic Soundness Statement

No production cryptographic soundness claim is made and none is required. The governing Gate 7 requirements and the G7-CI Implementation Plan explicitly list "Production cryptographic certification" as a non-goal. This adjudication does not certify production cryptographic soundness.



\### Final Closure Rationale

Gate 7 closes on G7-CI because:

1\. The governing Gate 7 requirements (PROTO-1 through PROTO-7) are satisfied by the combined implementation (parent `adeef375` + G7-CI `feedab71`).

2\. D-1 and D-2, the specific deficiencies that motivated G7-CI, are demonstrably resolved in `feedab71`.

3\. D-3, the one remaining significant finding, is an explicitly deferred non-goal that does not appear as a mandatory exit criterion in the governing Gate 7 requirements.

4\. All architectural boundaries (Gate 6, Stage 3.4, C1 ∧ C2 ∧ C3 ∧ C4) are preserved.

5\. 90/90 regression tests pass across all seven suites, confirmed by both L2 and L3 verification.

6\. L3 limitations are preserved and do not independently block closure.

7\. The chain-of-custody SHA discrepancy is a record-keeping deficiency (noted and not resolved by this adjudication) but does not introduce ambiguity about the actual implementation evaluated.



\*\*GATE 7 — CLOSED / PASS\*\*



\---



\*Record produced by formal adjudication — no implementation changes were made during this adjudication.\*



