"""Server-side authorization — mock users, real matrix enforcement."""

from __future__ import annotations

import secrets
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

USERS: dict[str, dict[str, Any]] = {
    "analyst@example.org": {
        "password": "analyst",
        "name": "Alex Analyst",
        "role": "HumanitarianAnalyst",
        "scopes": [
            "detections:read",
            "detections:list",
            "capabilities:invoke",
            "capabilities:invoke:investigate",
        ],
        "did": "did:example:analyst-001",
        "org": "did:example:org-relief-alpha",
    },
    "commander@example.org": {
        "password": "commander",
        "name": "Casey Commander",
        "role": "IncidentCommander",
        "scopes": [
            "detections:read",
            "detections:list",
            "capabilities:invoke",
            "capabilities:invoke:investigate",
            "cells:status:write",
            "alerts:subscribe",
        ],
        "did": "did:example:commander-001",
        "org": "did:example:org-relief-alpha",
    },
    "research@example.org": {
        "password": "research",
        "name": "Riley Research",
        "role": "ResearchPartner",
        "scopes": ["detections:read", "detections:list"],
        "did": "did:example:research-001",
        "org": "did:example:org-partner-research",
    },
}

CAPABILITY_REQUIRED_SCOPES: dict[str, list[str]] = {
    "ping": [],
    "generate_detection_brief": ["capabilities:invoke", "detections:read"],
    "recommend_next_sensor": ["capabilities:invoke", "detections:read"],
    "investigate_anomaly": [
        "capabilities:invoke:investigate",
        "detections:read",
    ],
    "execute_sandbox_task": ["capabilities:invoke"],
}

TOKEN_TTL_SECONDS = 8 * 60 * 60
_tokens: dict[str, dict[str, Any]] = {}


@dataclass
class AuthZContext:
    subject_id: str
    org_id: str
    role: str
    scopes: list[str]
    assurance: str = "mock_password"
    expires_at: float = 0.0
    presentation_id: str = ""
    name: str = ""
    email: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def has_scopes(self, required: list[str]) -> bool:
        have = set(self.scopes)
        return all(s in have for s in required)


def login(
    email: str, password: str
) -> tuple[Optional[str], Optional[AuthZContext], Optional[str]]:
    key = (email or "").strip().lower()
    user = USERS.get(key)
    if not user or user["password"] != password:
        return None, None, "Invalid credentials"

    now = time.time()
    ctx = AuthZContext(
        subject_id=user["did"],
        org_id=user["org"],
        role=user["role"],
        scopes=list(user["scopes"]),
        assurance="mock_password",
        expires_at=now + TOKEN_TTL_SECONDS,
        presentation_id=secrets.token_hex(8),
        name=user["name"],
        email=key,
    )
    token = secrets.token_urlsafe(32)
    _tokens[token] = {"ctx": ctx, "expires_at": ctx.expires_at}
    return token, ctx, None


def logout(token: str) -> None:
    _tokens.pop(token, None)


def resolve_token(
    token: Optional[str],
) -> tuple[Optional[AuthZContext], Optional[str]]:
    if not token:
        return None, "Missing authorization token"
    entry = _tokens.get(token)
    if not entry:
        return None, "Invalid or expired token"
    if time.time() > entry["expires_at"]:
        _tokens.pop(token, None)
        return None, "Token expired"
    return entry["ctx"], None


def authorize_capability(
    ctx: AuthZContext, capability: str
) -> tuple[bool, Optional[str]]:
    required = CAPABILITY_REQUIRED_SCOPES.get(capability)
    if required is None:
        return False, f"Unknown capability: {capability}"
    if not ctx.has_scopes(required):
        missing = [s for s in required if s not in ctx.scopes]
        return False, f"Insufficient scope for {capability}; missing: {missing}"
    return True, None