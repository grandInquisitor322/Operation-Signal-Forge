# Evidence package for Phase 2.7 Architecture Audit upgrade

The PARTIAL disposition is fair if the only artifact examined is the verification **record**. The implementation **does** exist; below is the Section 12 citation map so Workstreams 2–5 can move from VERIFY → PASS without inventing paths.

## Workstream 2 / H7 — Retention governance

| **Required** | **Citation** |
| --- | --- |
| Named policy / ownership artifact | identity_runtime/retention_governance.py |
| Approval authority | RETENTION_POLICY_OWNER = "IdentityAuditAdmin" |
| Change / purge authority | Scope identity_audit:admin (RETENTION_CHANGE_SCOPE, PURGE_AUTHORITY_SCOPE) |
| Mechanism not redesigned | mechanism_preserved: per_event_retention_in_audit_governance; still uses audit_governance.retention_policy() |
| Change ledger | record_retention_change() → dapp_api/retention_governance.json |
| Tests | test_retention_owner_named in test_phase27_assurance.py |

## Workstream 3 / H2 — Privileged audit self-auditing

| **Required** | **Citation** |
| --- | --- |
| Function | log_privileged_audit_action() in audit_governance.py |
| Wired on admin ops | purge_expired_file → operation="purge_expired_audit"; read_audit_authorized (admin) → operation="admin_read_audit" |
| Event type | privileged_audit_action on governed presentation-audit path (hash-chained) |
| Test | test_privileged_audit_self_auditing — asserts event present after purge |

## Workstream 4 / H3 — Adversarial isolation

| **Required** | **Citation** |
| --- | --- |
| Module | identity_runtime/tests/test_phase27_assurance.py |
| Credential / Matrix non-effect | test_recovery_does_not_mutate_credentials_or_scopes — asserts credentials_modified is False, authorization_scopes_granted is False; no TR/scope grant fields |
| Unauthorized recovery | test_recovery_cannot_act_without_approver_scope — authz={"scopes": ["capabilities:invoke"]} → insufficient_recovery_authority |
| Framing | Negative: prohibited authority path **rejected**; successful path asserts **absence of credential/authz side effects** |

## Workstream 5 / H4 — Tamper alert path

| **Required** | **Citation** |
| --- | --- |
| Module | identity_runtime/tamper_response.py |
| Trigger | **On-demand / callable** check_audit_integrity() (no in-repo cron/Slack) |
| Check | verify_chain on audit records |
| Alert path | dapp_api/tamper_alerts.jsonl (NOTIFICATION_PATH_SELECTED) |
| Also | Governed event audit_integrity_failure on failure |
| Test | test_tamper_detection_response — intact chain OK; tampered chain fails + alert file created |
| Not SIEM | Explicitly local JSONL only |

## New invariant — verification process ≠ audit-trail authority

| **Question** | **Finding** |
| --- | --- |
| Does record_verification write the G4 presentation audit store? | **No** — appends only dapp_api/independent_verification.jsonl |
| Does verifier role require identity_audit:admin? | **No** — H1 API is separate from audit ACL |
| Can a verifier wipe the hash-chain by verifying? | **No** — no call into purge_expired_file / audit append from H1 module |

**Status: PASS** for separation of verification records from G4 audit-trail authority.

## Workstream 1 rigor gap (honest)

The record’s limitations field is correct: first exercise accepted implementer console PASS + spot-check, not isolated re-execution. That remains a **process maturity** note, not a missing H7–H4 implementation. Closing it fully means a *future* verification with verifier-run suites—not blocking architecture existence of H2–H4.

## Suggested disposition upgrade

| **Workstream** | **Prior (record-only audit)** | **With this evidence map** |
| --- | --- | --- |
| H1 process existence | PASS | **PASS** |
| H1 re-execution rigor | PARTIAL | **PARTIAL** (disclosed; non-blocking for first use) |
| H7 | VERIFY | **PASS** |
| H2 | VERIFY | **PASS** |
| H3 | VERIFY | **PASS** |
| H4 | VERIFY | **PASS** |
| Invariants (cited paths) | VERIFY | **PASS** where evidenced above |
| **Overall** | PARTIAL | **ARCHITECTURE AUDIT — PASS** (with H1 rigor limitation noted) |
