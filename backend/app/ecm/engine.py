"""
Lenstra ECM (Weierstrass form) — reliable educational factorization probe.

When elliptic-curve group law fails because a denominator shares a factor with n,
gcd recovers that factor. Budgeted by curves + timeout. Failure ≠ security proof.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from math import gcd


@dataclass
class EcmResult:
    factor_found: bool
    factor: int | None
    cofactor: int | None
    curves_tried: int
    elapsed_ms: float
    timed_out: bool
    message: str


def _is_probable_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31):
        if n == p:
            return True
        if n % p == 0:
            return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 23):
        if a >= n:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        cont = False
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                cont = True
                break
        if cont:
            continue
        return False
    return True


def _primes_upto(limit: int) -> list[int]:
    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    r = int(limit**0.5)
    for i in range(2, r + 1):
        if sieve[i]:
            sieve[i * i : limit + 1 : i] = b"\x00" * (((limit - i * i) // i) + 1)
    return [i for i, v in enumerate(sieve) if v]


class _Point:
    __slots__ = ("x", "y", "inf")

    def __init__(self, x: int | None = None, y: int | None = None, inf: bool = False):
        self.x = x
        self.y = y
        self.inf = inf


def _add_points(p: _Point, q: _Point, a: int, n: int) -> tuple[_Point | None, int | None]:
    """Return (point, None) or (None, factor) if non-invertible denominator found."""
    if p.inf:
        return q, None
    if q.inf:
        return p, None
    assert p.x is not None and p.y is not None and q.x is not None and q.y is not None
    if p.x == q.x and (p.y + q.y) % n == 0:
        return _Point(inf=True), None
    try:
        if p.x == q.x and p.y == q.y:
            denom = (2 * p.y) % n
            g = gcd(denom, n)
            if 1 < g < n:
                return None, g
            inv = pow(denom, -1, n)
            lam = ((3 * p.x * p.x + a) * inv) % n
        else:
            denom = (q.x - p.x) % n
            g = gcd(denom, n)
            if 1 < g < n:
                return None, g
            inv = pow(denom, -1, n)
            lam = ((q.y - p.y) * inv) % n
    except ValueError:
        g = gcd(denom, n)
        return (None, g) if 1 < g < n else (_Point(inf=True), None)

    xr = (lam * lam - p.x - q.x) % n
    yr = (lam * (p.x - xr) - p.y) % n
    return _Point(xr, yr), None


def _mul_point(k: int, p: _Point, a: int, n: int) -> tuple[_Point | None, int | None]:
    result = _Point(inf=True)
    addend = p
    while k > 0:
        if k & 1:
            result, factor = _add_points(result, addend, a, n)
            if factor is not None:
                return None, factor
            if result is None:
                return None, None
        addend, factor = _add_points(addend, addend, a, n)
        if factor is not None:
            return None, factor
        if addend is None:
            return None, None
        k >>= 1
    return result, None


def _ecm_curve(n: int, B1: int, rng: random.Random, deadline: float) -> int | None:
    # Random curve y^2 = x^3 + a x + b  with random point
    for _ in range(8):
        if time.perf_counter() > deadline:
            return None
        x = rng.randrange(1, n)
        y = rng.randrange(1, n)
        a = rng.randrange(0, n)
        b = (y * y - x * x * x - a * x) % n
        # Discriminant non-zero mod factors ideally; ignore and proceed
        p = _Point(x, y)
        # Multiply by product of prime powers ≤ B1
        for prime in _primes_upto(B1):
            if time.perf_counter() > deadline:
                return None
            pp = prime
            while pp * prime <= B1:
                pp *= prime
            p2, factor = _mul_point(pp, p, a, n)
            if factor is not None:
                return factor
            if p2 is None:
                return None
            p = p2
        return None
    return None


def ecm_factor(
    n: int,
    *,
    timeout_ms: int = 8000,
    curves: int = 40,
    B1: int = 50_000,
    seed: int | None = None,
) -> EcmResult:
    start = time.perf_counter()
    deadline = start + timeout_ms / 1000.0
    rng = random.Random(seed if seed is not None else (time.time_ns() & 0xFFFFFFFF))

    if n < 2:
        return EcmResult(False, None, None, 0, 0.0, False, "n must be ≥ 2")
    if _is_probable_prime(n):
        return EcmResult(
            False, None, None, 0, (time.perf_counter() - start) * 1000, False, "n appears prime; ECM not applicable"
        )

    for p in _primes_upto(1_000_000):
        if time.perf_counter() > deadline:
            break
        if n % p == 0 and 1 < p < n:
            return EcmResult(
                True, p, n // p, 0, (time.perf_counter() - start) * 1000, False, f"Factor found by trial division: {p}"
            )

    B1 = max(50, min(int(B1), 20_000))
    curves = max(1, min(int(curves), 120))
    tried = 0
    timed_out = False

    for i in range(curves):
        if time.perf_counter() > deadline:
            timed_out = True
            break
        tried += 1
        b1_try = min(B1, 200 + i * 150)
        factor = _ecm_curve(n, b1_try, rng, deadline)
        if factor is not None and 1 < factor < n:
            return EcmResult(
                True,
                factor,
                n // factor,
                tried,
                (time.perf_counter() - start) * 1000,
                False,
                "Non-trivial factor discovered via Lenstra ECM.",
            )

    elapsed = (time.perf_counter() - start) * 1000
    msg = (
        "Factorization attempt reached the configured computational budget. This result is inconclusive."
        if timed_out or elapsed >= timeout_ms * 0.95
        else "No factor discovered within configured curve budget. This result is inconclusive."
    )
    return EcmResult(False, None, None, tried, elapsed, timed_out or elapsed >= timeout_ms * 0.95, msg)
