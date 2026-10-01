# Operation Signal Forge — Stage 3.5 Formal Closure Adjudication

**Status:** Adjudicator determination, for governance recording. Not yet committed to the repository.
**Mode:** Read-only. No repository file, branch, commit or history was modified. This record exists outside the repository.

## Decision

**STAGE 3.5 — CLOSED / PASS, WITH RECORDED CONDITIONS**

The conditions in §7 are custody and carry-forward items. None reopens Gate 5, Gate 6 or Gate 7, and none is a Stage 3.5 closure blocker on the evidence available. Condition C-1 (governing documents not in the repository) limits how far I could independently verify the requirement text.

## 1. Inputs and constraints applied

- **Readiness input:** `Stage_3.5_Closure_Readiness_Report.md` (tip observed `01b2dddaa6af6b7ddb7585bb7590cf7a8de221a0`, 2026-10-01). Treated as an input, not as closure.
- **Truncation:** the supplied report ends inside §4 (the layering diagram). Its §5 and §6, including the evidence chain this record was to cite, were not supplied. The chain below was rebuilt from the report's §2 and §3 and checked against the repository. It is not a copy of the report's §6.
- **Rules followed:** no reopening of Gates 5–7 without direct contradictory evidence. D-3, production cryptographic certification and Matrix integration are not treated as blockers unless a governing exit criterion requires them. Both Gate 7 SHA values are preserved.

## 2. Repository integrity

| Check | Result |
|---|---|
| `01b2dddaa6af6b7ddb7585bb7590cf7a8de221a0` | Exists; equals `origin/main` at fetch time. |
| `feedab71ab2ab0689b76e2492b25fc7283aa2283` (authoritative G7-CI implementation) | Exists; ancestor of tip. |
| `adeef37508214fe1522f5941ac67539f1acd52a3` (parent Gate 7 candidate) | Exists; ancestor of tip. |
| `5f7523bf3865dce519ccd87a82fe897f665bd123` (originally recorded candidate) | **Not a repository object.** Preserved as the historical record, per the Chain-of-Correction Note. |
| `d0ecc8f8378070b16bc85111c7ab70a37458df9c` (Gate 5 re-adjudicated candidate) | Exists; ancestor of tip. |
| Changes after `feedab71` up to tip | Four files only: `Gate_7_Formal_Adjudication.md`, `Gate_7_Chain_of_Correction_Note.md`, `third-party-apis-and-licenses.md`, and `dapp_api/independent_verification.jsonl`. **`identity_runtime/` is byte-identical to `feedab71`.** |
| Parent to `feedab71` code change | Three files: `protocol_catalog.py`, `c4_policy_wrapper.py`, `test_gate7_contract_integrity.py`. |

## 3. Gate determinations

| Gate | Formal record in repository | Decision recorded | Verification IDs (present in `independent_verification.jsonl`) |
|---|---|---|---|
| **5** | `docs/architecture/stage-3.5/WP-7/Abjudication Reports/WP7-CAND-01R1.1 — Gate 5 Re-Adjudication Report.md` (2026-09-21) | PASS on SF-3.5-VER-1 to VER-6 and CONF-3/CONF-4. R-1 and R-2 CLOSED. | `0443695590caa787` (R1.1 L2, PASS, 2026-09-18). `7b52a66a0f5f7397` (Phase 3.5 abstraction L2, PASS, 2026-09-04). |
| **6** | `.../gate-6-cryptographic-agility/Gate_6_Formal_Adjudication.md` (2026-09-25) | GATE 6 — CRYPTOGRAPHIC AGILITY: PASS | `b4e005e81baf180e` (L2, PASS). `02f259757e3989ae` (L3, `verifier-gate6-l3-independent`, PASS). |
| **7** | `.../gate-7-protocol-versioning/Gate_7_Formal_Adjudication.md` (2026-09-30); `Gate_7_Chain_of_Correction_Note.md` | GATE 7 — CLOSED / PASS | `cd6d80d1b6ab784b` (parent L2, PASS). `f39c9d4e2d9055d2` (G7-CI L2, PASS). `276d3506496b78e2` (G7-CI L3, PASS). |

Notes:
- The readiness report's Gate 5 row cites trail records but not the Gate 5 re-adjudication report above. Add that path to the evidence chain.
- All six IDs named in the readiness report were found. Each is PASS with a named implementer and verifier.

## 4. Independent re-execution at tip (`01b2ddd`, archive copy)

| Suite | Result |
|---|---|
| `test_gate7_contract_integrity` | 10/10 |
| `test_gate7_interoperability` | 16/16 |
| `test_gate6_substitution` | 4/4 |
| `test_gate5_fail_closed_verifier` | 4/4 |
| `test_wp7_workstream_c_c4_wrapper` | 10/10 |
| `test_phase35_zk_abstraction` | 25/25 |
| `test_wp7_r11_targeted_remediation` | 9/9 |
| `test_phase34_visibility_boundary` | 16/16 |
| **Full `identity_runtime/tests` discovery** | **262/262 OK** |

