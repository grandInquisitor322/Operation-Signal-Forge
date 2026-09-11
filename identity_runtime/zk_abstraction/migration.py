# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""SF-3.5 migration evaluation stubs — policy hooks only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MigrationEvaluation:
    allowed: bool
    reason: str


def evaluate_migration(
    *,
    from_scheme: str,
    to_scheme: str,
    policy_allows: bool,
) -> MigrationEvaluation:
    if not policy_allows:
        return MigrationEvaluation(False, "migration_disallowed_by_policy")
    return MigrationEvaluation(True, "ok")