"""
Minimal did:key helpers for Ed25519 (interim).

DID method: did:key
Multicodec prefix for Ed25519 pub: 0xed 0x01
Multibase: base58btc (z prefix)
"""

from __future__ import annotations

import base64
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    out = ""
    while n > 0:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    for b in data:
        if b == 0:
            out = "1" + out
        else:
            break
    return out or "1"


def _b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    full = n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")
    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break
    return b"\x00" * pad + full


def public_key_to_did_key(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    multicodec = b"\xed\x01" + raw
    return "did:key:z" + _b58encode(multicodec)


def did_key_to_public_key(did: str) -> Ed25519PublicKey:
    if not did.startswith("did:key:z"):
        raise ValueError(f"Unsupported DID method/format: {did}")
    payload = _b58decode(did[len("did:key:z") :])
    idx = payload.find(b"\xed\x01")
    if idx >= 0 and len(payload) >= idx + 34:
        raw = payload[idx + 2 : idx + 34]
    else:
        raw = payload[-32:]
    if len(raw) != 32:
        raise ValueError("Not an Ed25519 did:key")
    return Ed25519PublicKey.from_public_bytes(raw)


def generate_keypair() -> Tuple[Ed25519PrivateKey, str]:
    private = Ed25519PrivateKey.generate()
    did = public_key_to_did_key(private.public_key())
    return private, did


def private_to_pem(private: Ed25519PrivateKey) -> bytes:
    return private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def private_from_pem(pem: bytes) -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(pem, password=None)


def b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64u_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)