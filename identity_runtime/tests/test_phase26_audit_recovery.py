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

"""Phase 2.6 G4 audit governance + G2 recovery executor tests."""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.audit_governance import (
    TAMPER_EVIDENCE_DESIGN,
    actor_may_read_audit,
    filter_expired,
    read_audit_authorized,
    verify_chain,
)
from identity_runtime.did_resolver import LocalDidResolver
from identity_runtime.holder_keys import establish_identity
from identity_runtime.presentation_audit import log_event, read_audit_log
from identity_runtime.recovery_executor import RecoveryExecutor
from identity_runtime.recovery_policy import TRIGGER_KEYS_LOST


class Phase26Tests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.audit_path = self.base / "audit.jsonl"
        self.store = self.base / "did_store"
        self.store.mkdir()
        self.resolver = LocalDidResolver(self.store)

    def tearDown(self):
        self._tmp.cleanup()

    def test_tamper_design_recorded(self):
        self.assertEqual(TAMPER_EVIDENCE_DESIGN["mechanism"], "hash_chained_jsonl")
        self.assertFalse(TAMPER_EVIDENCE_DESIGN["external_service_required"])
        self.assertFalse(TAMPER_EVIDENCE_DESIGN["retains_reusable_auth_material"])

    def test_hash_chain_and_detect_tamper(self):
        log_event("presentation_success", path=self.audit_path, subject_did="did:key:zA")
        log_event("presentation_failure", path=self.audit_path, reason="x")
        recs = read_audit_log(self.audit_path, limit=50)
        ok, reason = verify_chain(recs)
        self.assertTrue(ok, reason)
        recs[0]["reason"] = "mutated"
        ok2, _ = verify_chain(recs)
        self.assertFalse(ok2)

    def test_audit_access_denied(self):
        ok, reason = actor_may_read_audit("nobody")
        self.assertFalse(ok)
        self.assertEqual(reason, "insufficient_audit_authority")
        recs, err = read_audit_authorized(
            self.audit_path, actor="nobody", authz={"scopes": []}
        )
        self.assertIsNone(recs)
        self.assertEqual(err, "insufficient_audit_authority")

    def test_audit_access_allowed(self):
        log_event("challenge_issued", path=self.audit_path, audience="a")
        recs, err = read_audit_authorized(
            self.audit_path,
            actor="auditor",
            authz={"scopes": ["identity_audit:read"]},
        )
        self.assertIsNone(err)
        self.assertTrue(len(recs) >= 1)

    def test_retention_filter(self):
        old = {
            "event": "challenge_issued",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=400)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
        new = {
            "event": "challenge_issued",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        kept, purged = filter_expired([old, new])
        self.assertEqual(purged, 1)
        self.assertEqual(len(kept), 1)

    def test_recovery_unauthorized(self):
        ex = RecoveryExecutor(
            requests_path=self.base / "req.json", resolver=self.resolver
        )
        doc, _, _ = establish_identity(resolver=self.resolver)
        rec, err = ex.request_recovery(
            subject_did=doc["id"],
            trigger=TRIGGER_KEYS_LOST,
            requester="user-1",
            evidence_reference="t1",
        )
        self.assertIsNone(err)
        out, err2 = ex.approve_and_execute(
            rec["recovery_id"], actor="random", authz={"scopes": []}
        )
        self.assertIsNone(out)
        self.assertEqual(err2, "insufficient_recovery_authority")

    def test_recovery_authorized_rotates_keys(self):
        ex = RecoveryExecutor(
            requests_path=self.base / "req.json", resolver=self.resolver
        )
        doc, _, mid = establish_identity(resolver=self.resolver)
        rec, err = ex.request_recovery(
            subject_did=doc["id"],
            trigger=TRIGGER_KEYS_LOST,
            requester="user-1",
            evidence_reference="t1",
        )
        self.assertIsNone(err)
        out, err2 = ex.approve_and_execute(
            rec["recovery_id"],
            actor="approver",
            authz={"scopes": ["identity_recovery:approver"]},
            governance_reference="IR-1",
        )
        self.assertIsNone(err2, err2)
        self.assertFalse(out["recovery"]["credentials_modified"])
        self.assertFalse(out["recovery"]["authorization_scopes_granted"])
        self.assertNotEqual(out["method_activated"], mid)
        updated, e = self.resolver.resolve(doc["id"])
        self.assertIsNone(e)
        old = next(v for v in updated["verificationMethod"] if v["id"] == mid)
        self.assertEqual(old["status"], "retired")


if __name__ == "__main__":
    unittest.main()