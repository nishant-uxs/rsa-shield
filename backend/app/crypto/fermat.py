"""Fermat factorization probe for near-twin primes (close p, q).

If |p − q| is small, Fermat recovers factors quickly. Success is deterministic
evidence of weakness — not a claim about random well-spaced RSA primes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class FermatResult:
    factor_found: bool
    factor: int | None
    cofactor: int | None
    steps: int
    message: str


def fermat_factor(n: int, max_steps: int = 50_000) -> FermatResult:
    """Attempt Fermat factorization for up to max_steps increments of a."""
    if n < 4 or n % 2 == 0:
        return FermatResult(False, None, None, 0, "Fermat skipped: invalid or even modulus")

    a = math.isqrt(n) + 1
    if a * a == n:
        return FermatResult(True, a, a, 0, f"Fermat: perfect square root a={a}")

    for steps in range(1, max_steps + 1):
        b2 = a * a - n
        b = math.isqrt(b2)
        if b * b == b2:
            p = a - b
            q = a + b
            if p > 1 and q > 1 and p * q == n:
                return FermatResult(
                    True,
                    p,
                    q,
                    steps,
                    f"Fermat factor found in {steps} steps (|p−q| small).",
                )
        a += 1

    return FermatResult(
        False,
        None,
        None,
        max_steps,
        f"Fermat: no factor within {max_steps} steps (primes not near-twins under bound).",
    )
