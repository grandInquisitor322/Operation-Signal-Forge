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
DID Resolver abstraction + local file-backed resolver (Phase 2.4 / 2.5).

resolve(did) -> DID Document
Does NOT imply issuer trust (Trust Registry is separate).
Method policy gate via validate_did_for_runtime (accepted ≠ managed).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional, Protocol

from identity_runtime.did_document import validate_did_document

DEFAULT_STORE = Path(__file__).resolve().parent.parent / "dapp_api" / "did_store"


class DidResolver(Protocol):
    def resolve(self, did: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        """Returns (document, error)."""
        ...


def _safe_filename(did: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", did)


class LocalDidResolver:
    """Repository/file local resolver."""

    def __init__(self, store_dir: Optional[Path] = None) -> None:
        self.store_dir = Path(store_dir or DEFAULT_STORE)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, did: str) -> Path:
        return self.store_dir / f"{_safe_filename(did)}.json"

    def put(self, doc: dict[str, Any]) -> tuple[bool, str]:
        ok, reason = validate_did_document(doc)
        if not ok:
            return False, reason
        did = doc["id"]
        self.path_for(did).write_text(json.dumps(doc, indent=2), encoding="utf-8")
        return True, "stored"

    def resolve(self, did: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        from identity_runtime.did_method_policy import validate_did_for_runtime

        ok, reason = validate_did_for_runtime(did)
        if not ok:
            return None, reason

        path = self.path_for(did)
        if not path.exists():
            return None, "did_not_found"
        try:
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            return None, "malformed_did_document"
        ok, reason = validate_did_document(doc)
        if not ok:
            return None, reason
        if doc.get("id") != did:
            return None, "did_document_id_mismatch"
        return doc, None


_default_resolver: DidResolver = LocalDidResolver()


def get_resolver() -> DidResolver:
    return _default_resolver


def set_resolver(resolver: DidResolver) -> None:
    global _default_resolver
    _default_resolver = resolver


def resolve(did: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Module entry point — delegates to the configured resolver instance."""
    return get_resolver().resolve(did)