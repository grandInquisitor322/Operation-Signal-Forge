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

"""Phase 2.3 Trust Registry governance tests."""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.credential_status import register_active
from identity_runtime.did_key import generate_keypair
from identity_runtime.envelope import sign_envelope
from identity_runtime.renewal import renew_credential
from identity_runtime.service import present_credential
from identity_runtime.trust_registry import (
    approve_issuer,
    issuer_allows_type,
    load_audit,
    propose_issuer,
    restore_issuer,
    revoke_issuer,
    suspend_issuer,
)


def _mint(priv, issuer_did, subject_did, ctype="HumanitarianAnalyst"):
    from identity_runtime.credential_status import new_credential_id

    now = datetime.now(timezone.utc)
    cred_id = new_credential_id()
    payload = {
        "id": cred_id,
        "type": "SignalForgeCredential",
        "issuer": issuer_did,
        "issuanceDate": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expirationDate": (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "credentialSubject": {
            "id": subject_did,
            "credentialType": ctype,
            "name": "T",
            "org": issuer_did,
            "credentialId": cred_id,
        },
    }
    env = sign_envelope(payload, priv, issuer_did)
    register_active(
        cred_id,
        issuer_did=issuer_did,
        subject_id=subject_did,
        credential_type=ctype,
    )
    return env


class TrustGovernanceTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.reg_path = base / "trust_registry.json"
        self.audit_path = base / "audit.jsonl"
        self.status_path = base / "credential_status.json"
        self.admins_path = base / "admins.json"

        self.reg_path.write_text("[]", encoding="utf-8")
        self.status_path.write_text('{"credentials":{}}', encoding="utf-8")
        self.admins_path.write_text(
            '{"admins":[{"id":"gov-admin"}]}', encoding="utf-8"
        )

        import identity_runtime.trust_registry as tr
        import identity_runtime.credential_status as cs

        self._tr = tr.DEFAULT_PATH
        self._ta = tr.AUDIT_PATH
        self._admins = tr.ADMINS_PATH
        self._cs = cs.DEFAULT_PATH

        tr.DEFAULT_PATH = self.reg_path
        tr.AUDIT_PATH = self.audit_path
        tr.ADMINS_PATH = self.admins_path
        cs.DEFAULT_PATH = self.status_path

        self.gov = "gov-admin"
        self.priv, self.issuer = generate_keypair()
        _, self.subject = generate_keypair()

    def tearDown(self):
        import identity_runtime.trust_registry as tr
        import identity_runtime.credential_status as cs

        tr.DEFAULT_PATH = self._tr
        tr.AUDIT_PATH = self._ta
        tr.ADMINS_PATH = self._admins
        cs.DEFAULT_PATH = self._cs
        self._tmp.cleanup()

    def test_untrusted_absent(self):
        ok, reason = issuer_allows_type(self.issuer, "HumanitarianAnalyst")
        self.assertFalse(ok)
        self.assertEqual(reason, "issuer_not_trusted")

    def test_propose_not_trusted(self):
        ok, msg, entry = propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        self.assertTrue(ok)
        self.assertEqual(entry["status"], "proposed")
        allowed, reason = issuer_allows_type(self.issuer, "HumanitarianAnalyst")
        self.assertFalse(allowed)
        self.assertEqual(reason, "issuer_proposed")

    def test_approve_scoped(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst", "ResearchPartner"],
            actor=self.gov,
        )
        ok, msg = approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
            governance_reference="GOV-1",
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "active")
        a1, _ = issuer_allows_type(self.issuer, "HumanitarianAnalyst")
        a2, r2 = issuer_allows_type(self.issuer, "ResearchPartner")
        self.assertTrue(a1)
        self.assertFalse(a2)
        self.assertEqual(r2, "issuer_type_not_allowed")

    def test_present_after_approve(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
        )
        env = _mint(self.priv, self.issuer, self.subject)
        authz, err = present_credential(env)
        self.assertIsNone(err)
        self.assertEqual(authz["role"], "HumanitarianAnalyst")

    def test_suspend_denies(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
        )
        env = _mint(self.priv, self.issuer, self.subject)
        suspend_issuer(self.issuer, actor=self.gov, reason="review")
        _, err = present_credential(env)
        self.assertEqual(err, "issuer_suspended")
        ok, _ = issuer_allows_type(self.issuer, "HumanitarianAnalyst")
        self.assertFalse(ok)

    def test_restore(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
        )
        suspend_issuer(self.issuer, actor=self.gov, reason="review")
        ok, msg = restore_issuer(self.issuer, actor=self.gov, reason="cleared")
        self.assertTrue(ok)
        self.assertEqual(msg, "active")
        env = _mint(self.priv, self.issuer, self.subject)
        _, err = present_credential(env)
        self.assertIsNone(err)

    def test_revoke_issuer(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
        )
        env = _mint(self.priv, self.issuer, self.subject)
        revoke_issuer(self.issuer, actor=self.gov, reason="policy")
        _, err = present_credential(env)
        self.assertEqual(err, "issuer_revoked")

    def test_renew_after_issuer_revoke(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
        )
        env = _mint(self.priv, self.issuer, self.subject)
        revoke_issuer(self.issuer, actor=self.gov, reason="policy")
        new_env, err, _ = renew_credential(
            env, issuer_private=self.priv, issuer_did=self.issuer, force=True
        )
        self.assertIsNone(new_env)
        self.assertEqual(err, "issuer_revoked")

    def test_emergency_suspend_audit(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
        )
        suspend_issuer(
            self.issuer, actor=self.gov, reason="key_compromise", emergency=True
        )
        audit = load_audit(self.audit_path)
        self.assertTrue(
            any(
                a.get("emergency") and a.get("action") == "emergency_suspend"
                for a in audit
            )
        )
        self.assertTrue(any(a.get("action") == "approve" for a in audit))
        self.assertTrue(any(a.get("action") == "propose" for a in audit))

    def test_approval_audit_fields(self):
        propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=self.gov,
        )
        approve_issuer(
            self.issuer,
            actor=self.gov,
            allowed_credential_types=["HumanitarianAnalyst"],
            governance_reference="MOU-42",
        )
        audit = load_audit(self.audit_path)
        ap = [a for a in audit if a.get("action") == "approve"][-1]
        self.assertEqual(ap["actor"], self.gov)
        self.assertEqual(ap["governance_reference"], "MOU-42")
        self.assertEqual(ap["previous_state"], "proposed")
        self.assertEqual(ap["resulting_state"], "active")

    def test_unauthorized_actor_denied(self):
        ok, msg, entry = propose_issuer(
            issuer_did=self.issuer,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor="random-user",
        )
        self.assertFalse(ok)
        self.assertEqual(msg, "insufficient_governance_authority")
        self.assertIsNone(entry)

    def test_authz_scope_grants_governance(self):
        """12th: TrustRegistryAdmin via authz scopes (not admin list)."""
        priv, issuer = generate_keypair()
        actor = "did:key:scope-admin-not-on-list"
        ok, msg, entry = propose_issuer(
            issuer_did=issuer,
            display_name="Scope Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor=actor,
            authz={
                "subject_id": actor,
                "role": "TrustRegistryAdmin",
                "scopes": ["trust_registry:admin"],
            },
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["status"], "proposed")
        allowed, reason = issuer_allows_type(issuer, "HumanitarianAnalyst")
        self.assertFalse(allowed)
        self.assertEqual(reason, "issuer_proposed")


if __name__ == "__main__":
    unittest.main()