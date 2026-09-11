# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5-PROTO-2.1 — governed identity tuple (metadata, not auto public input)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdentityTuple:
    """Protocol/scheme/policy identity. Membership does NOT auto-make public inputs."""

    protocol_id: str
    protocol_version: str
    scheme_id: str
    scheme_version: str
    policy_version: str