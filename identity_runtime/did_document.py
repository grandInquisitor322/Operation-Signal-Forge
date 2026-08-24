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
Local DID Document model (Phase 2.4).

VerificationMethod lists keys that *exist*.
authentication[] lists which methods may authenticate.
A key in verificationMethod is NOT automatically valid for every purpose.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DidDocumentError(ValueError):
    pass


def make_verification_method(
    *,
    did: str,
    key_id: str,
    public_key_multibase: str,
    controller: Optional[str] = None,
    type_name: str = "Ed25519VerificationKey2020",
) -> dict[str, Any]:
    frag = key_id if key_id.startswith("#") else f"#{key_id}"
    full_id = f"{did}{frag}" if not key_id.startswith(did) else key_id
    return {
        "id": full_id,
        "type": type_name,
        "controller": controller or did,
        "publicKeyMultibase": public_key_multibase,
        "status": "active",
        "created": _now(),
        "retired": None,
    }


def create_did_document(
    did: str,
    *,
    verification_methods: list[dict[str, Any]],
    authentication: Optional[list[str]] = None,
    also_known_as: Optional[list[str]] = None,
    identity_type: str = "Person",
) -> dict[str, Any]:
    if not did or not did.startswith("did:"):
        raise DidDocumentError("invalid_did")
    if not verification_methods:
        raise DidDocumentError("missing_verification_method")
    vm_ids = {vm["id"] for vm in verification_methods}
    auth = authentication
    if auth is None:
        # Default: only first method is authentication-capable
        auth = [verification_methods[0]["id"]]
    for a in auth:
        if a not in vm_ids:
            raise DidDocumentError("authentication_references_unknown_method")
    return {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": did,
        "identityType": identity_type,
        "verificationMethod": list(verification_methods),
        "authentication": list(auth),
        "alsoKnownAs": list(also_known_as or []),
        "updated": _now(),
    }


def validate_did_document(doc: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "not_an_object"
    did = doc.get("id")
    if not did or not str(did).startswith("did:"):
        return False, "invalid_did"
    vms = doc.get("verificationMethod")
    if not isinstance(vms, list) or not vms:
        return False, "missing_verification_method"
    ids = set()
    for vm in vms:
        if not isinstance(vm, dict):
            return False, "invalid_verification_method"
        vid = vm.get("id")
        if not vid or not vm.get("publicKeyMultibase"):
            return False, "incomplete_verification_method"
        if vid in ids:
            return False, "duplicate_verification_method_id"
        ids.add(vid)
        if vm.get("status") not in (None, "active", "retired"):
            return False, "invalid_method_status"
    auth = doc.get("authentication") or []
    if not isinstance(auth, list):
        return False, "invalid_authentication"
    for a in auth:
        if a not in ids:
            return False, "authentication_references_unknown_method"
    return True, "ok"


def get_method(doc: dict[str, Any], method_id: str) -> Optional[dict[str, Any]]:
    for vm in doc.get("verificationMethod") or []:
        if vm.get("id") == method_id:
            return vm
    return None


def active_authentication_methods(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Methods that are both in authentication[] and status active."""
    auth_ids = set(doc.get("authentication") or [])
    out = []
    for vm in doc.get("verificationMethod") or []:
        if vm.get("id") in auth_ids and (vm.get("status") or "active") == "active":
            out.append(vm)
    return out


def is_authentication_capable(doc: dict[str, Any], method_id: str) -> bool:
    vm = get_method(doc, method_id)
    if not vm:
        return False
    if (vm.get("status") or "active") != "active":
        return False
    return method_id in (doc.get("authentication") or [])