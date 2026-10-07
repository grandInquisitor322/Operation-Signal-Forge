# Independent Verification Package — Phase 2.8

**Hand this to the independent verifier (e.g. Claude).**

Verifier must be **distinct** from the implementer and may **confirm or escalate** the level (never de-escalate).

## 1. Assignment (proposal)

| **Field** | **Value** |
| --- | --- |
| Phase | **2.8 — Independent Assurance & Verification Maturity** |
| Scope | phase-2.8-verification-maturity |
| Implementer | implementer-phase28 |
| **Proposed level** | **2** — Independent test re-execution |
| Domains | audit_compliance, api_behavior |
| Risk rationale | Assurance-process control for H1; behavioral change to verification recording gates; not a full identity-recovery/crypto redesign |
| Why not Level 1 | Changes behavior of PASS evidence requirements (not docs-only) |
| Why not Level 3 (proposal) | No production identity auth path changed; tooling-agnostic Level 2 re-execution is proportional. **Verifier may escalate to 3.** |

**Ambiguity rule:** if unsure, escalate to Level 3.

## 2. What changed (spot-check list)

| **Module** | **Purpose** |
| --- | --- |
| identity_runtime/verification_levels.py | Levels 1–3; propose_level; confirm_or_escalate (no de-escalate); evidence gates |
| identity_runtime/independent_verification.py | Leveled records; PASS blocked without Level 2/3 evidence |
| identity_runtime/tests/test_phase28_verification_levels.py | 10 unit tests |
| identity_runtime/tests/test_phase27_assurance.py | Updated so H1 record supplies Level-compatible evidence |

**Must not have changed**: credential lifecycle, Trust Registry, Matrix, recovery executor semantics, Fusion, sensors, G4 hash-chain meaning.

## 3. Implementer-reported regression (do not treat as sole Level 2 evidence)

| **Suite** | **Result** |
| --- | --- |
| test_phase28_verification_levels | 10/10 PASS |
| test_phase27_assurance | 7/7 PASS |
| test_phase26_audit_recovery | 7/7 PASS |
| test_phase24_identity_infra | 13/13 PASS |
| test_renewal_rotation | 12/12 PASS |
| test_trust_governance | 12/12 PASS |
| test_did_method_policy | 6/6 PASS |
| test_recovery_policy | 7/7 PASS |
| **Total** | **74/74 PASS** |

Existing implementer verification row (for reference only):

af900cdb3851add4 · Level 2 · dapp_api/independent_verification.jsonl
