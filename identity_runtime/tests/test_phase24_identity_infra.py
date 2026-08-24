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

"""Phase 2.4 Identity Infrastructure Foundations tests."""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from identity_runtime.credential_status import register_active
from identity_runtime.did_document import (
    create_did_document,
    make_verification_method,
    validate_did_document,
)
from identity_runtime.did_key import generate_keypair
from identity_runtime.did_resolver import LocalDidResolver
from identity_runtime.envelope import sign_envelope
from identity_runtime.holder_keys import establish_identity, rotate_holder_key
from identity_runtime.identity_types import (
    membership,
    organization,
    person,
    role,
    validate_identity_record,
)
from identity_runtime.presentation import (
    clear_nonce_store,
    create_possession_proof,
    issue_challenge,
    verify_subject_binding,
)
from identity_runtime.service import present_credential
from identity_runtime.trust_registry import approve_issuer, propose_issuer


class Phase24Tests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = Path(self._tmp.name) / "did_store"
        self.store.mkdir()
        self.resolver = LocalDidResolver(self.store)
        clear_nonce_store()

        import identity_runtime.trust_registry as tr
        import identity_runtime.credential_status as cs
        import identity_runtime.did_resolver as dr

        self._tr = tr.DEFAULT_PATH
        self._ta = tr.AUDIT_PATH
        self._admins = tr.ADMINS_PATH
        self._cs = cs.DEFAULT_PATH
        self._res = dr.get_resolver()

        tr.DEFAULT_PATH = Path(self._tmp.name) / "reg.json"
        tr.AUDIT_PATH = Path(self._tmp.name) / "audit.jsonl"
        tr.ADMINS_PATH = Path(self._tmp.name) / "admins.json"
        tr.DEFAULT_PATH.write_text("[]", encoding="utf-8")
        tr.ADMINS_PATH.write_text('{"admins":[{"id":"gov-admin"}]}', encoding="utf-8")
        cs.DEFAULT_PATH = Path(self._tmp.name) / "status.json"
        cs.DEFAULT_PATH.write_text('{"credentials":{}}', encoding="utf-8")
        dr.set_resolver(self.resolver)

    def tearDown(self):
        import identity_runtime.trust_registry as tr
        import identity_runtime.credential_status as cs
        import identity_runtime.did_resolver as dr

        tr.DEFAULT_PATH = self._tr
        tr.AUDIT_PATH = self._ta
        tr.ADMINS_PATH = self._admins
        cs.DEFAULT_PATH = self._cs
        dr.set_resolver(self._res)
        clear_nonce_store()
        self._tmp.cleanup()

    def test_did_document_create_and_validate(self):
        _, did = generate_keypair()
        mb = did[len("did:key:") :]
        vm = make_verification_method(did=did, key_id="key-1", public_key_multibase=mb)
        doc = create_did_document(did, verification_methods=[vm])
        ok, reason = validate_did_document(doc)
        self.assertTrue(ok, reason)
        self.assertIn(vm["id"], doc["authentication"])

    def test_auth_must_reference_known_method(self):
        _, did = generate_keypair()
        mb = did[len("did:key:") :]
        vm = make_verification_method(did=did, key_id="key-1", public_key_multibase=mb)
        with self.assertRaises(Exception):
            create_did_document(
                did,
                verification_methods=[vm],
                authentication=[f"{did}#nope"],
            )

    def test_invalid_did_document(self):
        ok, reason = validate_did_document({"id": "not-a-did"})
        self.assertFalse(ok)

    def test_resolve_known(self):
        doc, _, _ = establish_identity(resolver=self.resolver)
        got, err = self.resolver.resolve(doc["id"])
        self.assertIsNone(err)
        self.assertEqual(got["id"], doc["id"])

    def test_resolve_unknown(self):
        got, err = self.resolver.resolve(
            "did:key:z6MkUnknown000000000000000000000000"
        )
        self.assertIsNone(got)
        self.assertEqual(err, "did_not_found")

    def test_malformed_document(self):
        did = "did:key:z6MkBadMalform0000000001"
        p = self.resolver.path_for(did)
        p.write_text("{not json", encoding="utf-8")
        got, err = self.resolver.resolve(did)
        self.assertIsNone(got)
        self.assertEqual(err, "malformed_did_document")

    def test_holder_key_rotation(self):
        doc, _, mid_old = establish_identity(resolver=self.resolver)
        did = doc["id"]
        updated, _, mid_new, retired = rotate_holder_key(
            did, resolver=self.resolver
        )
        self.assertEqual(updated["id"], did)
        self.assertEqual(retired, mid_old)
        self.assertEqual(updated["authentication"], [mid_new])
        old_vm = next(v for v in updated["verificationMethod"] if v["id"] == mid_old)
        self.assertEqual(old_vm["status"], "retired")
        new_vm = next(v for v in updated["verificationMethod"] if v["id"] == mid_new)
        self.assertEqual(new_vm["status"], "active")

    def _issue_vc_for_subject(self, issuer_priv, issuer_did, subject_did):
        from identity_runtime.credential_status import new_credential_id

        propose_issuer(
            issuer_did=issuer_did,
            display_name="Org",
            requested_credential_types=["HumanitarianAnalyst"],
            actor="gov-admin",
        )
        approve_issuer(
            issuer_did,
            actor="gov-admin",
            allowed_credential_types=["HumanitarianAnalyst"],
        )
        now = datetime.now(timezone.utc)
        cid = new_credential_id()
        payload = {
            "id": cid,
            "type": "SignalForgeCredential",
            "issuer": issuer_did,
            "issuanceDate": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expirationDate": (now + timedelta(days=30)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "credentialSubject": {
                "id": subject_did,
                "credentialType": "HumanitarianAnalyst",
                "name": "T",
                "org": issuer_did,
                "credentialId": cid,
            },
        }
        env = sign_envelope(payload, issuer_priv, issuer_did)
        register_active(
            cid,
            issuer_did=issuer_did,
            subject_id=subject_did,
            credential_type="HumanitarianAnalyst",
        )
        return env

    def test_valid_possession_proof(self):
        doc, sub_priv, mid = establish_identity(resolver=self.resolver)
        issuer_priv, issuer_did = generate_keypair()
        env = self._issue_vc_for_subject(issuer_priv, issuer_did, doc["id"])
        ch = issue_challenge(audience="signal-forge-dapp")
        proof = create_possession_proof(
            subject_private=sub_priv,
            subject_did=doc["id"],
            verification_method_id=mid,
            credential_id=env["id"],
            challenge=ch,
        )
        ok, reason = verify_subject_binding(
            credential=env, proof=proof, challenge=ch, require_binding=True
        )
        self.assertTrue(ok, reason)

    def test_replay_rejected(self):
        doc, sub_priv, mid = establish_identity(resolver=self.resolver)
        issuer_priv, issuer_did = generate_keypair()
        env = self._issue_vc_for_subject(issuer_priv, issuer_did, doc["id"])
        ch = issue_challenge(audience="sf")
        proof = create_possession_proof(
            subject_private=sub_priv,
            subject_did=doc["id"],
            verification_method_id=mid,
            credential_id=env["id"],
            challenge=ch,
        )
        ok1, _ = verify_subject_binding(
            credential=env, proof=proof, challenge=ch, require_binding=True
        )
        self.assertTrue(ok1)
        ok2, reason = verify_subject_binding(
            credential=env, proof=proof, challenge=ch, require_binding=True
        )
        self.assertFalse(ok2)
        self.assertEqual(reason, "replay_detected")

    def test_retired_key_rejected(self):
        doc, sub_priv, mid = establish_identity(resolver=self.resolver)
        issuer_priv, issuer_did = generate_keypair()
        env = self._issue_vc_for_subject(issuer_priv, issuer_did, doc["id"])
        ch = issue_challenge(audience="sf")
        proof = create_possession_proof(
            subject_private=sub_priv,
            subject_did=doc["id"],
            verification_method_id=mid,
            credential_id=env["id"],
            challenge=ch,
        )
        rotate_holder_key(doc["id"], resolver=self.resolver)
        ok, reason = verify_subject_binding(
            credential=env, proof=proof, challenge=ch, require_binding=True
        )
        self.assertFalse(ok)
        self.assertIn(
            reason,
            (
                "verification_method_not_authentication_capable",
                "verification_method_retired",
            ),
        )

    def test_missing_proof_when_required(self):
        doc, _, _ = establish_identity(resolver=self.resolver)
        issuer_priv, issuer_did = generate_keypair()
        env = self._issue_vc_for_subject(issuer_priv, issuer_did, doc["id"])
        ok, reason = verify_subject_binding(
            credential=env, proof=None, require_binding=True
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "missing_subject_binding_proof")

    def test_present_without_binding_still_works(self):
        """Default present path unchanged (2.1–2.3 regression)."""
        doc, _, _ = establish_identity(resolver=self.resolver)
        issuer_priv, issuer_did = generate_keypair()
        env = self._issue_vc_for_subject(issuer_priv, issuer_did, doc["id"])
        authz, err = present_credential(env)
        self.assertIsNone(err)
        self.assertEqual(authz["role"], "HumanitarianAnalyst")

    def test_person_org_role(self):
        p = person(did="did:key:zPerson", name="Alex")
        o = organization(did="did:key:zOrg", name="NGO")
        r = role(role_id="analyst", name="Analyst", organization_did=o["did"])
        m = membership(
            person_did=p["did"], organization_did=o["did"], role_id=r["roleId"]
        )
        self.assertTrue(validate_identity_record(p)[0])
        self.assertTrue(validate_identity_record(o)[0])
        self.assertTrue(validate_identity_record(r)[0])
        self.assertTrue(validate_identity_record(m)[0])
        bad = membership(person_did="did:same", organization_did="did:same")
        self.assertFalse(validate_identity_record(bad)[0])


if __name__ == "__main__":
    unittest.main()