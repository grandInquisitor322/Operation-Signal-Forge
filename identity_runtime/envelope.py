"""
Option C interim credential: signed JSON envelope (not full W3C Data Integrity).

Canonical bytes = UTF-8 JSON of payload with sorted keys, excluding `proof`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from identity_runtime.did_key import b64u_decode, b64u_encode, did_key_to_public_key


def _canonical_payload(envelope: dict[str, Any]) -> bytes:
    body = {k: v for k, v in envelope.items() if k != "proof"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_envelope(
    payload: dict[str, Any],
    issuer_private: Ed25519PrivateKey,
    issuer_did: str,
) -> dict[str, Any]:
    envelope = dict(payload)
    envelope.setdefault("issuer", issuer_did)
    to_sign = _canonical_payload(envelope)
    sig = issuer_private.sign(to_sign)
    envelope["proof"] = {
        "type": "SfEd25519Envelope2026-interim",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verificationMethod": f"{issuer_did}#key-1",
        "signature": b64u_encode(sig),
    }
    return envelope


def verify_envelope(envelope: dict[str, Any]) -> tuple[bool, str]:
    proof = envelope.get("proof")
    if not isinstance(proof, dict):
        return False, "missing_proof"
    sig_b64 = proof.get("signature")
    if not sig_b64:
        return False, "missing_signature"
    issuer = envelope.get("issuer")
    if not issuer:
        return False, "missing_issuer"
    try:
        public = did_key_to_public_key(issuer)
        public.verify(b64u_decode(sig_b64), _canonical_payload(envelope))
    except Exception as e:
        return False, f"signature_invalid:{e}"
    return True, "ok"