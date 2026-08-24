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

"""Phase 2.5 recovery policy tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.recovery_policy import (
    TRIGGER_KEYS_COMPROMISED,
    TRIGGER_KEYS_LOST,
    actor_may_approve_recovery,
    build_recovery_request,
    get_recovery_service,
    recovery_boundary_statement,
)


class RecoveryPolicyTests(unittest.TestCase):
    def test_boundary_statement(self):
        s = recovery_boundary_statement()
        self.assertIn("does not renew", s)
        self.assertIn("Authorization Matrix", s)

    def test_build_request(self):
        rec, err = build_recovery_request(
            subject_did="did:key:z6Mkabc",
            trigger=TRIGGER_KEYS_LOST,
            requester="user-1",
            evidence_reference="ticket-9",
        )
        self.assertIsNone(err)
        self.assertEqual(rec["status"], "requested")
        self.assertFalse(rec["impact_policy"]["reissue_credentials"])
        self.assertFalse(rec["impact_policy"]["grant_authorization_scopes"])

    def test_compromise_impact(self):
        rec, err = build_recovery_request(
            subject_did="did:key:z6Mkabc",
            trigger=TRIGGER_KEYS_COMPROMISED,
            requester="user-1",
            evidence_reference="sec-1",
            compromise_summary="device theft",
        )
        self.assertIsNone(err)
        self.assertTrue(rec["impact_policy"]["retire_prior_authentication_methods"])
        self.assertFalse(rec["impact_policy"]["reissue_credentials"])

    def test_invalid_trigger(self):
        rec, err = build_recovery_request(
            subject_did="did:key:z6Mkabc",
            trigger="magic",
            requester="user-1",
        )
        self.assertIsNone(rec)
        self.assertEqual(err, "invalid_recovery_trigger")

    def test_approver_scope(self):
        ok, reason = actor_may_approve_recovery(
            "did:key:zApprover",
            authz={
                "subject_id": "did:key:zApprover",
                "scopes": ["identity_recovery:approver"],
            },
        )
        self.assertTrue(ok, reason)

    def test_approver_denied(self):
        ok, reason = actor_may_approve_recovery("random-user")
        self.assertFalse(ok)
        self.assertEqual(reason, "insufficient_recovery_authority")

    def test_service_not_implemented(self):
        svc = get_recovery_service()
        with self.assertRaises(NotImplementedError):
            svc.request_recovery()


if __name__ == "__main__":
    unittest.main()