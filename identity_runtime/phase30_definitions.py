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
Phase 3.0 — Machine-readable anchors for definition artifacts.
No cryptography. No proof generation or verification.
"""

from __future__ import annotations

USE_CASE = (
    "Prove that the presenter is an eligible emergency responder for a "
    "specified active disaster-response context, without revealing "
    "unnecessary credential or identity information."
)

CRYPTOGRAPHIC_OBJECTIVE = {
    "fact_proven": (
        "Presenter is an eligible emergency responder for the specified "
        "active disaster-response context."
    ),
    "verifier_needs": [
        "proof_valid",
        "disaster_context_reference",
        "minimal_eligibility_outcome",
    ],
    "must_remain_private": [
        "unnecessary_identity_attributes",
        "full_credential_payload",
        "unrelated_roles_and_scopes",
        "authorization_matrix_decisions",
        "recovery_metadata",
    ],
}

PRIVACY_VERIFIER_LEARNS = [
    "eligibility_as_emergency_responder_for_specified_context",
    "disaster_context_reference",
    "cryptographic_validity_of_proof",
]

PRIVACY_VERIFIER_MUST_NOT_LEARN = [
    "full_identity_profile",
    "full_credential_contents",
    "authorization_scopes_or_tasking",
    "trust_registry_internal_policy_beyond_public_need",
    "credential_lifecycle_or_recovery_state",
]

SUCCESS_ESTABLISHES = [
    "cryptographic_validity_under_future_procedure",
    "eligible_emergency_responder_for_specified_active_context",
]

SUCCESS_DOES_NOT_ESTABLISH = [
    "authorization",  # Authorization Matrix
    "issuer_trust",  # Trust Registry
    "credential_lifecycle_correctness",
    "identity_recovery",
    "disaster_authority_or_command",
    "fusion_or_sensor_truth",
]

DEFERRED_STAGES = (
    "3.2_disaster_context_authority",
    "3.3_disaster_context_representation",
    "3.4_witness_public_input_boundary",
    "3.5_zk_protocol_circuit_design",
    "3.6_plus_prototype_integration_validation",
)

INVARIANTS = (
    "zkp_proof_validity_is_not_authorization",
    "authorization_remains_authorization_matrix",
    "trust_governance_separate_from_proof_verification",
    "credential_lifecycle_outside_zkp_layer",
    "identity_recovery_outside_zkp_layer",
    "incident_disaster_management_outside_zkp_layer",
)


def definition_complete() -> bool:
    return all(
        [
            bool(USE_CASE.strip()),
            bool(CRYPTOGRAPHIC_OBJECTIVE["fact_proven"]),
            len(PRIVACY_VERIFIER_LEARNS) >= 1,
            len(PRIVACY_VERIFIER_MUST_NOT_LEARN) >= 1,
            len(SUCCESS_ESTABLISHES) >= 1,
            len(SUCCESS_DOES_NOT_ESTABLISH) >= 1,
            "3.2_disaster_context_authority" in DEFERRED_STAGES,
            "zkp_proof_validity_is_not_authorization" in INVARIANTS,
        ]
    )