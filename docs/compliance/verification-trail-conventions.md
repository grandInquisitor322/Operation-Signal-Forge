# Verification Trail Conventions

**Project:** Operation Signal Forge  
**Status:** Standing process note (H1 Independent Verification)  
**Aligned through:** Stage 3.5 **CLOSED / PASS** (Gates 5–7); Gate 7 formal adjudication CLOSED / PASS  
**Authoritative G7-CI implementation SHA:** `feedab71ab2ab0689b76e2492b25fc7283aa2283`  
**Originally recorded G7-CI candidate SHA (historical, not a Git object):** `5f7523bf3865dce519ccd87a82fe897f665bd123`  
**Nature:** Evidentiary hygiene — **non-certifying**

These conventions keep `dapp_api/independent_verification.jsonl` usable as a phase-over-phase evidence trail. They do not change the Level 1/2/3 *definitions* in `verification_levels.py`; they govern **how records are written and interpreted**.

---

## 1. Store and immutability

| Rule | Practice |
|------|----------|
| **Single append-only log** | Default path: `dapp_api/independent_verification.jsonl` |
| **No silent deletes** | Do not remove or rewrite historical lines to “clean” the trail |
| **No silent overwrites** | A bad classification gets a **new** row; optional note that it supersedes an earlier id |
| **One JSON object per line** | Stable, grep-friendly, append-only |

---

## 2. Record roles

| Role | Typical level | When to use |
|------|---------------|-------------|
| **Binding technical verification** | **2** or **3** | Suites re-run; itemized `verifier_run_results`; this is the row audits should cite first |
| **Architecture-audit closure** | **1** often enough | Documents audit PASS; may reference the binding id instead of re-running everything |
| **Blocked / incomplete** | Any | Document-only review, missing execution access, or failed gates — **never** record PASS without required evidence |

**Rule:** Each closed phase should have **exactly one binding** technical row (Level 2+ when tests are the evidence). Extra Level 1 closure rows are optional and must **point at** the binding id in `notes`.

---

## 3. Required fields (binding PASS)

For a binding **PASS** record, include at least:

- `verification_id`, `timestamp`, `verifier`, `implementer`, `scope`
- `verification_level`, `risk_rationale`, `domains`
- `suites`, `result`, `evidence_type`
- `limitations` — **non-empty** (use `none material` only when truly none; empty string is invalid for Level 3 PASS)
- Level **2+**: `verifier_run_results` (itemized; include `"runner": "verifier"`)
- Level **3**: non-empty `execution_context`

**Do not** treat implementer console output alone as Level 2+ PASS evidence.

---

## 4. Level selection (short form)

| Situation | Guidance |
|-----------|----------|
| Pure docs / audit acceptance | Level **1** with explicit rationale |
| Docs + machine-checkable tests / packaging | Level **2** default |
| Crypto runtime, proof-on-path, or high-consequence authz-boundary change | Expect Level **2–3**; **do not** cite an old non-crypto Level 2 as a free pass |
| Ambiguity | **Escalate** (stronger level), never de-escalate without a new architectural decision |

Phase 3.0–3.2 packaging/definition work is **not** automatic Level 3 solely because future ZKP is high-risk.

| Situation | Guidance |
|-----------|----------|
| Gate 5/6 architecture + test re-execution | Level 2 binding rows as used; Gate 6 also has formal L3 evidence on record |
| Gate 7 protocol versioning / G7-CI | L2 `f39c9d4e2d9055d2` (90/90); L3 `276d3506496b78e2`; formal Gate 7 CLOSED / PASS |
| Stage 3.5 formal closure | Covers **Gates 5–7** only; see formal closure adjudication |
| Local/developer suite green | Not a substitute for Level 3 independence where Level 3 is required |

### Independence limitations (preserve; disclosure only)

Recorded Stage 3.5 / Gate 6–7 Level 3 work used **verifier-controlled local execution under Phase 2.9 I2**. It was **not** a separate CI account or multi-tenant verification farm. Implementer and verifier **roles** are distinct on the records; work occurred in the same organizational channel. Documentation updates do **not** remove these limitations.

### Scheme coverage (Gate 6)

