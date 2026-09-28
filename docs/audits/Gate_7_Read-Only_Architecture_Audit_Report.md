# Operation Signal Forge — Gate 7 Read-Only Architecture Audit Report

**Stage 3.5 — Protocol Versioning and Interoperability (WP-3)**  
**Document type:** Architecture audit baseline (not formal Gate 7 adjudication)  
**Mode:** Read-only — no code, tests, or documentation modified during the audit  
**Tree inspected:** `aa4ecce` (public `origin/main` snapshot used for inspection)  
**Date:** 2026-09-25  

**Authoritative references (as stated in the audit prompt):**

- Stage 3.5 Specification: `SPEC-STAGE-3.5-001`
- Stage 3.5 Principle 3.5-10 — Protocol Versioning and Interoperability
- Requirement family: `SF-3.5-PROTO-1` … `SF-3.5-PROTO-7` (including `PROTO-2.1`)
- Work Package: **WP-3**
- Architectural Test: **Interoperability Test**

**Not claimed by this report:**

- Formal Gate 7 PASS or FAIL
- Production cryptographic assurance
- Post-quantum security
- Interoperability with external production systems
- Reopening or re-adjudication of Gate 6

---

## A. Executive Summary

**Current Gate 7 posture:** Substantial protocol/scheme/policy plumbing already exists in the repository: an explicit five-field `IdentityTuple`, C4 protocol/scheme/policy evaluation, registry allowlists and lifecycle checks, audit logging of the full identity tuple, and a Gate 6 `SchemeVerifier` boundary that does not treat protocol/policy metadata as automatic public inputs.

**Preliminary baseline:** **REMEDIATION REQUIRED**

**Main findings:**

1. **PROTO-1 and PROTO-2.1 are largely implemented.** The five identity-tuple fields are explicit on the verification request path and in audit records. Inclusion in the identity tuple does **not** automatically place `policy_version` (or protocol fields) into `public_input_view` or the C3 semantic binding.
2. **PROTO-3, PROTO-4, and PROTO-7 are partial PASS.** Exact protocol-version membership, exact scheme key resolution, lifecycle handling, policy match, and several fail-closed C4 tests exist.
3. **PROTO-5 and PROTO-6 are gaps.** There is no explicit semantic-continuity / incompatibility mechanism that forces a new `protocol_version` when Stage 3.3/3.4/C1–C4 meaning would change. `migration.py` provides scheme-migration evaluation stubs only.
4. **PROTO-2 residual risk.** `CryptographicRegistry.validate_operation(..., protocol_version="1.0.0", policy_version="1.0.0")` supplies defaults that can fill tuple elements if callers bypass C4’s explicit checks.
5. **No dedicated Gate 7 Interoperability Test suite.** Coverage is primarily Workstream C (C4) unit tests plus incidental fixed `1.0.0` tuples in other suites.

Gate 6 should **not** be reopened. Protocol versioning currently sits in identity metadata, C4, and registry governance around the existing cryptographic boundary.

---

## B. Requirement Matrix

