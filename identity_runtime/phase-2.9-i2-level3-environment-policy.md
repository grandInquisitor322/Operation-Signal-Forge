# Phase 2.9 — I2 Level 3 Verification Environment Policy

**Project:** Operation Signal Forge  
**Decision ID:** I2  
**Status:** Accepted  
**Date:** 2026-08-24  
**Predecessor:** Phase 2.8 (Closed; verification record `3bf6a9ce3fd54f22`)

## 1. Primary decision

**The verifier-controlled local Level 3 environment is the baseline.**  
**A separately provisioned Level 3 CI/lab environment is not required at this time and will not be built under Phase 2.9.**

Separate provisioning remains a **future escalation option**, not a current defect requiring closure.

## 2. Baseline Level 3 model (from Phase 2.8)

A Level 3 PASS requires all of the following:

1. Verifier functionally separate from the implementer  
2. Verifier-run suite results captured (`verifier_run_results`) — not implementer console alone  
3. Non-empty `execution_context`  
4. Explicit `limitations` (including the statement **"none material"** when none are known — empty field is not acceptable)  
5. Recorded `verification_level` and `risk_rationale`  
6. Records stored on the H1 path (`independent_verification.jsonl`), not the G4 audit trail  
7. Verifier may confirm or escalate level; may not de-escalate without a new architectural decision  

The local-execution limitation **must continue to be disclosed** in verification records. It must **not** be described as multi-tenant CI isolation.

## 3. Threat model & tradeoff record

| Threat class | Assessment | Phase 2.9 disposition |
|--------------|------------|------------------------|
| Environment contamination | Plausible; not demonstrated; verifier controls local env | Monitor; no new environment |
| Shared mistaken assumptions | Plausible assurance concern | Mitigate via independent evidence/reviewer controls |
| Implementation-environment compromise | Theoretical; no evidence of compromise | Not a current critical threat |
| Reproducibility drift | Plausible operational concern | Record execution context; reassess if frequency grows |
| False PASS from implementer-only output | Addressed by Level 2/3 evidence gates | **Closed** by H1 control |

## 4. Reassessment triggers (separate Level 3 provisioning)

Revisit I2 only if one or more of the following hold:

1. Operational threat model becomes materially more adversarial or higher-stakes  
2. Deployments where common-environment trust is a credible attack/assurance failure path  
3. Level 3 verification is frequent enough that environment standardization materially improves reproducibility  
4. External contractual, regulatory, partner, or assurance requirements demand separately provisioned verification  
5. Multiple phases show local Level 3 execution producing inconsistent or contested results  
6. Cost of independent provisioning falls such that assurance benefit clearly outweighs operational burden  

Any future phase that provisions separate isolation **must cite** one or more triggers (or a new ADR). Informal reversal of I2 is not permitted.

## 5. H6 — Holder recovery notification

**Disposition: DEFERRED.**  

No trustworthy out-of-band channel has been identified that reliably reaches the **legitimate holder** rather than the recovery initiator. H6 is not implemented under Phase 2.9.

## 6. Explicitly not in scope

G1 Shared NonceStore · G3 Central SIEM · G5 additional DID methods · G7 ZKP · ninth lifecycle step · reopening Phase 2.8 · identity/credential/TR/Matrix/Capability/Fusion redesign.

## 7. Classification

| Item | Classification |
|------|----------------|
| I2 decision formalization | Foundation / PRIMARY |
| Minimum Level 3 controls confirmation | Foundation |
| Reassessment triggers | Foundation |
| H6 disposition | Conditional / Deferred |
| Separate CI provisioning | Future-Deferred (escalation only) |