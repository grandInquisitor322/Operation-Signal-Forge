# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5-VER-1..11 — Independent verification engine (fail-closed).
WP7-CAND-01R1 Workstream A + F-1..F-5 + Workstream B taxonomy.
WP7-CAND-01R1.1 R-1/R-2 + Gate 6 SchemeVerifier boundary.
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
from identity_runtime.zk_abstraction.canonical_public import (
    first_public_scalar_violation,
    parse_canonical_decimal,
)
from identity_runtime.zk_abstraction.scheme_types import (
    BoundStatementTarget,
    CryptoOutcome,
    CryptoValidityResult,
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
    """Legacy seam only — Gate 6 C1 uses SchemeVerifier, not this path."""
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
        "scheme_unsupported": "UNSUPPORTED_SCHEME",
        "materials_unavailable": "UNSUPPORTED_SCHEME",
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
            # Adapter may return reason_code:detail
            base = cr.reason.split(":", 1)[0] if cr.reason else ""
            if base in reason_map:
                return reason_map[base], cr.reason
            if base in (
                "g1_a_off_curve",
                "g1_a_not_in_subgroup",
                "g1_a_coordinate_out_of_range",
                "g1_a_malformed_encoding",
                "proof_format_required_sfg16a",
                "proof_parse_error",
                "empty_proof",
            ):
                return "MALFORMED_PROOF", cr.reason
            if base == "scheme_proof_check_failed":
                return "INVALID_PROOF", cr.reason
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
        # Kept for back-compat only; Gate 6 C1 does not call this.
        self.proof_check = proof_check or default_mock_proof_check
        self.policy_context = policy_context

    def verify_proof(self, request: VerificationRequest) -> VerificationResult:
        it = request.identity_tuple
        conditions: Dict[ConditionId, ConditionResult] = {}
        binding: Any = None

        try:
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

        modulus = None
        try:
            desc = self.registry.resolve_scheme(
                request.identity_tuple.scheme_id,
                request.identity_tuple.scheme_version,
            )
            modulus = getattr(desc, "public_scalar_modulus", None)
        except KeyError:
            modulus = None
        viol = first_public_scalar_violation(
            public, scalar_keys=("revision",), modulus=modulus
        )
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
            rev_parsed, rev_err = parse_canonical_decimal(rev_val)
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

    def _build_bound_statement(
        self,
        request: VerificationRequest,
        binding: Optional[BindingTarget],
        materials_ref: str,
    ) -> BoundStatementTarget:
        public = request.verifier_visible_inputs
        view = {
            str(k): (v if type(v) is str else (str(v) if v is not None else ""))
            for k, v in public.items()
            if not str(k).startswith("_")
        }
        if "revision" in public and type(public["revision"]) is not str:
            view["revision"] = str(public["revision"])
        it = request.identity_tuple
        sid = f"{it.scheme_id}@{it.scheme_version}:{request.context_id}:{request.revision}"
        return BoundStatementTarget(
            statement_id=sid,
            scheme_id=it.scheme_id,
            scheme_version=it.scheme_version,
            materials_ref=materials_ref,
            public_input_view=view,
            context_id=str(request.context_id),
            revision=str(request.revision),
            eligibility_proposition=request.claim_proposition or "",
            relation_hint=(binding.public_conditions_fingerprint if binding else ""),
        )

    def _map_crypto_to_c1(self, crypto: CryptoValidityResult) -> ConditionResult:
        mapping = {
            CryptoOutcome.PASS: ConditionOutcome.PASS,
            CryptoOutcome.FAIL: ConditionOutcome.FAIL,
            CryptoOutcome.MALFORMED: ConditionOutcome.MALFORMED,
            CryptoOutcome.UNVERIFIABLE: ConditionOutcome.UNVERIFIABLE,
            CryptoOutcome.UNSUPPORTED: ConditionOutcome.UNSUPPORTED,
        }
        outcome = mapping.get(crypto.outcome, ConditionOutcome.UNVERIFIABLE)
        reason = crypto.reason_code
        if crypto.reason_detail and crypto.reason_detail != crypto.reason_code:
            reason = f"{crypto.reason_code}:{crypto.reason_detail}"
        return _cr(ConditionId.C1, outcome, reason)

    def _eval_c1(
        self, request: VerificationRequest, binding: Optional[BindingTarget]
    ) -> ConditionResult:
        """Gate 6: C1 via SchemeVerifier only (no BN254/SFG16A in orchestrator)."""
        if binding is None:
            return _cr(ConditionId.C1, ConditionOutcome.UNVERIFIABLE, "no_binding")
        it = request.identity_tuple
        try:
            desc = self.registry.resolve_scheme(it.scheme_id, it.scheme_version)
            materials_ref = desc.scheme_material_ref
        except KeyError:
            return _cr(ConditionId.C1, ConditionOutcome.UNSUPPORTED, "scheme_unsupported")
        try:
            verifier = self.registry.resolve_verifier(it.scheme_id, it.scheme_version)
        except KeyError:
            return _cr(
                ConditionId.C1, ConditionOutcome.UNSUPPORTED, "materials_unavailable"
            )
        bound = self._build_bound_statement(request, binding, materials_ref)
        try:
            crypto = verifier.verify_crypto(request.proof_bytes, bound)
        except Exception as e:  # noqa: BLE001
            return _cr(
                ConditionId.C1,
                ConditionOutcome.UNVERIFIABLE,
                f"verifier_exception:{type(e).__name__}",
            )
        if not isinstance(crypto, CryptoValidityResult):
            return _cr(
                ConditionId.C1, ConditionOutcome.UNVERIFIABLE, "verifier_exception"
            )
        return self._map_crypto_to_c1(crypto)