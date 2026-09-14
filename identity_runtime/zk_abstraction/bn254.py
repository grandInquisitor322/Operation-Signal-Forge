# Copyright 2026 Operation Signal Forge contributors
# Licensed under the Apache License, Version 2.0
"""
BN254 (alt_bn128) affine G1 + Fr public-scalar kernel.

Used by IndependentVerifier for executable NEG-C1-03 / NEG-C2-02 semantics.
No pairing; no silent reduction modulo p or r.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

# Base field Fp (G1 coordinates). y^2 = x^3 + 3.
BN254_P = 21888242871839275222246405745257275088696311157297823662689037894645226208583
# Scalar field Fr (Groth16 public inputs x_i).
BN254_R = 21888242871839275222246405745257275088548364400416034343698204186575808495617
BN254_B = 3
G1_GENERATOR: Tuple[int, int] = (1, 2)

G1Point = Optional[Tuple[int, int]]  # None = point at infinity

PROOF_G1_PREFIX = b"SFG16A:"


@dataclass(frozen=True)
class G1ParseResult:
    x: int
    y: int
    payload: bytes


def _inv(a: int, p: int = BN254_P) -> int:
    return pow(a % p, p - 2, p)


def g1_on_curve(x: int, y: int) -> bool:
    """True iff affine (x, y) lies on BN254 G1. Does not reduce x,y into Fp first."""
    if x < 0 or y < 0 or x >= BN254_P or y >= BN254_P:
        return False
    return (y * y - (x * x * x + BN254_B)) % BN254_P == 0


def g1_add(p: G1Point, q: G1Point) -> G1Point:
    if p is None:
        return q
    if q is None:
        return p
    x1, y1 = p
    x2, y2 = q
    if x1 == x2:
        if (y1 + y2) % BN254_P == 0:
            return None
        lam = (3 * x1 * x1 * _inv(2 * y1)) % BN254_P
    else:
        lam = ((y2 - y1) * _inv(x2 - x1)) % BN254_P
    x3 = (lam * lam - x1 - x2) % BN254_P
    y3 = (lam * (x1 - x3) - y1) % BN254_P
    return x3, y3


def g1_scalar_mul(k: int, point: G1Point) -> G1Point:
    """Double-and-add; scalar is not reduced modulo r (required for [r]P checks)."""
    if point is None or k == 0:
        return None
    if k < 0:
        raise ValueError("negative_scalar")
    acc: G1Point = None
    base = point
    kk = k
    while kk:
        if kk & 1:
            acc = g1_add(acc, base)
        base = g1_add(base, base)
        kk >>= 1
    return acc


def g1_in_prime_subgroup(x: int, y: int) -> bool:
    """BN254 G1 cofactor is 1: every on-curve affine point satisfies [r]P = O."""
    if not g1_on_curve(x, y):
        return False
    return g1_scalar_mul(BN254_R, (x, y)) is None


def validate_g1_affine(x: int, y: int) -> Optional[str]:
    """
    Fail-closed G1 A checks. Coordinates are not reduced modulo p.
    Returns a reason string on failure, else None.
    """
    if x < 0 or y < 0 or x >= BN254_P or y >= BN254_P:
        return "g1_a_coordinate_out_of_range"
    if not g1_on_curve(x, y):
        return "g1_a_off_curve"
    if not g1_in_prime_subgroup(x, y):
        return "g1_a_not_in_subgroup"
    return None


def encode_g1_proof(x: int, y: int, payload: bytes) -> bytes:
    return PROOF_G1_PREFIX + f"{x}:{y}:".encode("ascii") + payload


def parse_g1_proof(proof_bytes: bytes) -> Optional[G1ParseResult]:
    """Parse SFG16A:x:y:payload. Integers are exact (no mod-p)."""
    if not proof_bytes.startswith(PROOF_G1_PREFIX):
        return None
    rest = proof_bytes[len(PROOF_G1_PREFIX) :]
    parts = rest.split(b":", 2)
    if len(parts) != 3:
        raise ValueError("g1_a_malformed_encoding")
    xs, ys, payload = parts
    if not xs or not ys or not xs.isdigit() or not ys.isdigit():
        raise ValueError("g1_a_malformed_encoding")
    return G1ParseResult(x=int(xs), y=int(ys), payload=payload)


def _int_scalar_candidate(value: object) -> Optional[int]:
    if type(value) is int:
        return value
    if isinstance(value, str):
        s = value.strip()
        if s.startswith(("0x", "0X")):
            try:
                return int(s, 16)
            except ValueError:
                return None
        if s.isdigit():
            return int(s, 10)
    return None


def first_public_scalar_out_of_range(
    public: Mapping[str, object],
) -> Optional[tuple[str, int]]:
    """
    Groth16 x_i ∈ Fr. Integers (and numeric strings) must satisfy 0 <= x_i < r.
    No silent reduction modulo r.
    """
    for key, value in public.items():
        if str(key).startswith("_"):
            continue
        xi = _int_scalar_candidate(value)
        if xi is None:
            continue
        if xi < 0 or xi >= BN254_R:
            return key, xi
    return None
