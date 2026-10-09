"""Wiener's attack (continued fractions) for small private exponents d.

If d < (1/3) N^(1/4), continued-fraction convergents of e/N can recover d
(and then factors). Educational / audit probe only.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd, isqrt


@dataclass
class WienerResult:
    factor_found: bool
    factor: int | None
    cofactor: int | None
    private_exponent: int | None
    convergents_tried: int
    message: str


def _continued_fraction(num: int, den: int) -> list[int]:
    cf: list[int] = []
    while den:
        q = num // den
        cf.append(q)
        num, den = den, num - q * den
    return cf


def _convergents(cf: list[int]) -> list[tuple[int, int]]:
    conv: list[tuple[int, int]] = []
    for i in range(len(cf)):
        if i == 0:
            conv.append((cf[0], 1))
        elif i == 1:
            conv.append((cf[0] * cf[1] + 1, cf[1]))
        else:
            h1, k1 = conv[i - 1]
            h2, k2 = conv[i - 2]
            conv.append((cf[i] * h1 + h2, cf[i] * k1 + k2))
    return conv


def wiener_attack(n: int, e: int, max_convergents: int = 10_000) -> WienerResult:
    if n < 15 or e < 3:
        return WienerResult(False, None, None, None, 0, "Wiener skipped: invalid parameters")

    cf = _continued_fraction(e, n)
    conv = _convergents(cf)[:max_convergents]

    for idx, (k, d) in enumerate(conv, start=1):
        if k == 0:
            continue
        # phi(n) candidate: (e*d - 1) must be divisible by k
        if (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        # Solve x^2 - (n - phi + 1)x + n = 0
        s = n - phi + 1
        disc = s * s - 4 * n
        if disc < 0:
            continue
        root = isqrt(disc)
        if root * root != disc:
            continue
        if (s + root) % 2 != 0:
            continue
        p = (s + root) // 2
        q = (s - root) // 2
        if p > 1 and q > 1 and p * q == n:
            return WienerResult(
                True,
                min(p, q),
                max(p, q),
                d,
                idx,
                f"Wiener: recovered d≈{d.bit_length()}-bit private exponent; factors extracted.",
            )

    bound = isqrt(isqrt(n)) // 3  # rough N^1/4 / 3
    return WienerResult(
        False,
        None,
        None,
        None,
        len(conv),
        f"Wiener: no small-d recovery in {len(conv)} convergents "
        f"(attack targets d < ~N^(1/4)/3 ≈ {max(bound, 0)}).",
    )


def generate_wiener_weak_key(bits: int = 256) -> tuple[int, int, int, int, int]:
    """Return (n, e, d, p, q) with small d for lab fixtures."""
    from Crypto.Util.number import getPrime, inverse

    half = bits // 2
    while True:
        p = getPrime(half)
        q = getPrime(half)
        if p == q:
            continue
        n = p * q
        phi = (p - 1) * (q - 1)
        # Choose d small enough for Wiener
        limit = max(3, isqrt(isqrt(n)) // 3)
        d = getPrime(max(16, limit.bit_length() - 2))
        if d >= limit or gcd(d, phi) != 1:
            continue
        try:
            e = inverse(d, phi)
        except ValueError:
            continue
        if e > 1 and (e * d) % phi == 1:
            return n, e, d, p, q
