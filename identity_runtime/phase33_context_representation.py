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
Stage 3.3 — Disaster context representation anchors.
Packaging only. No serialization, crypto, or public/private split.
"""

from __future__ import annotations

CONTEXT_ID_RULES = (
    "immutable_context_id",
    "revision_for_authoritative_changes",
    "new_id_only_for_materially_distinct_context",
    "external_ids_are_traceability_only",
)

SCOPE_FIELDS = (
    "incident_type",
    "geographic_applicability",
    "operational_period",
    "authoritative_lifecycle_state",
)

LIFECYCLE_STATES = (
    "ACTIVE",
    "EXPIRED",
    "REVOKED",
    "SUPERSEDED",
)

EXCLUSIONS = (
    "casualty_lists",
    "responder_rosters",
    "dispatch_data",
    "resource_inventories",
    "vehicle_asset_tracking",
    "communications_data",
    "command_notes",
    "unrelated_operational_metadata",
    "unnecessary_personal_information",
)

INVARIANTS = (
    "active_context_established_by_authority_not_zkp",
    "qualification_not_equal_incident_activation",
    "assignment_not_equal_qualification",
    "proof_validity_not_authorization",
    "authorization_remains_authorization_matrix",
    "incident_management_outside_zkp_layer",
    "minimum_necessary_context_representation",
    "context_bound_eligibility",
    "representation_is_not_authorization_engine",
)

REPRESENTATION_MODEL = "canonical_context_envelope_plus_external_authoritative_record_reference"

GOVERNING = {
    "scope": (
        "Represent the minimum authoritative context necessary to support "
        "the intended decision, and no more."
    ),
    "authority_evidence": (
        "Minimize operational content, not authority evidence required for trust."
    ),
    "canonicalization": "Same context + same revision = same meaning everywhere.",
    "external_boundary": (
        "Signal Forge consumes context; it does not become the source system "
        "for incident operations."
    ),
}

GATE_3_3_TO_3_4 = {
    "identity_explicit": True,
    "scope_bounded": True,
    "lifecycle_unambiguous": True,
    "authority_evidence_explicit": True,
    "delegation_explicit": True,
    "conflict_precedence_explicit": True,
    "minimum_disclosure_explicit": True,
    "external_boundary_explicit": True,
    "hybrid_model_selected": True,
    "sufficient_for_stage_3_4": True,
    "no_core_ambiguity": True,
    "no_public_private_split": True,
    "no_zk_runtime": True,
}


def package_complete() -> bool:
    return all(
        [
            "immutable_context_id" in CONTEXT_ID_RULES,
            len(SCOPE_FIELDS) == 4,
            "ACTIVE" in LIFECYCLE_STATES,
            len(LIFECYCLE_STATES) == 4,
            "casualty_lists" in EXCLUSIONS,
            REPRESENTATION_MODEL.startswith("canonical_context_envelope"),
            "representation_is_not_authorization_engine" in INVARIANTS,
            GATE_3_3_TO_3_4["sufficient_for_stage_3_4"] is True,
            GATE_3_3_TO_3_4["no_public_private_split"] is True,
            GATE_3_3_TO_3_4["no_zk_runtime"] is True,
        ]
    )