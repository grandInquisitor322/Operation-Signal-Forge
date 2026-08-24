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
Holder identity key rotation (Phase 2.4).

Independent from credential rotation.
Preserves DID; activates new verification method; retires old.
Does not touch Trust Registry, Authorization Matrix, or credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from identity_runtime.did_document import (
    DidDocumentError,
    create_did_document,
    make_verification_method,
    validate_did_document,
)
from identity_runtime.did_key import generate_keypair
from identity_runtime.did_resolver import LocalDidResolver, get_resolver


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pubkey_multibase_from_did_key(did_key: str) -> str:
    if not did_key.startswith("did:key:"):
        raise DidDocumentError("expected_did_key")
    return did_key[len("did:key:") :]


def establish_identity(
    *,
    identity_type: str = "Person",
    resolver: Optional[LocalDidResolver] = None,
) -> tuple[dict[str, Any], Any, str]:
    """
    Create DID (did:key), document with one active auth method, store locally.
    Returns (doc, private_key, method_id).
    """
    priv, did = generate_keypair()
    mb = _pubkey_multibase_from_did_key(did)
    vm = make_verification_method(did=did, key_id="key-1", public_key_multibase=mb)
    doc = create_did_document(
        did,
        verification_methods=[vm],
        authentication=[vm["id"]],
        identity_type=identity_type,
    )
    r = resolver or get_resolver()
    if hasattr(r, "put"):
        ok, reason = r.put(doc)  # type: ignore[attr-defined]
        if not ok:
            raise DidDocumentError(reason)
    return doc, priv, vm["id"]


def rotate_holder_key(
    did: str,
    *,
    resolver: Optional[LocalDidResolver] = None,
    new_key_id: Optional[str] = None,
) -> tuple[dict[str, Any], Any, str, str]:
    """
    Preserve DID, add new active auth key, retire previous auth keys.
    Returns (updated_doc, new_private_key, new_method_id, retired_method_id).
    """
    r = resolver or get_resolver()
    doc, err = r.resolve(did)
    if err or not doc:
        raise DidDocumentError(err or "did_not_found")

    old_auth = list(doc.get("authentication") or [])
    if not old_auth:
        raise DidDocumentError("no_active_authentication")
    retired_id = old_auth[0]

    priv, did_key = generate_keypair()
    # Document-centric continuity: controller DID string stays fixed;
    # verification material rotates via multibase on the new method.
    mb = _pubkey_multibase_from_did_key(did_key)
    kid = new_key_id or f"key-{len(doc.get('verificationMethod') or []) + 1}"
    new_vm = make_verification_method(did=did, key_id=kid, public_key_multibase=mb)

    vms = []
    for vm in doc.get("verificationMethod") or []:
        if vm.get("id") in old_auth:
            vm = dict(vm)
            vm["status"] = "retired"
            vm["retired"] = _now()
        vms.append(vm)
    vms.append(new_vm)

    updated = dict(doc)
    updated["verificationMethod"] = vms
    updated["authentication"] = [new_vm["id"]]
    updated["updated"] = _now()
    ok, reason = validate_did_document(updated)
    if not ok:
        raise DidDocumentError(reason)
    if hasattr(r, "put"):
        pok, preason = r.put(updated)  # type: ignore[attr-defined]
        if not pok:
            raise DidDocumentError(preason)
    return updated, priv, new_vm["id"], retired_id