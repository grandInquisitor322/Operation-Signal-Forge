**ADR-G7: Protocol Contract Integrity and Seal Binding**



**D-1 — Content/seal binding is not enforced at publication.**

ProtocolSemanticContract seals are content-derived by compute\_seal(), but publish() trusts the caller-provided seal and uses the seal string as the immutability comparison. A modified contract can therefore reuse the previously valid seal and replace the existing contract under the same (protocol\_id, protocol\_version). The frozen object prevents post-publication mutation, but does not prevent publication of altered content carrying a copied seal.



1. **Content-derived seal**
compute\_seal() is authoritative.
The seal field itself is excluded from the input to compute\_seal().
2. **Publication verification**
If publish() accepts a supplied seal, it MUST recompute the seal from the contract content.
A mismatch MUST fail closed.
3. **Identity immutability**
(protocol\_id, protocol\_version) can bind to only one contract content/seal.
Same identity + different contract content → PROTOCOL\_CONTRACT\_IMMUTABLE.
Same identity + identical contract → idempotent/no-op.
4. **Runtime integrity verification**
Before trusting a catalog contract, runtime MUST recompute its seal and compare it with the stored seal.
Mismatch → fail closed.
5. **Scope boundary**
This ADR addresses contract integrity and seal binding only.
It does not define how the verifier evaluates contract semantics—that remains the separate D-3 remediation.
6. **Relationship to the original Gate 7 ADR**
Explicitly state that this ADR supplements/clarifies ADR-G7-Protocol-Versioning-and-Interoperability.

&#x20;   It should not silently redefine unrelated Gate 7 requirements.

