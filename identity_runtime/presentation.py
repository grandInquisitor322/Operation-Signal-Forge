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

"""
Subject binding + replay-resistant presentation helpers (Phase 2.4 / 2.5).

Proof-of-possession of the subject DID's active authentication key.
Replay protection via durable NonceStore (Phase 2.5).
Audit metadata via presentation_audit (no reusable auth material).

Does not use ZKP. Does not redefine credential lifecycle.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from identity_runtime.did_document import is_authentication_capable
from identity_runtime.did_key import b64u_decode, b64u_encode, did_key_to_public_key
from identity_runtime.did_resolver import resolve
from identity_runtime.nonce_store import get_nonce_store


def clear_nonce_store() -> None:
    """API compatibility for tests; inject a temp store via set_nonce_store."""
    pass


def issue_challenge(
    *,
    audience: str,
    ttl_seconds: int = 300,
) -> dict[str, Any]:
    """Issue a challenge; nonce is recorded as pending in NonceStore."""
    ch = get_nonce_store().issue(audience=audience, ttl_seconds=ttl_seconds)
    try:
        from identity_runtime.presentation_audit import log_challenge_issued

        log_challenge_issued(
            audience=audience,
            expires_at=ch.get("expiresAt") or "",
            nonce=ch.get("nonce") or "",
        )
    except Exception:
        pass
    return ch


def _canonical_binding_payload(
    *,
    subject_did: str,
    credential_id: str,
    nonce: str,
    audience: str,
) -> bytes:
    body = {
        "audience": audience,
        "credentialId": credential_id,
        "nonce": nonce,
        "subject": subject_did,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def create_possession_proof(
    *,
    subject_private: Ed25519PrivateKey,
    subject_did: str,
    verification_method_id: str,
    credential_id: str,
    challenge: dict[str, Any],
) -> dict[str, Any]:
    nonce = challenge["nonce"]
    audience = challenge["audience"]
    msg = _canonical_binding_payload(
        subject_did=subject_did,
        credential_id=credential_id,
        nonce=nonce,
        audience=audience,
    )
    sig = subject_private.sign(msg)
    return {
        "type": "Ed25519SubjectBinding2026",
        "verificationMethod": verification_method_id,
        "nonce": nonce,
        "audience": audience,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signature": b64u_encode(sig),
    }


def verify_subject_binding(
    *,
    credential: dict[str, Any],
    proof: Optional[dict[str, Any]],
    challenge: Optional[dict[str, Any]] = None,
    require_binding: bool = True,
) -> tuple[bool, str]:
    """
    Verify presenter controls credential subject DID.
    Nonce consumption runs only after cryptographic verification succeeds.
    """
    subject = (credential.get("credentialSubject") or {}).get("id") or (
        credential.get("credentialSubject") or {}
    ).get("did") or ""
    credential_id = credential.get("id") or ""
    issuer_did = credential.get("issuer") or ""

    if not proof:
        if require_binding:
            try:
                from identity_runtime.presentation_audit import log_presentation_result

                log_presentation_result(
                    success=False,
                    reason="missing_subject_binding_proof",
                    credential_id=credential_id,
                    subject_did=subject,
                    issuer_did=issuer_did,
                )
            except Exception:
                pass
            return False, "missing_subject_binding_proof"
        return True, "binding_not_required"

    if not subject:
        return False, "missing_subject_did"

    nonce = proof.get("nonce")
    audience = proof.get("audience")
    if not nonce or not audience:
        return False, "incomplete_binding_proof"

    if challenge:
        if challenge.get("nonce") != nonce:
            return False, "nonce_mismatch"
        if challenge.get("audience") != audience:
            return False, "audience_mismatch"

    vm_id = proof.get("verificationMethod")
    if not vm_id:
        return False, "missing_verification_method"

    doc, err = resolve(subject)
    if err or not doc:
        return False, err or "subject_did_unresolved"

    if not is_authentication_capable(doc, vm_id):
        return False, "verification_method_not_authentication_capable"

    vm = None
    for m in doc.get("verificationMethod") or []:
        if m.get("id") == vm_id:
            vm = m
            break
    if not vm:
        return False, "verification_method_not_found"
    if (vm.get("status") or "active") != "active":
        return False, "verification_method_retired"

    mb = vm.get("publicKeyMultibase") or ""
    try:
        if subject.startswith("did:key:"):
            public = did_key_to_public_key(subject)
            if mb:
                try:
                    public = did_key_to_public_key("did:key:" + mb)
                except Exception:
                    public = did_key_to_public_key(subject)
        else:
            public = did_key_to_public_key("did:key:" + mb)
    except Exception as e:
        return False, f"public_key_resolve_failed:{e}"

    msg = _canonical_binding_payload(
        subject_did=subject,
        credential_id=credential_id,
        nonce=nonce,
        audience=audience,
    )
    try:
        public.verify(b64u_decode(proof["signature"]), msg)
    except Exception:
        try:
            from identity_runtime.presentation_audit import log_presentation_result

            log_presentation_result(
                success=False,
                reason="invalid_subject_binding_signature",
                credential_id=credential_id,
                subject_did=subject,
                issuer_did=issuer_did,
                verification_method_id=vm_id or "",
            )
        except Exception:
            pass
        return False, "invalid_subject_binding_signature"

    ok, reason = get_nonce_store().consume(nonce, audience=audience)
    if not ok:
        try:
            from identity_runtime.presentation_audit import log_presentation_result

            log_presentation_result(
                success=False,
                reason=reason,
                credential_id=credential_id,
                subject_did=subject,
                issuer_did=issuer_did,
                verification_method_id=vm_id or "",
                nonce=nonce,
            )
        except Exception:
            pass
        return False, reason

    try:
        from identity_runtime.presentation_audit import (
            log_nonce_consumed,
            log_presentation_result,
        )

        log_nonce_consumed(audience=audience, nonce=nonce)
        log_presentation_result(
            success=True,
            reason="ok",
            credential_id=credential_id,
            subject_did=subject,
            issuer_did=issuer_did,
            verification_method_id=vm_id or "",
            nonce=nonce,
        )
    except Exception:
        pass
    return True, "ok"