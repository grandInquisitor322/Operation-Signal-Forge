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
Phase 2.8 — Risk-based Independent Verification levels (I1).

Level 1: evidence review / spot-check
Level 2: independent test re-execution (verifier-run)
Level 3: isolated verifier-controlled execution

Ambiguity escalates to the stronger level.
Phase author proposes; independent verifier confirms or escalates (never de-escalates).
"""

from __future__ import annotations

from typing import Any, Optional

LEVEL_1 = 1
LEVEL_2 = 2
LEVEL_3 = 3

LEVEL_NAMES = {
    LEVEL_1: "evidence_review_spot_check",
    LEVEL_2: "independent_test_re_execution",
    LEVEL_3: "isolated_verifier_controlled_execution",
}

HIGH_CONSEQUENCE_DOMAINS = frozenset(
    {
        "identity",
        "authentication",
        "authorization",
        "access_control",
        "credential_lifecycle",
        "identity_recovery",
        "cryptographic",
        "security_controls",
        "audit_compliance",
        "audit_governance",
    }
)

MEDIUM_CONSEQUENCE_DOMAINS = frozenset(
    {
        "behavioral_change",
        "api_behavior",
        "capability_layer",
        "dapp_ux",
    }
)

LOW_CONSEQUENCE_DOMAINS = frozenset(
    {
        "documentation",
        "docs",
        "non_security_config",
        "low_impact_refactor",
        "milestone_record",
    }
)


def level_name(level: int) -> str:
    return LEVEL_NAMES.get(int(level), f"unknown_level_{level}")


def recommend_level(
    *,
    domains: list[str],
    explicit_level: Optional[int] = None,
    ambiguous: bool = False,
) -> tuple[int, str]:
    """Recommend level from domains. Ambiguity escalates upward."""
    if explicit_level is not None:
        lvl = int(explicit_level)
        if lvl not in (1, 2, 3):
            return LEVEL_3, "invalid_explicit_level_escalated_to_3"
        if ambiguous and lvl < LEVEL_3:
            return min(3, lvl + 1), "ambiguous_escalated_from_explicit"
        return lvl, "explicit"

    normalized = {
        d.strip().lower().replace("-", "_").replace(" ", "_") for d in domains if d
    }
    if not normalized:
        return LEVEL_2, "empty_domains_default_level_2"

    if normalized & HIGH_CONSEQUENCE_DOMAINS:
        base, reason = LEVEL_3, "high_consequence_domain"
    elif normalized & MEDIUM_CONSEQUENCE_DOMAINS:
        base, reason = LEVEL_2, "medium_consequence_domain"
    elif normalized <= LOW_CONSEQUENCE_DOMAINS:
        base, reason = LEVEL_1, "low_consequence_domain"
    else:
        base, reason = LEVEL_2, "unknown_domain_default_level_2"

    if ambiguous and base < LEVEL_3:
        return base + 1, f"{reason}_ambiguous_escalated"
    return base, reason


def propose_level(
    *,
    domains: list[str],
    proposed_by: str,
    proposed_level: Optional[int] = None,
    ambiguous: bool = False,
    rationale: str = "",
) -> dict[str, Any]:
    """Phase author proposal (not binding)."""
    if proposed_level is None:
        lvl, reason = recommend_level(domains=domains, ambiguous=ambiguous)
    else:
        lvl, reason = recommend_level(
            domains=domains, explicit_level=proposed_level, ambiguous=ambiguous
        )
    return {
        "status": "proposed",
        "proposed_by": proposed_by,
        "proposed_level": lvl,
        "proposed_level_name": level_name(lvl),
        "domains": list(domains),
        "risk_rationale": rationale or reason,
        "binding": False,
        "note": "Verifier must confirm or escalate; cannot de-escalate.",
    }


def confirm_or_escalate(
    proposal: dict[str, Any],
    *,
    verifier: str,
    confirmed_level: Optional[int] = None,
    escalate_to: Optional[int] = None,
    verifier_rationale: str = "",
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """
    Independent verifier final authority.
    May confirm proposed level or escalate to a stronger level only.
    """
    if not verifier or not str(verifier).strip():
        return None, "missing_verifier"
    proposed = int(proposal.get("proposed_level") or 0)
    if proposed not in (1, 2, 3):
        return None, "invalid_proposal"

    if escalate_to is not None:
        final = int(escalate_to)
        if final not in (1, 2, 3):
            return None, "invalid_escalate_to"
        if final < proposed:
            return None, "verifier_cannot_de_escalate"
        action = "escalated" if final > proposed else "confirmed"
    elif confirmed_level is not None:
        final = int(confirmed_level)
        if final not in (1, 2, 3):
            return None, "invalid_confirmed_level"
        if final < proposed:
            return None, "verifier_cannot_de_escalate"
        action = "escalated" if final > proposed else "confirmed"
    else:
        final = proposed
        action = "confirmed"

    return {
        "status": action,
        "verifier": verifier,
        "proposed_level": proposed,
        "final_level": final,
        "final_level_name": level_name(final),
        "verifier_rationale": verifier_rationale or None,
        "binding": True,
        "domains": proposal.get("domains") or [],
        "risk_rationale": proposal.get("risk_rationale"),
    }, None


def validate_level_record(fields: dict[str, Any]) -> tuple[bool, str]:
    required = [
        "verification_level",
        "risk_rationale",
        "domains",
        "expected_evidence",
        "verifier",
    ]
    for k in required:
        if k not in fields or fields[k] in (None, "", []):
            return False, f"missing_{k}"
    lvl = int(fields["verification_level"])
    if lvl not in (1, 2, 3):
        return False, "invalid_verification_level"
    return True, "ok"


def expected_evidence_for_level(level: int) -> list[str]:
    if level == LEVEL_1:
        return [
            "reviewer_distinct_from_implementer",
            "reported_evidence_reviewed",
            "repository_spot_check",
        ]
    if level == LEVEL_2:
        return [
            "reviewer_distinct_from_implementer",
            "verifier_ran_relevant_suites",
            "suite_results_captured",
            "not_solely_implementer_console",
        ]
    return [
        "reviewer_distinct_from_implementer",
        "verifier_controlled_execution_context",
        "independent_configuration_where_practical",
        "verifier_ran_required_suites",
        "verifier_run_results_captured",
        "environment_limitations_recorded",
    ]


def validate_evidence_for_level(
    level: int,
    *,
    verifier_run_results: Optional[dict[str, Any]] = None,
    execution_context: str = "",
    implementer_console_only: bool = False,
) -> tuple[bool, str]:
    """
    Gate: insufficient evidence must not be treated as PASS.
    Level 2+ requires verifier-run results; Level 3 requires execution_context.
    """
    lvl = int(level)
    if lvl >= LEVEL_2:
        if implementer_console_only:
            return False, "level2_plus_rejects_implementer_console_only"
        if not verifier_run_results:
            return False, "missing_verifier_run_results"
    if lvl >= LEVEL_3:
        if not execution_context or not str(execution_context).strip():
            return False, "missing_execution_context_for_level3"
    return True, "ok"