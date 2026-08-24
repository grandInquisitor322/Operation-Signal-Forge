"""Phase 2.2 renewal & rotation tests + regression of present pipeline."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.credential_status import register_active, revoke
from identity_runtime.did_key import generate_keypair
from identity_runtime.envelope import sign_envelope
from identity_runtime.renewal import renew_credential, rotate_credential
from identity_runtime.service import present_credential


def _issuer():
    priv, did = generate_keypair()
    return priv, did


def _ensure_issuer_in_registry(issuer_did: str, path: Path):
    reg = []
    if path.exists():
        reg = json.loads(path.read_text(encoding="utf-8-sig"))
    reg = [e for e in reg if e.get("issuer_did") != issuer_did]
    reg.append(
        {
            "issuer_did": issuer_did,
            "display_name": "Test Issuer",
            "status": "active",
            "allowed_credential_types": [
                "HumanitarianAnalyst",
                "ResearchPartner",
            ],
            "revocation_method": "status_list",
            "effective_from": "2026-01-01",
        }
    )
    path.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def _mint(priv, issuer_did, subject_did, ctype="HumanitarianAnalyst", days=365, exp=None):
    from identity_runtime.credential_status import new_credential_id

    now = datetime.now(timezone.utc)
    cred_id = new_credential_id()
    if exp is None:
        exp = (now + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "id": cred_id,
        "type": "SignalForgeCredential",
        "issuer": issuer_did,
        "issuanceDate": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expirationDate": exp,
        "credentialSubject": {
            "id": subject_did,
            "credentialType": ctype,
            "name": "Test User",
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


class RenewalRotationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.status_path = Path(self._tmp.name) / "credential_status.json"
        self.reg_path = Path(self._tmp.name) / "trust_registry.json"

        import identity_runtime.credential_status as cs
        import identity_runtime.trust_registry as tr

        self._cs_default = cs.DEFAULT_PATH
        self._tr_default = tr.DEFAULT_PATH
        cs.DEFAULT_PATH = self.status_path
        tr.DEFAULT_PATH = self.reg_path
        self.status_path.write_text('{"credentials":{}}', encoding="utf-8")
        self.reg_path.write_text("[]", encoding="utf-8")

        self.priv, self.issuer = _issuer()
        _ensure_issuer_in_registry(self.issuer, self.reg_path)
        _, self.subject = generate_keypair()

    def tearDown(self):
        import identity_runtime.credential_status as cs
        import identity_runtime.trust_registry as tr

        cs.DEFAULT_PATH = self._cs_default
        tr.DEFAULT_PATH = self._tr_default
        self._tmp.cleanup()

    def test_present_active(self):
        env = _mint(self.priv, self.issuer, self.subject)
        authz, err = present_credential(env)
        self.assertIsNone(err)
        self.assertEqual(authz["role"], "HumanitarianAnalyst")
        self.assertIn("capabilities:invoke:investigate", authz["scopes"])

    def test_expired_denied(self):
        exp = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        env = _mint(self.priv, self.issuer, self.subject, exp=exp)
        authz, err = present_credential(env)
        self.assertEqual(err, "credential_expired")
        self.assertIsNone(authz)

    def test_revoked_denied(self):
        env = _mint(self.priv, self.issuer, self.subject)
        revoke(env["id"], reason="test")
        authz, err = present_credential(env)
        self.assertEqual(err, "credential_revoked")

    def test_renewal_near_expiry(self):
        exp = (datetime.now(timezone.utc) + timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        old = _mint(self.priv, self.issuer, self.subject, exp=exp)
        new_env, err, info = renew_credential(
            old,
            issuer_private=self.priv,
            issuer_did=self.issuer,
            days_valid=365,
            renewal_window_days=30,
        )
        self.assertIsNone(err, err)
        self.assertNotEqual(new_env["id"], old["id"])
        authz, err2 = present_credential(new_env)
        self.assertIsNone(err2)
        self.assertEqual(authz["role"], "HumanitarianAnalyst")
        authz_a, err_a = present_credential(old)
        self.assertIsNone(err_a)

    def test_renewal_not_in_window(self):
        exp = (datetime.now(timezone.utc) + timedelta(days=200)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        old = _mint(self.priv, self.issuer, self.subject, exp=exp)
        new_env, err, _ = renew_credential(
            old,
            issuer_private=self.priv,
            issuer_did=self.issuer,
            renewal_window_days=30,
        )
        self.assertEqual(err, "not_in_renewal_window")
        self.assertIsNone(new_env)

    def test_renewal_force(self):
        exp = (datetime.now(timezone.utc) + timedelta(days=200)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        old = _mint(self.priv, self.issuer, self.subject, exp=exp)
        new_env, err, _ = renew_credential(
            old,
            issuer_private=self.priv,
            issuer_did=self.issuer,
            force=True,
        )
        self.assertIsNone(err)
        self.assertIsNotNone(new_env)

    def test_authorization_continuity(self):
        exp = (datetime.now(timezone.utc) + timedelta(days=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        old = _mint(self.priv, self.issuer, self.subject, exp=exp)
        a1, _ = present_credential(old)
        new_env, err, _ = renew_credential(
            old, issuer_private=self.priv, issuer_did=self.issuer, force=True
        )
        self.assertIsNone(err)
        a2, _ = present_credential(new_env)
        self.assertEqual(a1["scopes"], a2["scopes"])
        self.assertEqual(a1["role"], a2["role"])

    def test_revoked_cannot_renew(self):
        old = _mint(self.priv, self.issuer, self.subject)
        revoke(old["id"], reason="compromised")
        new_env, err, _ = renew_credential(
            old, issuer_private=self.priv, issuer_did=self.issuer, force=True
        )
        self.assertEqual(err, "credential_revoked")
        self.assertIsNone(new_env)

    def test_rotate_revokes_old(self):
        old = _mint(self.priv, self.issuer, self.subject)
        new_env, err, info = rotate_credential(
            old,
            issuer_private=self.priv,
            issuer_did=self.issuer,
            revoke_old=True,
        )
        self.assertIsNone(err)
        _, err_old = present_credential(old)
        self.assertEqual(err_old, "credential_revoked")
        authz, err_new = present_credential(new_env)
        self.assertIsNone(err_new)
        self.assertEqual(authz["role"], "HumanitarianAnalyst")

    def test_rotate_after_compromise(self):
        old = _mint(self.priv, self.issuer, self.subject)
        revoke(old["id"], reason="compromised")
        _, sub2 = generate_keypair()
        new_env, err, info = rotate_credential(
            old,
            issuer_private=self.priv,
            issuer_did=self.issuer,
            new_subject_id=sub2,
            revoke_old=True,
        )
        self.assertIsNone(err)
        authz, err2 = present_credential(new_env)
        self.assertIsNone(err2)
        self.assertEqual(authz["subject_id"], sub2)

    def test_untrusted_issuer_cannot_renew(self):
        old = _mint(self.priv, self.issuer, self.subject)
        other_priv, other_did = generate_keypair()
        new_env, err, _ = renew_credential(
            old,
            issuer_private=other_priv,
            issuer_did=other_did,
            force=True,
        )
        self.assertIsNotNone(err)
        self.assertIsNone(new_env)

    def test_old_after_renewal_still_expires(self):
        exp = (datetime.now(timezone.utc) + timedelta(days=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        old = _mint(self.priv, self.issuer, self.subject, exp=exp)
        new_env, err, _ = renew_credential(
            old, issuer_private=self.priv, issuer_did=self.issuer, force=True
        )
        self.assertIsNone(err)
        self.assertEqual(old["expirationDate"], exp)
        exp2 = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        expired = _mint(self.priv, self.issuer, self.subject, exp=exp2)
        _, err_e = present_credential(expired)
        self.assertEqual(err_e, "credential_expired")
        _, err_b = present_credential(new_env)
        self.assertIsNone(err_b)


if __name__ == "__main__":
    unittest.main()