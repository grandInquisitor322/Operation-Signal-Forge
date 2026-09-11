# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Stage 3.5 — Cryptographic abstraction (no concrete ZK library)."""

from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    SchemeDescriptor,
    SchemeLifecycleState,
    OperationType,
)
from identity_runtime.zk_abstraction.verifier import (
    IndependentVerifier,
    VerificationRequest,
    VerificationResult,
    VerificationFailure,
)
from identity_runtime.zk_abstraction.audit import CryptographicAuditLogger
from identity_runtime.zk_abstraction.binder import ContextClaimBinder, BindingTarget
from identity_runtime.zk_abstraction.identity import IdentityTuple

__all__ = [
    "CryptographicRegistry",
    "SchemeDescriptor",
    "SchemeLifecycleState",
    "OperationType",
    "IndependentVerifier",
    "VerificationRequest",
    "VerificationResult",
    "VerificationFailure",
    "CryptographicAuditLogger",
    "ContextClaimBinder",
    "BindingTarget",
    "IdentityTuple",
]