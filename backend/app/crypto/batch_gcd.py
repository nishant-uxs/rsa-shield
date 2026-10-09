"""Pairwise / batch GCD across an in-inventory modulus set (Heninger-style shared primes).

For small inventories we use naive pairwise GCD (educational scale). Large Internet-scale
batch product trees (USENIX'12) are out of scope for this prototype.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd


@dataclass
class SharedFactorHit:
    i: int
    j: int
    factor: int
    key_id_a: str
    key_id_b: str


@dataclass
class BatchGcdResult:
    moduli_count: int
    pairs_checked: int
    hits: list[SharedFactorHit]
    message: str


def batch_gcd(
    moduli: list[int],
    key_ids: list[str] | None = None,
) -> BatchGcdResult:
    if key_ids is None:
        key_ids = [str(i) for i in range(len(moduli))]
    if len(moduli) != len(key_ids):
        raise ValueError("moduli and key_ids length mismatch")

    hits: list[SharedFactorHit] = []
    pairs = 0
    n = len(moduli)
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
            a, b = moduli[i], moduli[j]
            if a <= 1 or b <= 1:
                continue
            g = gcd(a, b)
            if 1 < g < a and g < b:
                hits.append(
                    SharedFactorHit(
                        i=i,
                        j=j,
                        factor=g,
                        key_id_a=key_ids[i],
                        key_id_b=key_ids[j],
                    )
                )

    if not hits:
        msg = (
            f"Batch GCD: checked {pairs} pairs across {n} moduli — no shared prime factors. "
            "Absence of shared factors is not a security proof for any single key."
        )
    else:
        msg = (
            f"Batch GCD: {len(hits)} shared-factor collision(s) among {n} moduli "
            f"({pairs} pairs). Shared primes imply immediate factorization of both keys."
        )
    return BatchGcdResult(moduli_count=n, pairs_checked=pairs, hits=hits, message=msg)
