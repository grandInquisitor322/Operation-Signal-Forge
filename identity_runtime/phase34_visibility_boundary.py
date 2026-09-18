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
Stage 3.4 — Witness / public-input visibility boundary anchors.
Decision packaging only. No proving system, circuits, or serialization.
"""

from __future__ import annotations

from typing import Dict

# --- Claim semantics (3.4-A) ---

ELIGIBILITY_PROPOSITION = (
    "The subject satisfies the qualification requirements and, where applicable, "
    "operational-assignment requirements for a specified authoritative "
    "disaster-response context and revision."
)

CLAIM_KINDS = (
    "qualification",
    "assignment",
    "eligibility",
    "authorization",
)

# --- Three-way classification (3.4-B) ---

CLASSIFICATIONS = (
    "verifier_visible",
    "private_witness",
    "outside_proof_boundary",
)

# Context fields from Stage 3.3 (visibility candidates; not all public)
CONTEXT_FIELDS = (
    "context_id",
    "revision",
    "incident_type",
    "geographic_applicability",
    "operational_period",
    "lifecycle_state",
)

# Minimum authority *conditions* that may be verifier-visible (3.4-G)
AUTHORITY_VISIBLE_CONDITIONS = (
    "authority_reference",
    "authority_role_class",
    "delegated_authority_indication",
)

# Explicit outside-proof exclusions (3.4-E)
OUTSIDE_PROOF = (
    "full_incident_management_records",
    "dispatch_history",
    "resource_allocation",
    "command_and_control_data",
    "casualty_lists",
    "unrelated_responder_records",
    "unrelated_credentials",
    "unnecessary_personal_information",
    "operational_telemetry_unrelated_to_claim",
)

# Fail-closed condition labels (3.4-J)
FAIL_CLOSED_TRIGGERS = (
    "missing",
    "ambiguous",
    "stale",
    "revoked",
    "superseded",
    "conflicted",
    "malformed",
    "unverifiable",
)

INVARIANTS = (
    "public_means_verifier_visible",
    "public_input_conditions_private_witness_evidence",
    "proof_boundary_subset_of_available_information",
    "eligibility_context_bound",
    "qualification_does_not_imply_assignment",
    "assignment_does_not_imply_qualification",
    "proof_validity_not_authorization",
    "authorization_remains_authorization_matrix",
    "stage_3_3_semantics_unchanged",
    "classification_does_not_imply_crypto_choice",
    "unresolved_condition_cannot_satisfy_eligibility",
)

GATE_3_4_TO_3_5 = {
    "proposition_explicit": True,
    "three_way_classification": True,
    "min_visible_context": True,
    "private_witness_boundary": True,
    "outside_exclusions": True,
    "context_revision_binding": True,
    "authority_visibility_bounded": True,
    "qual_assign_independent": True,
    "min_verifier_knowledge_contract": True,
    "fail_closed": True,
    "stage_3_3_unchanged": True,
    "no_stage_3_5_crypto": True,
    "sufficient_for_stage_3_5": True,
}


def classify_attribute(
    name: str,
    *,
    required_for_proposition: bool,
    is_evidence_not_condition: bool,
    outside_list: bool = False,
) -> str:
    """Claim-specific classification helper (design-boundary testable)."""
    if outside_list or name in OUTSIDE_PROOF:
        return "outside_proof_boundary"
    if not required_for_proposition:
        return "outside_proof_boundary"
    if is_evidence_not_condition:
        return "private_witness"
    return "verifier_visible"


def context_binding_key(context_id: str, revision: int) -> str:
    return f"{context_id}@{revision}"


def bindings_distinct(a_id: str, a_rev: int, b_id: str, b_rev: int) -> bool:
    return context_binding_key(a_id, a_rev) != context_binding_key(b_id, b_rev)


def qualification_satisfies_assignment(
    has_qualification: bool, requires_assignment: bool
) -> bool:
    """Qualification alone never satisfies assignment requirements."""
    if requires_assignment:
        return False
    return has_qualification


def assignment_satisfies_qualification(
    has_assignment: bool, requires_qualification: bool
) -> bool:
    """Assignment alone never satisfies qualification requirements."""
    if requires_qualification:
        return False
    return has_assignment


def eligibility_satisfied(
    *,
    required_conditions_ok: bool,
    any_fail_closed_trigger: bool,
) -> bool:
    """Fail-closed: any unresolved required condition → claim not satisfied."""
    if any_fail_closed_trigger:
        return False
    return required_conditions_ok


def claim_not_satisfied_is_not_authorization(claim_satisfied: bool) -> bool:
    """Failed/absent eligibility never yields authorization."""
    return not claim_satisfied


def package_complete() -> bool:
    return all(
        [
            "eligibility" in CLAIM_KINDS,
            "authorization" in CLAIM_KINDS,
            len(CLASSIFICATIONS) == 3,
            "context_id" in CONTEXT_FIELDS,
            "revision" in CONTEXT_FIELDS,
            "casualty_lists" in OUTSIDE_PROOF,
            "authority_reference" in AUTHORITY_VISIBLE_CONDITIONS,
            "missing" in FAIL_CLOSED_TRIGGERS,
            "proof_validity_not_authorization" in INVARIANTS,
            GATE_3_4_TO_3_5["sufficient_for_stage_3_5"] is True,
            GATE_3_4_TO_3_5["no_stage_3_5_crypto"] is True,
            GATE_3_4_TO_3_5["fail_closed"] is True,
        ]
    )


def minimum_verifier_knowledge_contract() -> Dict[str, object]:
    """Stage 3.5 handoff artifact (semantic, not cryptographic)."""
    return {
        "proposition": ELIGIBILITY_PROPOSITION,
        "verifier_visible_condition_classes": [
            "context_id_and_revision_as_required",
            "claim_required_context_conditions",
            "minimum_authority_conditions",
            "minimum_qualification_and_or_assignment_conditions",
        ],
        "private_witness_evidence_classes": [
            "qualification_evidence",
            "assignment_evidence_when_required",
            "credential_validity_evidence",
            "supporting_identity_attributes_for_proposition_only",
            "authority_credentials_and_trust_chain_when_ref_suffices",
        ],
        "outside_proof_boundary": list(OUTSIDE_PROOF),
        "minimization_rule": (
            "If this attribute can be removed without impairing evaluation of "
            "the proposition, it shall not be part of the public-input boundary."
        ),
    }