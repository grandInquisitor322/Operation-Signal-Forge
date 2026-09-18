# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5-VER-1..11 — Independent verification engine (fail-closed).
WP7-CAND-01R1 Workstream A + F-1..F-5 + Workstream B taxonomy.
WP7-CAND-01R1.1 R-1 mandatory SFG16A path + R-2 canonical Fr scalars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Set

from identity_runtime.zk_abstraction.acceptance import (
    AcceptanceControlFlowError,
    AcceptanceDecision,
    AcceptanceResult,
    ConditionId,
    ConditionOutcome,
    ConditionResult,
    FAILURE_PRECEDENCE,
    evaluate_acceptance,
)
from identity_runtime.zk_abstraction.result_taxonomy import (
    TaxonomyResult,
    classify_acceptance,
    classify_from_status_reason,
)
from identity_runtime.zk_abstraction.bn254 import (
    PROOF_G1_PREFIX,
    first_public_scalar_violation,
    parse_canonical_fr_decimal,
    parse_g1_proof,
    validate_g1_affine,
)
from identity_runtime.zk_abstraction.c4_policy_wrapper import (
    VerifierPolicyContext,
    c4_to_condition,
    evaluate_c4,
)
from identity_runtime.zk_abstraction.audit import CryptographicAuditLogger
from identity_runtime.zk_abstraction.binder import BindingTarget, ContextClaimBinder
from identity_runtime.zk_abstraction.identity import IdentityTuple
from identity_runtime.zk_abstraction.registry import (
    CryptographicRegistry,
    OperationType,
)

# F-5: allowlist (replaces denylist)
ALLOWED_PUBLIC_KEYS: frozenset[str] = frozenset(
    {
        "context_id",
        "revision",
        "lifecycle_state",
        "incident_type",
        "geographic_applicability",
        "operational_period",
        "authority_reference",
        "authority_role_class",
        "delegated_authority_indication",
        "eligibility_proposition",
        "_ambiguous",
        "_stale",
        "_revoked_material",
        "_superseded",
        "_conflicted",
        "_unverifiable",
        "_malformed",
    }
)

_MISSING = object()  # F-4


class VerificationFailure(Exception):
    def __init__(self, status_code: str, reason: str):
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"{status_code}:{reason}")


@dataclass
class VerificationRequest:
    identity_tuple: IdentityTuple
    proof_bytes: bytes
    verifier_visible_inputs: Dict[str, Any]
    context_id: str
    revision: int
    claim_proposition: str
    required_public_keys: Set[str] = field(
        default_factory=lambda: {
            "context_id",
            "revision",
            "lifecycle_state",
        }
    )
    expected_binding: Optional[BindingTarget] = None


@dataclass
class VerificationResult:
    accepted: bool
    status_code: str
    reason: str
    identity_tuple: IdentityTuple
    binding_target: Any
    acceptance: Optional[AcceptanceResult] = None
    verified_eligibility_claim: bool = False
    authorization_permitted: bool = False
    taxonomy: Optional[TaxonomyResult] = None


MockProofFn = Callable[[bytes, BindingTarget, Mapping[str, Any]], bool]


def default_mock_proof_check(
    proof_bytes: bytes, binding: BindingTarget, public: Mapping[str, Any]
) -> bool:
    expected = ("VALID:" + binding.public_conditions_fingerprint).encode("utf-8")
    return proof_bytes == expected


def _cr(cid: ConditionId, outcome: ConditionOutcome, reason: str = "") -> ConditionResult:
    return ConditionResult(condition_id=cid, outcome=outcome, reason=reason)


def _public_get(public: Mapping[str, Any], key: str) -> Any:
    if key not in public:
        return _MISSING
    return public[key]