| Requirement | Status | Evidence | Finding |
| ----- | ----- | ----- | ----- |
| PROTO-1 | PASS (with note) | `identity_runtime/zk_abstraction/identity.py` (`IdentityTuple`); `VerificationRequest.identity_tuple`; `c4_policy_wrapper.evaluate_c4`; `audit.log_verification` | All five fields are explicit on the request path and in audit. They are not all fields of `BoundStatementTarget` (consistent with PROTO-2.1). |
| PROTO-2 | GAP | `registry.validate_operation(..., protocol_version="1.0.0", policy_version="1.0.0")`; `DEFAULT_POLICY_CONTEXT` when `policy_context is None` | C4 rejects empty identity fields on the normal path, but the registry API can still default protocol/policy versions if invoked without kwargs. No heuristic scheme aliasing observed. |
| PROTO-2.1 | PASS | `identity.py` docstring (SF-3.5-PROTO-2.1); `ALLOWED_PUBLIC_KEYS` excludes protocol/policy fields; `_build_bound_statement` copies only `verifier_visible_inputs` | Tuple membership does not auto-make cryptographic public inputs. `policy_version` is not in the public allowlist or bound view. |
| PROTO-3 | PASS (partial) | Registry: unsupported protocol version if not in `_allowed_protocol_versions`; scheme resolve on exact `(scheme_id, scheme_version)`; C4 `protocol_id` allowlist | Deterministic exact-match style; no wildcards or “latest” resolver found. No separate semantic compatibility matrix beyond allowlists (see PROTO-5/6). |
| PROTO-4 | PASS (partial) | `IndependentVerifier.verify_proof`: C4 → C2 → C3 → C1; C4 uses registry + `VerifierPolicyContext`; C1 uses Gate 6 `resolve_verifier` | Supported/permitted checks exist. “Semantic contract compatible” is not a separate governed object—only version/policy/scheme checks. |
| PROTO-5 | GAP | No protocol semantic-contract registry; `migration.py` is scheme-only stubs | Architecture does not demonstrate protection against silent semantic drift under the same `protocol_version`. |
| PROTO-6 | GAP | No enforced “incompatible change ⇒ new protocol_version” control in code | Relies on process/discipline rather than an implemented gate. |
| PROTO-7 | PASS (partial) | C4 tests: unsupported protocol version, scheme min-version downgrade, policy mismatch, missing fields; registry fail-closed on unregistered scheme | Strong C4/registry negatives. Broader interoperability negatives and registry default-bypass surface remain residual concerns. |

---

## C. Identity Tuple Trace

| Field | Origin | Representation | Through verification | Outcome / audit |
| ----- | ----- | ----- | ----- | ----- |
| `protocol_id` | Caller constructs `IdentityTuple` on `VerificationRequest` | `IdentityTuple.protocol_id` | C4 allowlist (`VerifierPolicyContext.allowed_protocol_ids`, default `{"sf-zk"}`) | Audit `identity_tuple.protocol_id` |
| `protocol_version` | Same | `IdentityTuple.protocol_version` | C4 non-empty check → `registry.validate_operation(protocol_version=...)` vs `_allowed_protocol_versions` (default `{"1.0.0"}`) | Audit |
| `scheme_id` | Same | `IdentityTuple.scheme_id` | C4 → registry resolve / lifecycle → Gate 6 `resolve_verifier` / `BoundStatementTarget.scheme_id` | Audit + C1 crypto result echo |
| `scheme_version` | Same | `IdentityTuple.scheme_version` | Same + optional `_min_scheme_version` downgrade check | Audit + C1 |
| `policy_version` | Same | `IdentityTuple.policy_version` | C4 non-empty; optional match to `active_policy_version` when `require_policy_match` | Audit; **not** in `public_input_view` |

**Reconstruction:** The normal verify path does not rebuild the identity tuple from proof bytes. Scheme materials come from registry descriptor and verifier binding.

**Note:** `BoundStatementTarget` carries `scheme_id`, `scheme_version`, `materials_ref`, and domain `public_input_view` — not `protocol_id`, `protocol_version`, or `policy_version`. That is consistent with PROTO-2.1 when those remain governance metadata (C4 + audit).

---

## D. Compatibility Decision Flow (as implemented)

```text
VerificationRequest
  identity_tuple (5 fields) + proof_bytes + verifier_visible_inputs
        ↓
C4 evaluate_c4(registry, identity, policy_context?)
  - reject missing / ambiguous protocol or scheme fields
  - protocol_id ∈ allowed_protocol_ids
  - optional policy_version == active_policy_version
  - registry.validate_operation(scheme, scheme_version,
        protocol_version=identity.protocol_version,
        policy_version=identity.policy_version)
      · scheme registered?
      · protocol_version ∈ allowed_protocol_versions?
      · scheme version ≥ min (if set)?
      · lifecycle / deprecated ops?
        ↓
C2 allowlist + required public keys + scalar profile (scheme modulus)
        ↓
C3 ContextClaimBinder + domain consistency (no identity-tuple fields)
        ↓
C1 SchemeVerifier.verify_crypto(proof, BoundStatementTarget)
  - scheme_id/version/materials from registry + snapshot
  - no protocol_id/policy_version in bound target
        ↓
evaluate_acceptance(C1 ∧ C2 ∧ C3 ∧ C4) → taxonomy → audit(log full identity_tuple)