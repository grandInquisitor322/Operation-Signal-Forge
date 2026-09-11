# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""WP7-CAND-01R1 Workstream B — SF-3.5-VER-5 result & error taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from identity_runtime.zk_abstraction.acceptance import (
    AcceptanceDecision,
    AcceptanceResult,
    ConditionId,
    ConditionOutcome,
    ConditionResult,
)


class VerificationOutcomeClass(str, Enum):
    VERIFIED_ELIGIBILITY = "VERIFIED_ELIGIBILITY"
    CLAIM_NOT_SATISFIED = "CLAIM_NOT_SATISFIED"
    MALFORMED = "MALFORMED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    UNVERIFIABLE = "UNVERIFIABLE"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


FORBIDDEN_OUTCOME = "ASSERTED_INELIGIBLE"


class SubjectIneligibilityStatus(str, Enum):
    NOT_ASSERTED = "NOT_ASSERTED"
    ESTABLISHED = "ESTABLISHED"


@dataclass(frozen=True)
class TaxonomyResult:
    outcome: VerificationOutcomeClass
    subject_ineligibility: SubjectIneligibilityStatus
    verified_eligibility_claim: bool
    authorization_permitted: bool
    primary_condition: Optional[ConditionId]
    detail: str

    @property
    def is_verified_eligibility(self) -> bool:
        return self.outcome == VerificationOutcomeClass.VERIFIED_ELIGIBILITY

    @property
    def asserts_subject_ineligible(self) -> bool:
        return self.subject_ineligibility == SubjectIneligibilityStatus.ESTABLISHED


def _outcome_from_condition(outcome: ConditionOutcome) -> VerificationOutcomeClass:
    if outcome == ConditionOutcome.MALFORMED:
        return VerificationOutcomeClass.MALFORMED
    if outcome == ConditionOutcome.UNSUPPORTED:
        return VerificationOutcomeClass.UNSUPPORTED
    if outcome == ConditionOutcome.AMBIGUOUS:
        return VerificationOutcomeClass.AMBIGUOUS
    if outcome == ConditionOutcome.UNVERIFIABLE:
        return VerificationOutcomeClass.UNVERIFIABLE
    return VerificationOutcomeClass.CLAIM_NOT_SATISFIED


def classify_acceptance(acceptance: AcceptanceResult) -> TaxonomyResult:
    if acceptance.decision == AcceptanceDecision.VERIFIED_ELIGIBILITY:
        return TaxonomyResult(
            outcome=VerificationOutcomeClass.VERIFIED_ELIGIBILITY,
            subject_ineligibility=SubjectIneligibilityStatus.NOT_ASSERTED,
            verified_eligibility_claim=True,
            authorization_permitted=False,
            primary_condition=None,
            detail=acceptance.reason or "all_C1_C4_PASS",
        )

    primary = acceptance.primary_failure
    detail = acceptance.reason or acceptance.status_code
    outcome_class = VerificationOutcomeClass.CLAIM_NOT_SATISFIED

    if primary is not None and acceptance.condition_results:
        cr = acceptance.condition_results.get(primary)
        if cr is not None:
            outcome_class = _outcome_from_condition(cr.outcome)
            detail = cr.reason or detail

    return TaxonomyResult(
        outcome=outcome_class,
        subject_ineligibility=SubjectIneligibilityStatus.NOT_ASSERTED,
        verified_eligibility_claim=False,
        authorization_permitted=False,
        primary_condition=primary,
        detail=detail,
    )


def classify_from_status_reason(
    *,
    accepted: bool,
    status_code: str,
    reason: str,
) -> TaxonomyResult:
    if accepted:
        return TaxonomyResult(
            outcome=VerificationOutcomeClass.VERIFIED_ELIGIBILITY,
            subject_ineligibility=SubjectIneligibilityStatus.NOT_ASSERTED,
            verified_eligibility_claim=True,
            authorization_permitted=False,
            primary_condition=None,
            detail=reason or status_code,
        )

    code = (status_code or "").upper()
    if "MALFORMED" in code:
        oc = VerificationOutcomeClass.MALFORMED
    elif "UNSUPPORTED" in code or "SCHEME_" in code or "DOWNGRADE" in code:
        oc = VerificationOutcomeClass.UNSUPPORTED
    elif "AMBIGUOUS" in code:
        oc = VerificationOutcomeClass.AMBIGUOUS
    elif "UNVERIFIABLE" in code or "STRUCTURAL" in code:
        oc = VerificationOutcomeClass.UNVERIFIABLE
    else:
        oc = VerificationOutcomeClass.CLAIM_NOT_SATISFIED

    return TaxonomyResult(
        outcome=oc,
        subject_ineligibility=SubjectIneligibilityStatus.NOT_ASSERTED,
        verified_eligibility_claim=False,
        authorization_permitted=False,
        primary_condition=None,
        detail=reason or status_code,
    )
