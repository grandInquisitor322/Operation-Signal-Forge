# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5-AUD-1..8 — minimal non-sensitive cryptographic audit log."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from identity_runtime.zk_abstraction.identity import IdentityTuple

FORBIDDEN_AUDIT_KEYS: Set[str] = {
    "witness",
    "private_witness",
    "secret",
    "private_key",
    "proof_witness",
    "credential_raw",
    "sk",
    "trapdoor",
}


class CryptographicAuditLogger:
    """Logs operational metadata only; asserts no witness/secrets (SF-3.5-AUD-4)."""

    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    def log_verification(
        self,
        *,
        context_id: str,
        revision: int,
        claim_id: str,
        identity_tuple: IdentityTuple,
        verification_outcome: str,
        extra: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "context_id": context_id,
            "revision": revision,
            "claim_id": claim_id,
            "identity_tuple": {
                "protocol_id": identity_tuple.protocol_id,
                "protocol_version": identity_tuple.protocol_version,
                "scheme_id": identity_tuple.scheme_id,
                "scheme_version": identity_tuple.scheme_version,
                "policy_version": identity_tuple.policy_version,
            },
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "verification_outcome": verification_outcome,
        }
        if extra:
            payload["extra"] = extra
        self._assert_no_secrets(payload)
        self.entries.append(payload)
        return payload

    def _assert_no_secrets(self, payload: Dict[str, Any]) -> None:
        flat = _flatten_keys(payload)
        for k in flat:
            lk = k.lower()
            for forbidden in FORBIDDEN_AUDIT_KEYS:
                if forbidden in lk:
                    raise ValueError(f"SF-3.5-AUD-4_forbidden_audit_field:{k}")


def _flatten_keys(obj: Any, prefix: str = "") -> List[str]:
    keys: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            keys.append(p)
            keys.extend(_flatten_keys(v, p))
    return keys