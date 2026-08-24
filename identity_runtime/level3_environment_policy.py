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
Phase 2.9 — I2 Level 3 environment policy (governance, not infrastructure).

Separate CI/lab provisioning is NOT required. Local verifier-controlled
Level 3 remains the baseline.
"""

from __future__ import annotations

from typing import Any, Optional

I2_DECISION = {
    "id": "I2",
    "title": "No separate Level 3 CI/lab provisioning",
    "baseline": "verifier_controlled_local_level3",
    "separate_provisioning_required": False,
    "status": "accepted",
}

REASSESSMENT_TRIGGERS = (
    "threat_model_more_adversarial",
    "common_environment_trust_is_credible_attack_path",
    "level3_frequency_needs_standardization",
    "external_requirement_for_separate_provisioning",
    "inconsistent_or_contested_local_level3_results",
    "cost_benefit_favors_independent_provisioning",
)

H6_DISPOSITION = {
    "item": "H6_holder_recovery_notification",
    "status": "deferred",
    "reason": (
        "No trustworthy out-of-band channel identified that reaches the "
        "legitimate holder rather than the recovery initiator."
    ),
}


def separate_provisioning_required() -> bool:
    return bool(I2_DECISION["separate_provisioning_required"])


def limitations_acceptable(limitations: Optional[str]) -> tuple[bool, str]:
    """Empty limitations are not acceptable; explicit 'none material' is OK."""
    if limitations is None:
        return False, "limitations_missing"
    text = str(limitations).strip()
    if not text:
        return False, "limitations_empty"
    return True, "ok"


def level3_local_path_sufficient(
    *,
    verifier: str,
    implementer: str,
    verifier_run_results: Optional[dict[str, Any]],
    execution_context: str,
    limitations: str,
) -> tuple[bool, str]:
    """
    Confirm local Level 3 can satisfy policy without separate CI.
    Reuses the same evidence expectations as Phase 2.8 gates.
    """
    if not verifier or not str(verifier).strip():
        return False, "missing_verifier"
    if verifier.strip().lower() == (implementer or "").strip().lower():
        return False, "verifier_must_differ_from_implementer"
    if not verifier_run_results:
        return False, "missing_verifier_run_results"
    if not execution_context or not str(execution_context).strip():
        return False, "missing_execution_context"
    ok_lim, lim_reason = limitations_acceptable(limitations)
    if not ok_lim:
        return False, lim_reason
    if separate_provisioning_required():
        return False, "policy_requires_separate_provisioning"
    return True, "local_level3_sufficient_under_i2"