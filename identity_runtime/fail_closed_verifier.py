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

"""Gate 5 fail-closed acceptance control flow.

This module deliberately separates the four mandatory verification conditions
from the policy that decides whether a verified eligibility claim may be
emitted.  It does not implement a concrete proof system; C1-C4 are supplied as
explicit check results by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class CheckStatus(str, Enum):
    """Only an explicit PASS may satisfy a required acceptance condition."""

    PASS = "PASS"
    FAIL = "FAIL"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    MALFORMED = "MALFORMED"
    UNVERIFIABLE = "UNVERIFIABLE"


class VerificationStatus(str, Enum):
    """Externally meaningful verification outcomes for Gate 5."""

    VERIFIED_ELIGIBILITY = "VERIFIED_ELIGIBILITY"
    CLAIM_NOT_SATISFIED = "CLAIM_NOT_SATISFIED"


@dataclass(frozen=True)
class CheckResult:
    """Result of one mandatory C1-C4 verification condition."""

    condition: str
    status: CheckStatus
    detail: str = ""

    def __post_init__(self) -> None:
        if self.condition not in {"C1", "C2", "C3", "C4"}:
            raise ValueError("condition_must_be_C1_through_C4")


@dataclass(frozen=True)
class VerificationResult:
    """Fail-closed result emitted by the Gate 5 control-flow boundary."""

    status: VerificationStatus
    reason: str
    failed_condition: str | None
    checks: tuple[CheckResult, ...]
    verified_eligibility_claim: bool
    authorization_permitted: bool


def _validate_checks(checks: Iterable[CheckResult]) -> tuple[CheckResult, ...]:
    """Require exactly one explicit result for each mandatory condition."""

    materialized = tuple(checks)
    if len(materialized) != 4:
        raise ValueError("exactly_four_conditions_required")

    by_condition = {check.condition: check for check in materialized}
    required = {"C1", "C2", "C3", "C4"}
    if set(by_condition) != required:
        raise ValueError("all_C1_through_C4_required_once")

    return tuple(by_condition[name] for name in ("C1", "C2", "C3", "C4"))


def verify_fail_closed(
    *,
    c1: CheckResult,
    c2: CheckResult,
    c3: CheckResult,
    c4: CheckResult,
) -> VerificationResult:
    """Evaluate the only accepted Gate 5 path.

    Acceptance is possible only when every condition is explicitly PASS.
    Any other state is a non-successful verification result.  A non-success
    never emits a verified eligibility claim and never permits authorization.
    """

    checks = _validate_checks((c1, c2, c3, c4))
    failed = next((check for check in checks if check.status is not CheckStatus.PASS), None)

    if failed is not None:
        return VerificationResult(
            status=VerificationStatus.CLAIM_NOT_SATISFIED,
            reason=f"{failed.condition.lower()}_{failed.status.value.lower()}",
            failed_condition=failed.condition,
            checks=checks,
            verified_eligibility_claim=False,
            authorization_permitted=False,
        )

    return VerificationResult(
        status=VerificationStatus.VERIFIED_ELIGIBILITY,
        reason="all_C1_through_C4_pass",
        failed_condition=None,
        checks=checks,
        verified_eligibility_claim=True,
        authorization_permitted=True,
    )