def _legacy_status(
    acceptance: AcceptanceResult,
    conditions: Dict[ConditionId, ConditionResult],
) -> tuple[str, str]:
    if acceptance.decision == AcceptanceDecision.VERIFIED_ELIGIBILITY:
        return "OK", acceptance.reason

    reason_map = {
        "context_id_mismatch": "WRONG_CONTEXT",
        "revision_mismatch": "WRONG_REVISION",
        "claim_mismatch": "WRONG_CLAIM",
        "binding_mismatch": "BINDING_MISMATCH",
        "empty_proof": "MALFORMED_PROOF",
        "proof_format_required_sfg16a": "MALFORMED_PROOF",
        "g1_a_off_curve": "MALFORMED_PROOF",
        "g1_a_not_in_subgroup": "MALFORMED_PROOF",
        "g1_a_coordinate_out_of_range": "MALFORMED_PROOF",
        "g1_a_malformed_encoding": "MALFORMED_PROOF",
        "scheme_proof_check_failed": "INVALID_PROOF",
        "no_binding": "UNVERIFIABLE_CONDITION",
        "ambiguous": "AMBIGUOUS_CONDITION",
        "stale": "STALE_CONDITION",
        "revoked_material": "REVOKED_CONDITION",
        "superseded": "SUPERSEDED_CONDITION",
        "conflicted": "CONFLICTED_CONDITION",
        "unverifiable": "UNVERIFIABLE_CONDITION",
        "malformed": "MALFORMED_CONDITION",
        "unregistered_scheme": "UNSUPPORTED_SCHEME",
        "unsupported_protocol_version": "UNSUPPORTED_PROTOCOL",
        "unauthorized_scheme_downgrade": "SCHEME_DOWNGRADE",
        "deprecated_disallowed_by_policy": "SCHEME_DEPRECATED_DISALLOWED",
        "key_not_allowlisted": "OUTSIDE_BOUNDARY_LEAK",
        "proposition_missing": "WRONG_CLAIM",
        "context_id_missing": "WRONG_CONTEXT",
        "revision_missing": "WRONG_REVISION",
    }
    for cid in FAILURE_PRECEDENCE:
        cr = conditions[cid]
        if cr.outcome != ConditionOutcome.PASS:
            if cr.reason in reason_map:
                return reason_map[cr.reason], cr.reason
            if cr.reason.startswith("scalar_ge_field_order:") or cr.reason.startswith(
                "scalar_non_canonical_"
            ):
                return "MALFORMED_CONDITION", cr.reason
            if cr.reason.startswith("missing:"):
                return "MISSING_CONDITION", cr.reason
            if cr.reason.startswith("forbidden_public_key:") or cr.reason.startswith(
                "key_not_allowlisted:"
            ):
                return "OUTSIDE_BOUNDARY_LEAK", cr.reason
            if cr.reason.startswith("lifecycle:"):
                state = cr.reason.split(":", 1)[1]
                return f"{state}_CONDITION", cr.reason
            if cr.reason.startswith("scheme_"):
                if "disabled" in cr.reason:
                    return "SCHEME_DISABLED", cr.reason
                if "retired" in cr.reason:
                    return "SCHEME_RETIRED", cr.reason
            return acceptance.status_code, cr.reason or acceptance.reason
    return acceptance.status_code, acceptance.reason


