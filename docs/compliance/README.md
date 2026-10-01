# Compliance documentation

**Project:** Operation Signal Forge  
**Nature:** Technical compliance and assurance artifacts — **non-certifying** (not legal advice or regulatory certification)

This folder holds privacy/security-oriented project docs, phase **Compliance Impact Assessments**, and standing guardrails for future ZKP work.

---

## Start here (standing references)

| Doc | Purpose |
|-----|---------|
| [zkp-compliance-carry-forward.md](./zkp-compliance-carry-forward.md) | ZKP guardrails; Stage 3.5 CLOSED / PASS; D-3 and 3.6+ deferred |
| [verification-trail-conventions.md](./verification-trail-conventions.md) | How to write and interpret H1 records in `dapp_api/independent_verification.jsonl` |
| [post-zkp-integration-compliance-checklist.md](./post-zkp-integration-compliance-checklist.md) | Fill-later evidence checklist for Stage 3.6+ / proof-on-path work |
| [third-party-apis-and-licenses.md](./third-party-apis-and-licenses.md) | External services, licenses, attribution, and deployer obligations |

---

## Phase compliance impact assessments

Prefer these **assessment** filenames when citing a phase close:

| Phase | Assessment (canonical where present) |
|-------|--------------------------------------|
| 2.4 | `phase-2.4-compliance-impact-assessment.md.docx` |
| 2.5 | `Phase_2_5_Compliance_Impact_Assessment.docx` |
| 2.6 | `Phase 2.6 Compliance Impact Assessment.docx` |
| 2.7 | `Phase_2.7_Compliance_Impact_Assessment.docx` |
| 2.8 | `Google Gemini's Phase 2.8 Compliance Impact Assessment.docx` |
| 2.9 | `Google Gemini's Phase 2.9 COMPLIANCE IMPACT ASSESSMENT.docx` / `Phase 2.9 Compliance Review.docx` |
| 3.0 | `Phase_3.0_Compliance_Impact_Assessment.md` |
| 3.1 | `Phase_3_1_Compliance_Impact_Assessment.docx` / `Grok Phase 3.1 Compliance Impact Assessment.docx` |
| **3.2** | `Phase_3.2_Compliance_Impact_Assessment.md` |
| **3.3–3.4** | Architecture closed; cite stage packages under `docs/architecture/` |
| **3.5** | Formal closure: `../architecture/stage-3.5/gate-7-protocol-versioning/Stage_3_5_Formal_Closure_Adjudication.md` (Gates 5–7 CLOSED / PASS) |

Related architecture packages live under `docs/architecture/zkp/` and `docs/architecture/identity/`. Milestones live under `docs/milestones/`.

---

## Prompts vs assessments

| Kind | Example | Use |
|------|---------|-----|
| **Assessment** | `Phase_3.2_Compliance_Impact_Assessment.md` | Cite for phase disposition |
| **Prompt / worksheet** | `phase-3.2-compliance-impact-assessment.md` | Authoring input; not the closed assessment |

When both exist, the **`Phase_X.Y_Compliance_Impact_Assessment.*`** (or clearly titled “Compliance Impact Assessment”) is the citation target.

---

## Foundational compliance topics (pre-ZKP)

| Doc | Topic |
|-----|--------|
| [third-party-apis-and-licenses.md](./third-party-apis-and-licenses.md) | Third-party APIs, cloud, SDK licenses, attribution |
| `docs_compliance_privacy-and-data-handling.md.docx` | Privacy / data handling (convert to `.md` when convenient) |
| `docs_compliance_data-sources.md.docx` | Data sources (convert to `.md` when convenient) |
| `Compliance Review 7_29_26.docx` | Earlier overall review snapshot |

Legacy export (optional archive only; do not cite as canonical):

- `docs_compliance_third-party-apis-and-licenses.md_ (1).docx` or `_archive_third-party-apis-and-licenses.docx`

---

## Verification evidence (not in this folder)

| Artifact | Location |
|----------|----------|
| Independent verification log | `dapp_api/independent_verification.jsonl` |
| Level / evidence gates | `identity_runtime/verification_levels.py` |
| Record API | `identity_runtime/independent_verification.py` |
| I2 Level 3 environment policy | `docs/architecture/identity/phase-2.9-i2-level3-environment-policy.md` |

---

## Naming conventions (ongoing)

- Assessments: `Phase_<major>.<minor>_Compliance_Impact_Assessment.md` (or `.docx`)  
- Standing guardrails: lowercase kebab-case (e.g. `zkp-compliance-carry-forward.md`, `third-party-apis-and-licenses.md`)  
- Use **`docs/compliance/`** only — no top-level `Compliance\` folder for new canon  

---

## Out of scope for this index

- Claiming certification against named regulations  
- Completing the post-ZKP checklist before a proof exists on the path  
- Replacing architecture ADRs or phase milestones (those remain in `docs/architecture/` and `docs/milestones/`)