# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 6 adapter B — distinct mock mechanism (no BN254/SFG16A)."""

from __future__ import annotations

import hashlib

from identity_runtime.zk_abstraction.scheme_types import (
    BoundStatementTarget,
    CryptoOutcome,
    CryptoValidityResult,
)

ADAPTER_ID = "mock-digest-v2"
SCHEME_ID = "mock-digest"
SCHEME_VERSION = "1.0.0"
MATERIALS_REF = "mock-digest-materials"
PREFIX = b"M2:"


def _view_digest(bound: BoundStatementTarget) -> str:
    if bound.relation_hint:
        return bound.relation_hint
    items = sorted(bound.public_input_view.items())
    raw = "|".join(f"{k}={v}" for k, v in items)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class MockDigestV2Verifier:
    adapter_id = ADAPTER_ID

    def verify_crypto(
        self, proof_bytes: bytes, bound: BoundStatementTarget
    ) -> CryptoValidityResult:
        def _r(
            outcome: CryptoOutcome, code: str, detail: str = ""
        ) -> CryptoValidityResult:
            return CryptoValidityResult(
                outcome=outcome,
                reason_code=code,
                scheme_id=bound.scheme_id,
                scheme_version=bound.scheme_version,
                reason_detail=detail or code,
                materials_ref=bound.materials_ref,
                adapter_id=self.adapter_id,
                statement_id=bound.statement_id,
            )

        if bound.scheme_id != SCHEME_ID or bound.scheme_version != SCHEME_VERSION:
            return _r(CryptoOutcome.UNSUPPORTED, "scheme_unsupported")
        if not proof_bytes:
            return _r(CryptoOutcome.MALFORMED, "empty_proof")
        if not proof_bytes.startswith(PREFIX):
            return _r(CryptoOutcome.MALFORMED, "proof_format_invalid")
        tag = proof_bytes[len(PREFIX) :].decode("utf-8", errors="replace")
        expected = _view_digest(bound)
        if tag != expected:
            return _r(CryptoOutcome.FAIL, "relation_check_failed")
        return _r(CryptoOutcome.PASS, "ok")