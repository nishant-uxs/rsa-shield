"""Budgeted Pollard's p-1 factorization probe (public modulus only).

Recovers a factor when some prime divisor p of n has p-1 smooth up to B1.
Timeout / bound exhaustion => no factor claim (never a security proof).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from math import gcd, log


@dataclass
class PollardP1Result:
    factor_found: bool
    factor: int | None
    cofactor: int | None
    B1: int
    elapsed_ms: float
    timed_out: bool
    message: str


def _primes_upto(limit: int) -> list[int]:
    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    r = int(limit**0.5)
    for i in range(2, r + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start : limit + 1 : step] = b"\x00" * (((limit - start) // step) + 1)
    return [i for i, v in enumerate(sieve) if v]


def pollard_p1(
    n: int,
    *,
    B1: int = 50_000,
    timeout_ms: int = 1500,
    base: int = 2,
) -> PollardP1Result:
    """Stage-1 Pollard's p−1 with wall-clock budget."""
    t0 = time.perf_counter()

    def elapsed() -> float:
        return (time.perf_counter() - t0) * 1000

    def timed_out() -> bool:
        return elapsed() >= timeout_ms

    if n <= 1 or n % 2 == 0:
        return PollardP1Result(
            False,
            2 if n % 2 == 0 and n > 2 else None,
            (n // 2) if n % 2 == 0 and n > 2 else None,
            B1,
            round(elapsed(), 2),
            False,
            "Pollard p-1: even modulus rejected/handled before algebraic stage."
            if n % 2 == 0
            else "Pollard p-1: invalid modulus.",
        )

    # Quick gcd with small primes first
    for p in _primes_upto(min(1000, B1)):
        if timed_out():
            return PollardP1Result(
                False, None, None, B1, round(elapsed(), 2), True,
                f"Pollard p-1 timed out during trial sieve (B1={B1}). Not a security proof.",
            )
        if n % p == 0 and 1 < p < n:
            return PollardP1Result(
                True, p, n // p, B1, round(elapsed(), 2), False,
                f"Pollard p-1: factor found by small-prime sieve: {p}",
            )

    primes = _primes_upto(B1)
    a = base % n
    if a < 2:
        a = 2

    for p in primes:
        if timed_out():
            return PollardP1Result(
                False, None, None, B1, round(elapsed(), 2), True,
                f"Pollard p-1 timed out under B1={B1} after {round(elapsed(), 2)} ms. Not a security proof.",
            )
        # Raise a to the highest power p^e <= B1
        e = int(log(B1) / log(p)) if p > 1 else 0
        if e < 1:
            continue
        pe = p**e
        a = pow(a, pe, n)

    g = gcd(a - 1, n)
    ms = round(elapsed(), 2)
    if 1 < g < n:
        return PollardP1Result(
            True, g, n // g, B1, ms, False,
            f"Pollard p-1: factor found with B1={B1} (p-1 smooth stage).",
        )
    if g == n:
        # Unlucky base; one retry with alternate base under remaining budget
        if timed_out():
            return PollardP1Result(
                False, None, None, B1, ms, True,
                f"Pollard p-1 timed out (g=n) under B1={B1}. Not a security proof.",
            )
        a2 = 3
        for p in primes:
            if timed_out():
                break
            e = int(log(B1) / log(p)) if p > 1 else 0
            if e < 1:
                continue
            a2 = pow(a2, p**e, n)
        g2 = gcd(a2 - 1, n)
        ms = round(elapsed(), 2)
        if 1 < g2 < n:
            return PollardP1Result(
                True, g2, n // g2, B1, ms, False,
                f"Pollard p-1: factor found with alternate base, B1={B1}.",
            )

    return PollardP1Result(
        False, None, None, B1, ms, timed_out(),
        f"Pollard p-1: no factor within B1={B1} ({ms} ms). Not a security proof.",
    )