class IndependentVerifier:
    def __init__(
        self,
        registry: CryptographicRegistry,
        binder: Optional[ContextClaimBinder] = None,
        audit: Optional[CryptographicAuditLogger] = None,
        proof_check: Optional[MockProofFn] = None,
        policy_context: Optional[VerifierPolicyContext] = None,
    ) -> None:
        self.registry = registry
        self.binder = binder or ContextClaimBinder()
        self.audit = audit or CryptographicAuditLogger()
        self.proof_check = proof_check or default_mock_proof_check
        self.policy_context = policy_context

    def verify_proof(self, request: VerificationRequest) -> VerificationResult:
        it = request.identity_tuple
        conditions: Dict[ConditionId, ConditionResult] = {}
        binding: Any = None

        try:
            # Workstream C: C4 protocol/scheme/policy wrapper (no bypass)
            c4_eval = evaluate_c4(
                self.registry,
                it,
                operation=OperationType.PROOF_VERIFICATION,
                policy_context=self.policy_context,
            )
            conditions[ConditionId.C4] = c4_to_condition(c4_eval)

            conditions[ConditionId.C2] = self._eval_c2(request)
            c3, binding = self._eval_c3(request)
            conditions[ConditionId.C3] = c3
            conditions[ConditionId.C1] = self._eval_c1(request, binding)

            acceptance = evaluate_acceptance(conditions)
            status_code, reason = _legacy_status(acceptance, conditions)

            result = VerificationResult(
                accepted=acceptance.accepted,
                status_code=status_code,
                reason=reason,
                identity_tuple=it,
                binding_target=binding if acceptance.accepted else None,
                acceptance=acceptance,
                verified_eligibility_claim=acceptance.verified_eligibility_claim,
                authorization_permitted=False,
            )
        except AcceptanceControlFlowError as e:
            # F-3
            result = VerificationResult(
                accepted=False,
                status_code=getattr(e, "status_code", "STRUCTURAL_FAILURE"),
                reason=str(e),
                identity_tuple=it,
                binding_target=None,
                acceptance=None,
                verified_eligibility_claim=False,
                authorization_permitted=False,
            )
        except Exception as e:  # noqa: BLE001
            result = VerificationResult(
                accepted=False,
                status_code="UNVERIFIABLE_CONDITION",
                reason=f"verifier_exception:{type(e).__name__}",
                identity_tuple=it,
                binding_target=None,
                acceptance=None,
                verified_eligibility_claim=False,
                authorization_permitted=False,
            )

        # Workstream B: SF-3.5-VER-5 taxonomy (does not alter C1-C4 AND)
        if result.acceptance is not None:
            result.taxonomy = classify_acceptance(result.acceptance)
        else:
            result.taxonomy = classify_from_status_reason(
                accepted=result.accepted,
                status_code=result.status_code,
                reason=result.reason,
            )
        result.authorization_permitted = False
        if result.taxonomy is not None:
            result.verified_eligibility_claim = (
                result.taxonomy.verified_eligibility_claim
            )

        # F-3: always audit
        try:
            self.audit.log_verification(
                context_id=request.context_id,
                revision=request.revision,
                claim_id=(request.claim_proposition or "")[:64],
                identity_tuple=it,
                verification_outcome=result.status_code,
            )
        except Exception:  # noqa: BLE001
            pass

        return result

    def _eval_c2(self, request: VerificationRequest) -> ConditionResult:
        public = request.verifier_visible_inputs

        for k in public:
            if k not in ALLOWED_PUBLIC_KEYS:
                return _cr(
                    ConditionId.C2,
                    ConditionOutcome.FAIL,
                    f"key_not_allowlisted:{k}",
                )

        for key in request.required_public_keys:
            val = _public_get(public, key)
            if val is _MISSING or val is None:
                return _cr(ConditionId.C2, ConditionOutcome.FAIL, f"missing:{key}")

        if public.get("_ambiguous"):
            return _cr(ConditionId.C2, ConditionOutcome.AMBIGUOUS, "ambiguous")
        lifecycle = public.get("lifecycle_state")
        if lifecycle in ("EXPIRED", "REVOKED", "SUPERSEDED"):
            return _cr(
                ConditionId.C2, ConditionOutcome.FAIL, f"lifecycle:{lifecycle}"
            )
        if public.get("_stale"):
            return _cr(ConditionId.C2, ConditionOutcome.FAIL, "stale")
        if public.get("_revoked_material"):
            return _cr(ConditionId.C2, ConditionOutcome.FAIL, "revoked_material")
        if public.get("_superseded"):
            return _cr(ConditionId.C2, ConditionOutcome.FAIL, "superseded")
        if public.get("_conflicted"):
            return _cr(ConditionId.C2, ConditionOutcome.FAIL, "conflicted")
        if public.get("_unverifiable"):
            return _cr(ConditionId.C2, ConditionOutcome.UNVERIFIABLE, "unverifiable")
        if public.get("_malformed"):
            return _cr(ConditionId.C2, ConditionOutcome.MALFORMED, "malformed")
        viol = first_public_scalar_violation(public, scalar_keys=("revision",))
        if viol is not None:
            key, err = viol
            return _cr(
                ConditionId.C2,
                ConditionOutcome.MALFORMED,
                f"{err}:{key}",
            )
        return _cr(ConditionId.C2, ConditionOutcome.PASS, "ok")

    def _eval_c3(
        self, request: VerificationRequest
    ) -> tuple[ConditionResult, Optional[BindingTarget]]:
        public = request.verifier_visible_inputs

        if not request.claim_proposition:
            return (
                _cr(ConditionId.C3, ConditionOutcome.FAIL, "proposition_missing"),
                None,
            )

        try:
            binding = self.binder.compute_target(
                context_id=request.context_id,
                revision=request.revision,
                eligibility_proposition=request.claim_proposition,
                public_conditions=public,
            )
        except Exception as e:  # noqa: BLE001
            return _cr(ConditionId.C3, ConditionOutcome.UNVERIFIABLE, str(e)), None

        ctx_val = _public_get(public, "context_id")
        if ctx_val is _MISSING:
            pass
        elif ctx_val is None:
            return (
                _cr(ConditionId.C3, ConditionOutcome.FAIL, "context_id_missing"),
                binding,
            )
        elif ctx_val != request.context_id:
            return (
                _cr(ConditionId.C3, ConditionOutcome.FAIL, "context_id_mismatch"),
                binding,
            )

        rev_val = _public_get(public, "revision")
        if rev_val is _MISSING:
            pass
        elif rev_val is None:
            return (
                _cr(ConditionId.C3, ConditionOutcome.FAIL, "revision_missing"),
                binding,
            )
        else:
            rev_parsed, rev_err = parse_canonical_fr_decimal(rev_val)
            if rev_err is not None or rev_parsed != request.revision:
                return (
                    _cr(ConditionId.C3, ConditionOutcome.FAIL, "revision_mismatch"),
                    binding,
                )

        prop_val = _public_get(public, "eligibility_proposition")
        if prop_val is _MISSING:
            pass
        elif prop_val is None:
            return (
                _cr(ConditionId.C3, ConditionOutcome.FAIL, "proposition_missing"),
                binding,
            )
        elif prop_val != request.claim_proposition:
            return (
                _cr(ConditionId.C3, ConditionOutcome.FAIL, "claim_mismatch"),
                binding,
            )

        if request.expected_binding is not None and request.expected_binding != binding:
            return (
                _cr(ConditionId.C3, ConditionOutcome.FAIL, "binding_mismatch"),
                binding,
            )
        return _cr(ConditionId.C3, ConditionOutcome.PASS, "ok"), binding

    def _eval_c1(
        self, request: VerificationRequest, binding: Optional[BindingTarget]
    ) -> ConditionResult:
        """
        R1.1-A: verifier-selected validation path only.
        Required format SFG16A. Unprefixed proofs MUST NOT fall through
        to legacy payload-equality acceptance.
        """
        if binding is None:
            return _cr(ConditionId.C1, ConditionOutcome.UNVERIFIABLE, "no_binding")
        if not request.proof_bytes:
            return _cr(ConditionId.C1, ConditionOutcome.MALFORMED, "empty_proof")

        if not request.proof_bytes.startswith(PROOF_G1_PREFIX):
            return _cr(
                ConditionId.C1,
                ConditionOutcome.MALFORMED,
                "proof_format_required_sfg16a",
            )

        try:
            g1 = parse_g1_proof(request.proof_bytes)
        except ValueError as e:
            return _cr(ConditionId.C1, ConditionOutcome.MALFORMED, str(e))
        if g1 is None:
            return _cr(
                ConditionId.C1,
                ConditionOutcome.MALFORMED,
                "proof_format_required_sfg16a",
            )

        g1_reason = validate_g1_affine(g1.x, g1.y)
        if g1_reason:
            return _cr(ConditionId.C1, ConditionOutcome.MALFORMED, g1_reason)

        proof_for_check = g1.payload
        if not proof_for_check:
            return _cr(ConditionId.C1, ConditionOutcome.MALFORMED, "empty_proof")

        try:
            ok = self.proof_check(
                proof_for_check, binding, request.verifier_visible_inputs
            )
        except Exception as e:  # noqa: BLE001
            return _cr(ConditionId.C1, ConditionOutcome.UNVERIFIABLE, str(e))
        if not ok:
            return _cr(ConditionId.C1, ConditionOutcome.FAIL, "scheme_proof_check_failed")
        return _cr(ConditionId.C1, ConditionOutcome.PASS, "ok")