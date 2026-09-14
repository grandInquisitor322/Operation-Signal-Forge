# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""
WP7-CAND-01R1 Workstream E — Authorization isolation boundary.

ZK verification → verified eligibility claim → Authorization Matrix

Authorization requires an explicit positive verified eligibility claim.
Non-success verification, missing/false/None claims, raw credentials, and
permissive defaults never authorize. Does not assert subject ineligibility
from verification failure (preserves Workstream B taxonomy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from identity_runtime.zk_abstraction.result_taxonomy import VerificationOutcomeClass
from identity_runtime.zk_abstraction.verifier import VerificationResult


@dataclass(frozen=True)
class VerifiedEligibilityClaim:
    positive: bool
    context_id: str
    revision: int
    scheme_id: str
    scheme_version: str
    source: str = "zk_verification"

    def is_usable(self) -> bool:
        return (
            self.positive is True
            and bool(self.context_id)
            and self.revision is not None
            and bool(self.scheme_id)
            and self.source == "zk_verification"
        )


@dataclass
class AuthorizationRequest:
    verified_claim: Optional[VerifiedEligibilityClaim] = None
    role: Optional[str] = None
    scopes: tuple[str, ...] = ()
    raw_credential: Optional[Mapping[str, Any]] = None
    force_authorize: bool = False
    default_allow: bool = False
    asserted_eligibility: Optional[bool] = None


@dataclass(frozen=True)
class AuthorizationDecision:
    permitted: bool
    reason: str
    status_code: str
    had_positive_verified_claim: bool
    used_raw_credential: bool = False
    used_force_or_default: bool = False


def claim_from_verification(result: VerificationResult) -> Optional[VerifiedEligibilityClaim]:
    if result is None:
        return None
    if not result.accepted:
        return None
    if not result.verified_eligibility_claim:
        return None
    if result.taxonomy is not None:
        if result.taxonomy.outcome != VerificationOutcomeClass.VERIFIED_ELIGIBILITY:
            return None
        if not result.taxonomy.verified_eligibility_claim:
            return None
    it = result.identity_tuple
    ctx = ""
    rev = 0
    if result.binding_target is not None:
        ctx = getattr(result.binding_target, "context_id", "") or ""
        rev = int(getattr(result.binding_target, "revision", 0) or 0)
    return VerifiedEligibilityClaim(
        positive=True,
        context_id=ctx or "bound",
        revision=rev,
        scheme_id=it.scheme_id,
        scheme_version=it.scheme_version,
        source="zk_verification",
    )


def authorize(request: AuthorizationRequest) -> AuthorizationDecision:
    used_raw = request.raw_credential is not None
    used_force = bool(request.force_authorize or request.default_allow)
    claim = request.verified_claim

    if claim is None:
        return AuthorizationDecision(
            permitted=False,
            reason="missing_verified_eligibility_claim",
            status_code="AUTHZ_DENIED_NO_CLAIM",
            had_positive_verified_claim=False,
            used_raw_credential=used_raw,
            used_force_or_default=used_force,
        )

    if claim.positive is not True:
        return AuthorizationDecision(
            permitted=False,
            reason="claim_not_positive",
            status_code="AUTHZ_DENIED_CLAIM_FALSE",
            had_positive_verified_claim=False,
            used_raw_credential=used_raw,
            used_force_or_default=used_force,
        )

    if not claim.is_usable():
        return AuthorizationDecision(
            permitted=False,
            reason="claim_unusable_or_wrong_source",
            status_code="AUTHZ_DENIED_CLAIM_MALFORMED",
            had_positive_verified_claim=False,
            used_raw_credential=used_raw,
            used_force_or_default=used_force,
        )

    return AuthorizationDecision(
        permitted=True,
        reason="verified_eligibility_claim_accepted",
        status_code="AUTHZ_PERMITTED",
        had_positive_verified_claim=True,
        used_raw_credential=used_raw,
        used_force_or_default=used_force,
    )


def authorize_from_verification(
    result: VerificationResult,
    *,
    raw_credential: Optional[Mapping[str, Any]] = None,
    force_authorize: bool = False,
    default_allow: bool = False,
    role: Optional[str] = None,
    scopes: tuple[str, ...] = (),
) -> AuthorizationDecision:
    claim = claim_from_verification(result)
    return authorize(
        AuthorizationRequest(
            verified_claim=claim,
            role=role,
            scopes=scopes,
            raw_credential=raw_credential,
            force_authorize=force_authorize,
            default_allow=default_allow,
        )
    )