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
Phase 3.1 — Confirmed proof use-case anchors (documentation bounds only).
No cryptography. No proof generation or verification.
"""

from __future__ import annotations

USE_CASE = (
    "Prove that the presenter is an eligible emergency responder for a "
    "specified active disaster-response context, without revealing "
    "unnecessary credential or identity information."
)

DESIGN_PRINCIPLES = (
    "minimum_necessary_proof",
    "context_bound_eligibility",
    "proof_validity_does_not_grant_authorization",
)

SUCCESS_PHASE_31 = (
    "one_unambiguous_implementation_neutral_use_case_ready_for_stage_3_2"
)

NON_SUCCESS_MUST_NOT_APPLY = (
    "ambiguous_verifier_learning",
    "multiple_unrelated_proof_statements",
    "zkp_layer_makes_authorization_decisions",
    "zkp_layer_manages_disaster_incidents",
    "cannot_bound_to_one_active_context",
)

INVARIANTS = (
    "zkp_proof_validity_is_not_authorization",
    "trust_governance_separate_from_proof_verification",
    "credential_lifecycle_outside_zkp_layer",
    "identity_recovery_outside_zkp_layer",
    "incident_disaster_management_outside_zkp_layer",
    "identity_infra_separate_from_operational_incident_infra",
)

DEFERRED = (
    "3.2_disaster_context_authority",
    "3.3_disaster_context_representation",
    "3.4_witness_public_input_boundary",
    "3.5_zk_protocol_circuit_design",
    "3.6_plus_prototype_integration_validation",
)

FORBIDDEN_AUTHORITY_HARDCODES = (
    "fema",
    "red cross",
    "redcross",
    "ahj",
)


def use_case_confirmed() -> bool:
    u = USE_CASE.lower()
    return all(
        [
            "eligible emergency responder" in u,
            "disaster-response context" in u or "disaster response context" in u,
            "unnecessary" in u,
            "minimum_necessary_proof" in DESIGN_PRINCIPLES,
            "context_bound_eligibility" in DESIGN_PRINCIPLES,
            "proof_validity_does_not_grant_authorization" in DESIGN_PRINCIPLES,
            "zkp_proof_validity_is_not_authorization" in INVARIANTS,
            "3.2_disaster_context_authority" in DEFERRED,
            not any(a in u for a in FORBIDDEN_AUTHORITY_HARDCODES),
        ]
    )