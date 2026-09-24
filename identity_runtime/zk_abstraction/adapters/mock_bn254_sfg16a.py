# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Gate 6 adapter A — BN254 SFG16A + mock fingerprint relation."""

from __future__ import annotations

from identity_runtime.zk_abstraction.bn254 import (
    PROOF_G1_PREFIX,
    parse_g1_proof,
    validate_g1_affine,
)
from identity_runtime.zk_abstraction.scheme_types import (
    BoundStatementTarget,
    CryptoOutcome,
    CryptoValidityResult,
)

ADAPTER_ID = "mock-bn254-sfg16a"
SCHEME_ID = "mock-scheme"
SCHEME_VERSION = "1.0.0"
MATERIALS_REF = "mock"


class MockBn254Sfg16aVerifier:
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
        if not proof_bytes.startswith(PROOF_G1_PREFIX):
            return _r(CryptoOutcome.MALFORMED, "proof_format_required_sfg16a")
        try:
            g1 = parse_g1_proof(proof_bytes)
        except ValueError as e:
            return _r(CryptoOutcome.MALFORMED, "proof_parse_error", str(e))
        if g1 is None:
            return _r(CryptoOutcome.MALFORMED, "proof_format_required_sfg16a")
        g1_reason = validate_g1_affine(g1.x, g1.y)
        if g1_reason:
            return _r(CryptoOutcome.MALFORMED, g1_reason, g1_reason)
        payload = g1.payload
        if not payload:
            return _r(CryptoOutcome.MALFORMED, "empty_proof")
        expected = ("VALID:" + (bound.relation_hint or "")).encode("utf-8")
        if payload != expected:
            return _r(CryptoOutcome.FAIL, "scheme_proof_check_failed")
        return _r(CryptoOutcome.PASS, "ok")