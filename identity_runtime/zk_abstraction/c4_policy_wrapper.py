# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""
WP7-CAND-01R1 Workstream C — C4 protocol / scheme / policy wrapper.

Enforces protocol_id, scheme_version, protocol_version, and active policy state.
Uses existing CryptographicRegistry — no parallel trust registry.
Fail-closed; does not alter C1/C2/C3 semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from identity_runtime.zk_abstraction.acceptance import (
    ConditionId,
    ConditionOutcome,
    ConditionResult,
)
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    EvaluationResult,
    OperationType,
)


@dataclass(frozen=True)
class VerifierPolicyContext:
    active_policy_version: str
    allowed_protocol_ids: frozenset[str] = frozenset({"sf-zk"})
    require_policy_match: bool = True


DEFAULT_POLICY_CONTEXT = VerifierPolicyContext(active_policy_version="1.0.0")


@dataclass(frozen=True)
class C4Evaluation:
    allowed: bool
    outcome: ConditionOutcome
    reason: str
    status_code: str
    evaluation: Optional[EvaluationResult] = None


def evaluate_c4(
    registry: CryptographicRegistry,
    identity: IdentityTuple,
    *,
    operation: OperationType = OperationType.PROOF_VERIFICATION,
    policy_context: Optional[VerifierPolicyContext] = None,
) -> C4Evaluation:
    ctx = policy_context or DEFAULT_POLICY_CONTEXT

    if not identity.protocol_id:
        return C4Evaluation(
            False, ConditionOutcome.MALFORMED, "missing_protocol_id", "C4_MALFORMED"
        )
    if not identity.scheme_id:
        return C4Evaluation(
            False, ConditionOutcome.MALFORMED, "missing_scheme_id", "C4_MALFORMED"
        )
    if not identity.scheme_version:
        return C4Evaluation(
            False, ConditionOutcome.MALFORMED, "missing_scheme_version", "C4_MALFORMED"
        )
    if not identity.protocol_version:
        return C4Evaluation(
            False, ConditionOutcome.MALFORMED, "missing_protocol_version", "C4_MALFORMED"
        )
    if not identity.policy_version:
        return C4Evaluation(
            False, ConditionOutcome.MALFORMED, "missing_policy_version", "C4_MALFORMED"
        )

    if identity.protocol_id == "__ambiguous__":
        return C4Evaluation(
            False, ConditionOutcome.AMBIGUOUS, "ambiguous_protocol_id", "C4_AMBIGUOUS"
        )
    if identity.scheme_version == "__ambiguous__":
        return C4Evaluation(
            False, ConditionOutcome.AMBIGUOUS, "ambiguous_scheme_version", "C4_AMBIGUOUS"
        )

    if identity.protocol_id not in ctx.allowed_protocol_ids:
        return C4Evaluation(
            False,
            ConditionOutcome.UNSUPPORTED,
            f"unsupported_protocol_id:{identity.protocol_id}",
            "UNSUPPORTED_PROTOCOL_ID",
        )

    if ctx.require_policy_match and identity.policy_version != ctx.active_policy_version:
        return C4Evaluation(
            False,
            ConditionOutcome.FAIL,
            f"policy_mismatch:request={identity.policy_version}"
            f":active={ctx.active_policy_version}",
            "POLICY_MISMATCH",
        )

    ev = registry.validate_operation(
        identity.scheme_id,
        identity.scheme_version,
        operation,
        protocol_version=identity.protocol_version,
        policy_version=identity.policy_version,
    )
    if not ev.allowed:
        return C4Evaluation(
            False, _map_registry_outcome(ev), ev.reason, ev.status_code, evaluation=ev
        )

    return C4Evaluation(True, ConditionOutcome.PASS, "ok", "OK", evaluation=ev)


def c4_to_condition(evaluation: C4Evaluation) -> ConditionResult:
    return ConditionResult(
        condition_id=ConditionId.C4,
        outcome=evaluation.outcome,
        reason=evaluation.reason,
    )


def _map_registry_outcome(ev: EvaluationResult) -> ConditionOutcome:
    code = (ev.status_code or "").upper()
    reason = (ev.reason or "").lower()
    if "DISABLED" in code or "disabled" in reason:
        return ConditionOutcome.UNSUPPORTED
    if "RETIRED" in code or "retired" in reason:
        return ConditionOutcome.UNSUPPORTED
    if "UNSUPPORTED" in code or "unregistered" in reason:
        return ConditionOutcome.UNSUPPORTED
    if "DOWNGRADE" in code or "downgrade" in reason:
        return ConditionOutcome.FAIL
    if "DEPRECATED" in code:
        return ConditionOutcome.UNSUPPORTED
    if "MALFORMED" in code:
        return ConditionOutcome.MALFORMED
    if "AMBIGUOUS" in code:
        return ConditionOutcome.AMBIGUOUS
    return ConditionOutcome.FAIL