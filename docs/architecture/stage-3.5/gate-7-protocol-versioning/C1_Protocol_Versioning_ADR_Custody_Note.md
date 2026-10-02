# C-1 Custody Note — ADR-G7 Protocol Versioning and Interoperability

**Type:** Documentation / chain-of-custody note only  
**Status:** RECORDED  
**Date:** 2026-10-02  
**Scope:** Does not reopen Gate 7 or Stage 3.5; does not invent ADR body text

---

## 1. Purpose

Stage 3.5 formal closure condition **C-1** requires governing architecture documents to be recoverable from the committed repository.

This note records that the following expected governing artifact was **not** found as a tracked file and could **not** be recovered from the operator’s available working sources during governance hygiene:

| Expected artifact | Status |
|-------------------|--------|
| `ADR-G7-Protocol-Versioning-and-Interoperability.md` | **Not present** on `origin/main`; **not recovered** from local search |

---

## 2. What *is* committed (related Gate 7 package)

| Artifact | Path |
|----------|------|
| Gate 7 formal adjudication | `Gate_7_Formal_Adjudication.md` |
| Stage 3.5 formal closure | `Stage_3_5_Formal_Closure_Adjudication.md` |
| Gate 7 Chain-of-Correction | `Gate_7_Chain_of_Correction_Note.md` |
| G7-CI ADR (contract integrity / seal binding) | `ADR-G7-Contract-Integrity-and-Seal-Binding.md` |
| G7-CI implementation plan | `Gate_7_Contract_Integrity_and_Seal_Binding_Implementation_Plan.md` |

The G7-CI ADR states that it **supplements** ADR-G7-Protocol-Versioning-and-Interoperability and must not silently redefine unrelated Gate 7 requirements.

---

## 3. How governing requirements are recovered today

PROTO-1 through PROTO-7 and related Gate 7 exit criteria, as used for formal closure, are available only as **quoted and applied** in:

- `Gate_7_Formal_Adjudication.md`
- `Stage_3_5_Formal_Closure_Adjudication.md`

That is a **custody limitation**: reviewers depend on adjudication text rather than a standalone committed PROTO ADR file.

---

## 4. Explicit non-actions

This note does **not**:

- Reconstruct or paraphrase a full Protocol-Versioning ADR body  
- Change Gate 7 or Stage 3.5 disposition (**CLOSED / PASS**)  
- Modify verification JSONL or implementation code  
- Satisfy C-1 for the missing ADR by substitution  

---

## 5. Owner follow-up (optional)

If an authentic original of `ADR-G7-Protocol-Versioning-and-Interoperability.md` is later found (chat export, backup, other clone):

1. Commit it under this directory with the established filename.  
2. Do not rewrite historical adjudication records.  
3. Optionally add a one-line pointer from this note that the ADR has been restored.

Until then, this note is the authoritative statement of the gap.

---

**C-1 residual for Protocol-Versioning ADR: DOCUMENTED AS NOT RECOVERED**