Direct inspection of `protocol_catalog.py` at `feedab71`: publication recomputes the seal and rejects a mismatched supplied seal. Different content under an existing `(protocol_id, protocol_version)` is rejected as immutable. `require()` re-verifies the stored seal before returning. In my probes, altered content with a copied old seal, an arbitrary seal and a stale-seal tamper were all rejected or detected. D-1 and D-2 are resolved. `verifier.py`, `registry.py`, `acceptance.py`, `scheme_types.py` and the adapters are unchanged in G7-CI, so Gate 6, Stage 3.4 and C1 ∧ C2 ∧ C3 ∧ C4 are untouched.

## 5. Readiness-report requirements (§3 of the report)

All rows marked SATISFIED are consistent with the repository evidence. The rows marked DEFERRED / NON-BLOCKING are accurately described: D-3 semantic execution, production cryptographic certification, and runtime proof path plus Matrix integration.

## 6. Contradictory-evidence search

I found **no direct contradictory evidence** that requires reopening Gate 5, 6 or 7. These observations are carried forward, not reopened. I made them in earlier independent verification, and they are unchanged at tip:

- **O-1 (D-3):** nothing outside the catalog reads contract fields. They are opaque labels. This matches the recorded non-goal.
- **O-2 (D-4):** protocol versions have no minimum-version or deprecation control. An older allowed protocol version is still accepted when a newer one is published. The Gate 7 adjudication reads PROTO-7 as met through the identity and admission allowlists. I cannot confirm what the ADR says "unauthorized downgrade" means (see C-1), so this is flagged for governance, not asserted as a defect.
- **O-3 (D-5):** the catalog is process-local with no external anchor. A self-consistent replacement through the private `_entries` store is accepted by `require()`.
- **O-4 (D-6/D-7):** the catalog and the registry both control which protocol versions are allowed. Verifier-side defaults exist. `require_policy_match=False` accepts any policy string.
- **O-5 (D-8):** audit entries and results do not record the contract seal.

## 7. Recorded conditions and limitations

- **C-1 — governing documents not in the repository.** `ADR-G7-Protocol-Versioning-and-Interoperability.md`, `ADR-G7-Contract-Integrity-and-Seal-Binding.md`, the Gate 7 and G7-CI implementation plans and prompts, and any Stage 3.5 exit-criteria document are absent from `01b2ddd`. The Gate 7 adjudication says its ADR files were untracked in the adjudicator's dirty working tree. I verified the records, code and tests. I could not verify the requirement text (PROTO-1 to PROTO-7, the G7-CI non-goals, the exit criteria) against its source, and I accepted the Gate 7 adjudication's quotation of it. Governance should commit those documents so closure rests on tracked artifacts.
- **C-2 — scope of "Stage 3.5".** The repository holds formal records for Gates 5, 6 and 7 only. I found nothing on Gates 1–4 and cannot tell whether they exist. This closure covers Gates 5–7 and the Stage 3.5 requirements in the readiness report.
- **C-3 — independence limits (preserved from the recorded L3).** Level 3 is local, verifier-controlled execution under Phase 2.9 I2, not a separate CI or multi-tenant farm. Roles are distinct on the records, but the commits share one git author. The Gate 5 and Gate 7 formal adjudications were made by AI agents in the same organizational channel. No D-3 claim. No production cryptographic soundness claim.
- **C-4 — scheme coverage.** Gate 6 substitution evidence uses mock adapters only.
- **C-5 — trail completeness.** The trail has no record of the Level 3 FAIL I issued on `adeef37` in chat. I cannot tell from the repository whether it motivated G7-CI, so I make no claim either way.
- **C-6 — test hygiene.** Running the suite rewrites tracked files (`dapp_api/*.json*`, workstream evidence JSON). I ran from an archive copy.

## 8. Formal adjudication record

| Field | Value |
|---|---|
| Stage | 3.5 — Cryptographic abstraction and verification (Gates 5, 6, 7) |
| Readiness input | `Stage_3.5_Closure_Readiness_Report.md`, tip `01b2dddaa6af6b7ddb7585bb7590cf7a8de221a0`; §5–§6 not supplied |
| Authoritative Gate 7 implementation SHA | `feedab71ab2ab0689b76e2492b25fc7283aa2283` |
| Originally recorded Gate 7 candidate SHA | `5f7523bf3865dce519ccd87a82fe897f665bd123` (not a repository object; preserved) |
| Parent Gate 7 candidate SHA | `adeef37508214fe1522f5941ac67539f1acd52a3` |
| Gate verification IDs | G5: `0443695590caa787`, `7b52a66a0f5f7397`; G6: `b4e005e81baf180e`, `02f259757e3989ae`; G7: `cd6d80d1b6ab784b`, `f39c9d4e2d9055d2`, `276d3506496b78e2` |
| Regression at tip | 262/262 (full suite), plus the eight named suites |
| Result | **STAGE 3.5 — CLOSED / PASS, WITH RECORDED CONDITIONS C-1 to C-6** |
| Deferred, non-blocking | D-3 semantic-contract execution; production cryptographic certification; catalog persistence (D-5); protocol and policy authority and defaulting (D-6/D-7); runtime proof path and Matrix integration |
| Adjudicator | Claude (Sonnet 5.5), in a claude.ai chat session. Not a role recorded in the verification trail. |
| Date | 2026-10-01. Exact time not available from the environment. |

**Non-claims.** This record makes no production cryptographic soundness claim, no legal or regulatory certification, and no claim that D-3, D-5, D-6, D-7 or Matrix integration were resolved.
