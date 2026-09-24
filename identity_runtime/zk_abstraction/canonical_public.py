# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""Scheme-neutral canonical public-input representation (Stage 3.4 / Gate 6)."""

from __future__ import annotations

from typing import Mapping, Optional, Tuple


def parse_canonical_decimal(value: object) -> Tuple[Optional[int], Optional[str]]:
    if type(value) is not str:
        return None, f"scalar_non_canonical_type:{type(value).__name__}"
    s = value
    if any(ord(c) <= 32 for c in s):
        return None, "scalar_non_canonical_whitespace"
    if not s:
        return None, "scalar_non_canonical_empty"
    if any(c in s for c in "+-.,eE_,"):
        return None, "scalar_non_canonical_charset"
    if not all(c in "0123456789" for c in s):
        return None, "scalar_non_canonical_charset"
    if len(s) > 1 and s.startswith("0"):
        return None, "scalar_non_canonical_leading_zero"
    xi = int(s, 10)
    if xi < 0:
        return None, "scalar_negative"
    return xi, None


def apply_scalar_modulus(
    xi: int, modulus: Optional[int]
) -> Tuple[Optional[int], Optional[str]]:
    if modulus is None:
        return xi, None
    if modulus <= 0:
        return None, "scalar_modulus_invalid"
    if xi >= modulus:
        return None, f"scalar_ge_field_order:x_i={xi}"
    return xi, None


def parse_canonical_decimal_with_modulus(
    value: object, modulus: Optional[int] = None
) -> Tuple[Optional[int], Optional[str]]:
    xi, err = parse_canonical_decimal(value)
    if err is not None:
        return None, err
    assert xi is not None
    return apply_scalar_modulus(xi, modulus)


def first_public_scalar_violation(
    public: Mapping[str, object],
    scalar_keys: tuple[str, ...] = ("revision",),
    *,
    modulus: Optional[int] = None,
) -> Optional[tuple[str, str]]:
    for key in scalar_keys:
        if key not in public:
            continue
        _xi, err = parse_canonical_decimal_with_modulus(public[key], modulus)
        if err is not None:
            return key, err
    return None