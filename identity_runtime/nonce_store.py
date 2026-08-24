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
Production-oriented challenge/nonce store (Phase 2.5 hardening).

Lifecycle: issued (pending) → consumed | expired → purged.

Presentation semantics are unchanged — this only makes replay protection
durable across process restarts (and multi-worker if they share the file).

Does not touch credential lifecycle, Trust Registry, or Authorization Matrix.
"""

from __future__ import annotations

import json
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent / "dapp_api" / "nonce_store.json"
)

DEFAULT_TTL_SECONDS = int(os.environ.get("SF_NONCE_TTL_SECONDS", "300"))
DEFAULT_CONSUMED_RETENTION_SECONDS = int(
    os.environ.get("SF_NONCE_CONSUMED_RETENTION_SECONDS", "86400")
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


class NonceStore(Protocol):
    def issue(
        self, *, audience: str, ttl_seconds: Optional[int] = None
    ) -> dict[str, Any]:
        ...

    def consume(self, nonce: str, *, audience: str) -> tuple[bool, str]:
        ...

    def purge_expired(self, *, now: Optional[datetime] = None) -> int:
        ...


class FileNonceStore:
    """
    File-backed nonce store (JSON object keyed by nonce).

    States per record:
      status: pending | consumed
      audience, issued_at, expires_at, consumed_at?
    """

    def __init__(
        self,
        path: Optional[Path] = None,
        *,
        default_ttl_seconds: int = DEFAULT_TTL_SECONDS,
        consumed_retention_seconds: int = DEFAULT_CONSUMED_RETENTION_SECONDS,
    ) -> None:
        self.path = Path(path or DEFAULT_PATH)
        self.default_ttl_seconds = default_ttl_seconds
        self.consumed_retention_seconds = consumed_retention_seconds
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"nonces": {}})

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"nonces": {}}
        data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        if "nonces" not in data:
            data = {"nonces": data if isinstance(data, dict) else {}}
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def issue(
        self, *, audience: str, ttl_seconds: Optional[int] = None
    ) -> dict[str, Any]:
        if not audience:
            raise ValueError("missing_audience")
        ttl = self.default_ttl_seconds if ttl_seconds is None else int(ttl_seconds)
        now = _now()
        nonce = secrets.token_urlsafe(16)
        record = {
            "status": "pending",
            "audience": audience,
            "issued_at": _iso(now),
            "expires_at": _iso(now + timedelta(seconds=ttl)),
            "consumed_at": None,
        }
        with self._lock:
            data = self._read()
            # Extremely unlikely collision; regenerate if needed
            while nonce in data["nonces"]:
                nonce = secrets.token_urlsafe(16)
            data["nonces"][nonce] = record
            self._write(data)
        return {
            "nonce": nonce,
            "audience": audience,
            "issuedAt": record["issued_at"],
            "expiresAt": record["expires_at"],
        }

    def consume(self, nonce: str, *, audience: str) -> tuple[bool, str]:
        if not nonce:
            return False, "invalid_nonce"
        if not audience:
            return False, "missing_audience"
        now = _now()
        with self._lock:
            data = self._read()
            rec = data["nonces"].get(nonce)
            if rec is None:
                return False, "invalid_nonce"
            if rec.get("audience") != audience:
                return False, "audience_mismatch"
            status = rec.get("status")
            if status == "consumed":
                return False, "replay_detected"
            try:
                exp = _parse(rec["expires_at"])
            except (KeyError, ValueError):
                return False, "invalid_challenge_expiry"
            # Small skew tolerance (30s) for clock drift
            if exp + timedelta(seconds=30) < now:
                rec["status"] = "pending"  # leave for purge as expired conceptually
                # Mark explicitly expired by not consuming; delete or leave
                return False, "nonce_expired"
            if status != "pending":
                return False, f"nonce_status_{status}"
            rec["status"] = "consumed"
            rec["consumed_at"] = _iso(now)
            data["nonces"][nonce] = rec
            self._write(data)
        return True, "ok"

    def purge_expired(self, *, now: Optional[datetime] = None) -> int:
        """Remove expired pending nonces and aged consumed records."""
        now = now or _now()
        removed = 0
        with self._lock:
            data = self._read()
            keep: dict[str, Any] = {}
            for nonce, rec in data["nonces"].items():
                status = rec.get("status")
                try:
                    exp = _parse(rec["expires_at"])
                except (KeyError, ValueError):
                    removed += 1
                    continue
                if status == "pending" and exp < now:
                    removed += 1
                    continue
                if status == "consumed":
                    consumed_at = rec.get("consumed_at")
                    if consumed_at:
                        try:
                            c = _parse(consumed_at)
                            if c + timedelta(
                                seconds=self.consumed_retention_seconds
                            ) < now:
                                removed += 1
                                continue
                        except ValueError:
                            removed += 1
                            continue
                    elif exp + timedelta(
                        seconds=self.consumed_retention_seconds
                    ) < now:
                        removed += 1
                        continue
                keep[nonce] = rec
            data["nonces"] = keep
            self._write(data)
        return removed


# Process-wide default (file-backed)
_default_store: NonceStore = FileNonceStore()


def get_nonce_store() -> NonceStore:
    return _default_store


def set_nonce_store(store: NonceStore) -> None:
    global _default_store
    _default_store = store