Gate 6 substitution evidence used **mock** scheme adapters (including `mock-bn254-sfg16a` / `mock-digest-v2` as applicable). Do **not** claim production scheme interoperability or production cryptographic certification.

---

## 5. Supersede pattern

When a first attempt was wrong (e.g. Level 1 when Level 2 was required):

1. **Leave** the old row in the JSONL.  
2. Append a **new** row with the correct level and evidence.  
3. In `notes`, state clearly:  
   `Supersedes classification of <old_verification_id> for disposition.`

Do not edit the old row’s `result` to hide history.

---

## 6. “Corrected” audit documents and SHA custody

If an architecture audit file is republished as **Corrected** or **Final Verification**:

- Prefer **one** canonical filename under `docs/architecture/...`  
- Add a **one-line changelog** at the top *or* a sibling `*_CHANGELOG.md` / note in the milestone:  
  - What changed (clerical vs substantive)  
  - Whether disposition, verification id, or suite counts changed  

Leaving only a “Corrected” title with no prior draft or summary creates a **compliance Partial-Residual** on trail transparency (see Phase 3.2 compliance assessment).

### Gate 7 candidate SHA custody

| Role | SHA |
|------|-----|
| Originally recorded (historical; **not** a Git object) | `5f7523bf3865dce519ccd87a82fe897f665bd123` |
| Authoritative G7-CI implementation | `feedab71ab2ab0689b76e2492b25fc7283aa2283` |
| Parent Gate 7 candidate | `adeef37508214fe1522f5941ac67539f1acd52a3` |

Preserve both the original and authoritative values. Do **not** globally rewrite historical records. Chain-of-Correction: `docs/architecture/stage-3.5/gate-7-protocol-versioning/Gate_7_Chain_of_Correction_Note.md`.

---

## 7. Scope and naming

- `scope` should match the phase id pattern, e.g.  
  `phase-3.2-disaster-context-authority-and-responder-model`  
  `phase-3.5-gate-7-contract-integrity-seal-binding`
- `verifier` and `implementer` must be **distinct** strings for independent verification claims  
- Same human operating the machine is allowed operationally; the **roles** on the record must still differ for binding independent verification

---

## 8. Phase close checklist (trail)

- [ ] Binding Level 2+ row exists with itemized suite results  
- [ ] Arithmetic vs prior baseline stated in notes or audit (e.g. 93+7=100)  
- [ ] Limitations explicit (local venv, no crypto, deferred gates, etc.)  
- [ ] Optional Level 1 audit-closure row references binding id  
- [ ] Milestone cites binding `verification_id`  
- [ ] No PEMs / secrets in repo; verification log stays metadata-only  

---

## 9. Test-suite hygiene (C-6)

Some test runs can rewrite tracked JSON/JSONL evidence files under `dapp_api/` or workstream evidence paths.

**Operational precaution:**

- Prefer running verification suites in a **controlled working copy or archive** when you must avoid contaminating the tracked tree.  
- **Inspect** any generated changes to tracked evidence files before committing.  
- Do **not** commit incidental evidence-file rewrites unless they are intentional, reviewed append-only trail updates.

This is a process control; it does not change verification APIs or test semantics.

---

## 10. Related code and docs

| Item | Location |
|------|----------|
| Record API | `identity_runtime/independent_verification.py` |
| Levels / evidence gates | `identity_runtime/verification_levels.py` |
| Level 3 local policy (I2) | `identity_runtime/level3_environment_policy.py` |
| ZKP boundaries carry-forward | `docs/compliance/zkp-compliance-carry-forward.md` |
| Stage 3.5 formal closure | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Stage_3_5_Formal_Closure_Adjudication.md` |
| Gate 7 formal adjudication | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Gate_7_Formal_Adjudication.md` |
| Gate 7 Chain-of-Correction | `docs/architecture/stage-3.5/gate-7-protocol-versioning/Gate_7_Chain_of_Correction_Note.md` |
| G7-CI ADR | `docs/architecture/stage-3.5/gate-7-protocol-versioning/ADR-G7-Contract-Integrity-and-Seal-Binding.md` |

---

**Reminder:** These conventions support internal assurance discipline. They are not legal advice, regulatory certification, or a claim that any phase’s product is certified.