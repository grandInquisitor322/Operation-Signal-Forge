# Copyright 2026 Operation Signal Forge contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Phase 2.7 — assurance & governance hardening tests."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.audit_governance import (
    AUDIT_ADMIN_SCOPE,
    purge_expired_file,
)
from identity_runtime.did_resolver import LocalDidResolver
from identity_runtime.holder_keys import establish_identity
from identity_runtime.independent_verification import (
    ASSIGNMENT_MODEL,
    list_verifications,
    record_verification,
)
from identity_runtime.presentation_audit import log_event, read_audit_log
from identity_runtime.recovery_executor import RecoveryExecutor
from identity_runtime.recovery_policy import (
    RECOVERY_APPROVER_SCOPE,
    TRIGGER_KEYS_LOST,
)
from identity_runtime.retention_governance import (
    RETENTION_POLICY_OWNER,
    record_retention_change,
    retention_governance_summary,
)
from identity_runtime.tamper_response import (
    NOTIFICATION_PATH_SELECTED,
    check_audit_integrity,
)


class Phase27Tests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.audit = self.base / "audit.jsonl"
        self.store = self.base / "dids"
        self.store.mkdir()
        self.resolver = LocalDidResolver(self.store)

    def tearDown(self):
        self._tmp.cleanup()

    def test_independent_verification_record(self):
        self.assertEqual(ASSIGNMENT_MODEL["model"], "rotating_reviewer")
        path = self.base / "iv.jsonl"
        rec = record_verification(
            verifier="reviewer-a",
            implementer="author-b",
            scope="phase-2.7",
            suites=["test_phase26_audit_recovery"],
            result="PASS",
            evidence_type="independently_verified",
            verification_level=1,
            domains=["documentation"],
            risk_rationale="process_control_record_only",
            path=path,
        )
        self.assertEqual(rec["evidence_type"], "independently_verified")
        listed = list_verifications(path)
        self.assertEqual(len(listed), 1)

    def test_retention_owner_named(self):
        s = retention_governance_summary()
        self.assertEqual(s["policy_owner_role"], "IdentityAuditAdmin")
        self.assertEqual(RETENTION_POLICY_OWNER, "IdentityAuditAdmin")
        rec, err = record_retention_change(
            actor="admin",
            authz={"scopes": [AUDIT_ADMIN_SCOPE]},
            change_description="extend recovery retention",
            path=self.base / "ret.json",
        )
        self.assertIsNone(err)
        self.assertIsNotNone(rec)
        denied, err2 = record_retention_change(
            actor="nobody",
            authz={"scopes": []},
            change_description="x",
            path=self.base / "ret.json",
        )
        self.assertIsNone(denied)
        self.assertEqual(err2, "insufficient_audit_admin_authority")

    def test_privileged_audit_self_auditing(self):
        log_event("challenge_issued", path=self.audit, audience="t")
        purge_expired_file(
            self.audit,
            actor="admin",
            authz={"scopes": [AUDIT_ADMIN_SCOPE]},
        )
        recs = read_audit_log(self.audit, limit=50)
        ops = [r for r in recs if r.get("event") == "privileged_audit_action"]
        self.assertTrue(any(o.get("operation") == "purge_expired_audit" for o in ops))

    def test_recovery_does_not_mutate_credentials_or_scopes(self):
        ex = RecoveryExecutor(
            requests_path=self.base / "req.json", resolver=self.resolver
        )
        doc, _, mid = establish_identity(resolver=self.resolver)
        rec, err = ex.request_recovery(
            subject_did=doc["id"],
            trigger=TRIGGER_KEYS_LOST,
            requester="u",
            evidence_reference="e1",
        )
        self.assertIsNone(err)
        out, err2 = ex.approve_and_execute(
            rec["recovery_id"],
            actor="approver",
            authz={"scopes": ["identity_recovery:approver"]},
        )
        self.assertIsNone(err2)
        self.assertFalse(out["recovery"]["credentials_modified"])
        self.assertFalse(out["recovery"]["authorization_scopes_granted"])
        self.assertNotIn("trust_registry_modified", out["recovery"])
        self.assertNotIn("scopes_granted", out["recovery"])

    def test_recovery_cannot_act_without_approver_scope(self):
        ex = RecoveryExecutor(
            requests_path=self.base / "req.json", resolver=self.resolver
        )
        doc, _, _ = establish_identity(resolver=self.resolver)
        rec, _ = ex.request_recovery(
            subject_did=doc["id"],
            trigger=TRIGGER_KEYS_LOST,
            requester="u",
            evidence_reference="e1",
        )
        out, err = ex.approve_and_execute(
            rec["recovery_id"],
            actor="attacker",
            authz={"scopes": ["capabilities:invoke"]},
        )
        self.assertIsNone(out)
        self.assertEqual(err, "insufficient_recovery_authority")

    def test_tamper_detection_response(self):
        self.assertIn("tamper_alerts.jsonl", NOTIFICATION_PATH_SELECTED["path"])
        log_event("presentation_success", path=self.audit, subject_did="did:key:zX")
        ok_result = check_audit_integrity(
            audit_path=self.audit, alert_path=self.base / "alerts.jsonl"
        )
        self.assertTrue(ok_result["ok"])
        lines = self.audit.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[0])
        rec["reason"] = "tampered"
        self.audit.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        bad = check_audit_integrity(
            audit_path=self.audit, alert_path=self.base / "alerts.jsonl"
        )
        self.assertFalse(bad["ok"])
        self.assertTrue((self.base / "alerts.jsonl").exists())

    def test_single_approver_baseline(self):
        self.assertEqual(RECOVERY_APPROVER_SCOPE, "identity_recovery:approver")


if __name__ == "__main__":
    unittest.main()