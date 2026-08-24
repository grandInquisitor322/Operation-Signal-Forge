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
Present a signed envelope credential → AuthZContext fields.

Verify order:
  signature → [optional subject binding] → trust registry → expiration
  → revocation → matrix scopes

Does not talk to Fusion or Capability Layer.
Subject binding is opt-in (require_subject_binding=False by default)
so Phase 2.1–2.3 present paths stay unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from identity_runtime.credential_status import check_status
from identity_runtime.envelope import verify_envelope
from identity_runtime.scope_mapper import scopes_for_credential_type
from identity_runtime.trust_registry import issuer_allows_type


def present_credential(
    envelope: dict[str, Any],
    *,
    subject_binding_proof: Optional[dict[str, Any]] = None,
    challenge: Optional[dict[str, Any]] = None,
    require_subject_binding: bool = False,
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """
    Returns (authz_dict, error).
    authz_dict aligns with dapp_api AuthZContext fields.
    """
    # 1) Signature
    ok, reason = verify_envelope(envelope)
    if not ok:
        return None, reason

    # 1b) Optional Phase 2.4 subject binding
    if require_subject_binding or subject_binding_proof is not None:
        from identity_runtime.presentation import verify_subject_binding

        bok, breason = verify_subject_binding(
            credential=envelope,
            proof=subject_binding_proof,
            challenge=challenge,
            require_binding=require_subject_binding
            or subject_binding_proof is not None,
        )
        if not bok:
            return None, breason

    subject = envelope.get("credentialSubject") or {}
    cred_type = subject.get("credentialType") or envelope.get("credentialType")
    if not cred_type:
        return None, "missing_credential_type"

    issuer = envelope.get("issuer")

    # 2) Trust Registry
    allowed, reg_reason = issuer_allows_type(issuer, cred_type)
    if not allowed:
        return None, reg_reason

    # 3) Expiration
    exp = envelope.get("expirationDate")
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if exp_dt < datetime.now(timezone.utc):
                return None, "credential_expired"
        except ValueError:
            return None, "invalid_expirationDate"

    # 4) Revocation / status
    credential_id = envelope.get("id") or subject.get("credentialId")
    status_ok, status_reason = check_status(credential_id)
    if not status_ok:
        return None, status_reason

    subject_id = subject.get("id") or subject.get("did")
    if not subject_id:
        return None, "missing_subject_id"

    # 5) Authorization Matrix (type → scopes)
    scopes = scopes_for_credential_type(cred_type)
    if not scopes and cred_type != "OrganizationMembership":
        return None, f"no_scopes_for_type:{cred_type}"
    if cred_type == "OrganizationMembership":
        return None, "membership_alone_insufficient"

    authz = {
        "subject_id": subject_id,
        "org_id": subject.get("org") or issuer,
        "role": cred_type,
        "scopes": scopes,
        "assurance": "vc_envelope_ed25519_interim",
        "name": subject.get("name") or cred_type,
        "email": subject.get("email") or "",
        "issuer": issuer,
        "credential_type": cred_type,
        "credential_id": credential_id,
    }
    return authz, None