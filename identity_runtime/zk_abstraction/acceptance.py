# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""
WP7-CAND-01R1 Workstream A — centralized C1–C4 acceptance control flow.
SF-3.5-VER-1..4, VER-6. F-1..F-5 remediation applied (minimal).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Tuple


class ConditionId(str, Enum):
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"


# F-2: unified failure precedence (acceptance, verifier status, audit identity)
FAILURE_PRECEDENCE: Tuple[ConditionId, ...] = (
    ConditionId.C4,
    ConditionId.C2,
    ConditionId.C3,
    ConditionId.C1,
)

REQUIRED_CONDITIONS: Tuple[ConditionId, ...] = (
    ConditionId.C1,
    ConditionId.C2,
    ConditionId.C3,
    ConditionId.C4,
)


class ConditionOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    MALFORMED = "MALFORMED"
    UNVERIFIABLE = "UNVERIFIABLE"


class AcceptanceDecision(str, Enum):
    VERIFIED_ELIGIBILITY = "VERIFIED_ELIGIBILITY"
    CLAIM_NOT_SATISFIED = "CLAIM_NOT_SATISFIED"


@dataclass(frozen=True)
class ConditionResult:
    condition_id: ConditionId
    outcome: ConditionOutcome
    reason: str = ""


@dataclass(frozen=True)
class AcceptanceResult:
    decision: AcceptanceDecision
    condition_results: Mapping[ConditionId, ConditionResult]  # F-1: MappingProxyType
    verified_eligibility_claim: bool
    authorization_permitted: bool
    status_code: str
    reason: str
    primary_failure: ConditionId | None = None  # F-2

    @property
    def accepted(self) -> bool:
        return self.decision == AcceptanceDecision.VERIFIED_ELIGIBILITY


class AcceptanceControlFlowError(ValueError):
    def __init__(self, message: str, *, status_code: str = "STRUCTURAL_FAILURE"):
        self.status_code = status_code
        super().__init__(message)


def _freeze_results(
    ordered: Mapping[ConditionId, ConditionResult],
) -> Mapping[ConditionId, ConditionResult]:
    """F-1: truly immutable view."""
    return MappingProxyType(dict(ordered))


def evaluate_acceptance(
    results: Mapping[ConditionId, ConditionResult],
) -> AcceptanceResult:
    for cid in REQUIRED_CONDITIONS:
        if cid not in results:
            raise AcceptanceControlFlowError(
                f"missing_condition:{cid.value}",
                status_code="STRUCTURAL_MISSING_CONDITION",
            )

    unexpected = set(results.keys()) - set(REQUIRED_CONDITIONS)
    if unexpected:
        raise AcceptanceControlFlowError(
            f"unexpected_condition:{sorted(c.value for c in unexpected)}",
            status_code="STRUCTURAL_UNEXPECTED_CONDITION",
        )

    for cid, cr in results.items():
        if cr.condition_id != cid:
            raise AcceptanceControlFlowError(
                f"duplicate_or_mismatched_condition:{cid.value}",
                status_code="STRUCTURAL_MISMATCHED_CONDITION",
            )

    ordered = {cid: results[cid] for cid in REQUIRED_CONDITIONS}
    frozen = _freeze_results(ordered)

    for cid in FAILURE_PRECEDENCE:
        outcome = ordered[cid].outcome
        if outcome != ConditionOutcome.PASS:
            return AcceptanceResult(
                decision=AcceptanceDecision.CLAIM_NOT_SATISFIED,
                condition_results=frozen,
                verified_eligibility_claim=False,
                authorization_permitted=False,
                status_code=f"{cid.value}_{outcome.value}",
                reason=ordered[cid].reason or f"{cid.value}:{outcome.value}",
                primary_failure=cid,
            )

    return AcceptanceResult(
        decision=AcceptanceDecision.VERIFIED_ELIGIBILITY,
        condition_results=frozen,
        verified_eligibility_claim=True,
        authorization_permitted=False,
        status_code="OK",
        reason="all_C1_C4_PASS",
        primary_failure=None,
    )


def condition_result(
    condition_id: ConditionId,
    outcome: ConditionOutcome,
    reason: str = "",
) -> ConditionResult:
    return ConditionResult(condition_id=condition_id, outcome=outcome, reason=reason)