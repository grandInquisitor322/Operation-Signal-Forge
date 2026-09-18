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
Phase 3.2 — Disaster context authority & responder model anchors.
Decision packaging only. No schemas, crypto, or runtime incident management.
"""

from __future__ import annotations

AUTHORITY_ROLES = (
    "authorized_incident_authority",
    "responder_qualification_authority",
    "operational_assignment_authority",
    "authorization_matrix",
    "zkp_verifier",
)

CLAIM_TYPES = (
    "qualification_claim",
    "assignment_claim",
    "authorization_decision",
)

LIFECYCLE_SEMANTICS = (
    "activation",
    "validity",
    "expiration",
    "revocation",
    "amendment",
    "supersession",
)

REJECTED_ALTERNATIVES = (
    "single_universal_authority",
    "red_cross_as_universal_incident_authority",
    "sar_as_universal_incident_authority",
    "zkp_layer_determines_disaster_status",
)

INVARIANTS = (
    "active_context_established_by_authority_not_zkp",
    "qualification_not_equal_incident_activation",
    "assignment_not_equal_qualification",
    "proof_validity_not_authorization",
    "authorization_remains_authorization_matrix",
    "incident_management_outside_zkp_layer",
)

FORBIDDEN_ORG_HARDCODES = (
    "fema",
    "red cross",
    "redcross",
    "ahj",
)

GATE_3_2_TO_3_3 = {
    "who_declares_context_active": "resolved_as_authorized_incident_authority_model",
    "responder_qualification_authority": "resolved_as_distinct_qualification_authority",
    "lifecycle_semantics_documented": True,
    "conflict_and_delegation_documented": True,
    "zkp_boundary_preserved": True,
}


def package_complete() -> bool:
    return all(
        [
            "authorized_incident_authority" in AUTHORITY_ROLES,
            "zkp_verifier" in AUTHORITY_ROLES,
            "qualification_claim" in CLAIM_TYPES,
            "assignment_claim" in CLAIM_TYPES,
            "authorization_decision" in CLAIM_TYPES,
            len(LIFECYCLE_SEMANTICS) == 6,
            "zkp_layer_determines_disaster_status" in REJECTED_ALTERNATIVES,
            "proof_validity_not_authorization" in INVARIANTS,
            GATE_3_2_TO_3_3["lifecycle_semantics_documented"] is True,
            GATE_3_2_TO_3_3["zkp_boundary_preserved"] is True,
        ]
    )