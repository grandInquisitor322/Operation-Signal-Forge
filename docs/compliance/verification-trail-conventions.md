# Verification Trail Conventions

**Project:** Operation Signal Forge  
**Status:** Standing process note (H1 Independent Verification)  
**Aligned through:** Phase 3.5 Gate 7 Implementation Candidate  (formal Gate 7 adjudication OPEN; candidate SHA adeef37508214fe1522f5941ac67539f1acd52a3)
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

Stage 3.5 
| Gate 5/6 architecture + test re-execution | Level 2 binding rows as used; Gate 6 also has formal L3 evidence on record |
| Gate 7 protocol versioning / interoperability | Binding evidence should be Level 2+; formal close expects independent Level 3 against the frozen commit SHA |
| Local/developer suite green (e.g. L2 id cd6d80d1b6ab784b) | Not a substitute for Level 3 independence 
---

## 5. Supersede pattern

When a first attempt was wrong (e.g. Level 1 when Level 2 was required):

1. **Leave** the old row in the JSONL.  
2. Append a **new** row with the correct level and evidence.  
3. In `notes`, state clearly:  
   `Supersedes classification of <old_verification_id> for disposition.`

Do not edit the old row’s `result` to hide history.

---

## 6. “Corrected” audit documents

If an architecture audit file is republished as **Corrected** or **Final Verification**:

- Prefer **one** canonical filename under `docs/architecture/...`  
- Add a **one-line changelog** at the top *or* a sibling `*_CHANGELOG.md` / note in the milestone:  
  - What changed (clerical vs substantive)  
  - Whether disposition, verification id, or suite counts changed  

Leaving only a “Corrected” title with no prior draft or summary creates a **compliance Partial-Residual** on trail transparency (see Phase 3.2 compliance assessment).

---

## 7. Scope and naming

- `scope` should match the phase id pattern, e.g.  
  `phase-3.2-disaster-context-authority-and-responder-model`
- `verifier` and `implementer` must be **distinct** strings for independent verification claims  
- Same human operating the machine is allowed operationally; the **roles** on the record must still differ for binding independent verification
- phase-3.5-gate-7-protocol-versioning

---

## 8. Phase close checklist (trail)

- [ ] Binding Level 2+ row exists with itemized suite results  
- [ ] Arithmetic vs prior baseline stated in notes or audit (e.g. 93+7=100)  
- [ ] Limitations explicit (local venv, no crypto, deferred gates, etc.)  
- [ ] Optional Level 1 audit-closure row references binding id  
- [ ] Milestone cites binding `verification_id`  
- [ ] No PEMs / secrets in repo; verification log stays metadata-only  

---

## 9. Related code and docs

| Item | Location |
|------|----------|
| Record API | `identity_runtime/independent_verification.py` |
| Levels / evidence gates | `identity_runtime/verification_levels.py` |
| Level 3 local policy (I2) | `identity_runtime/level3_environment_policy.py` |
| ZKP boundaries carry-forward | `docs/compliance/zkp-compliance-carry-forward.md` |

---

**Reminder:** These conventions support internal assurance discipline. They are not legal advice, regulatory certification, or a claim that any phase’s product is certified.