"""Deterministic RSA parameter analysis + heuristic warnings (separate from ECM evidence)."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd

from app.core.enums import FindingCategory


@dataclass
class Finding:
    category: FindingCategory
    code: str
    severity: str
    title: str
    detail: str


@dataclass
class AnalysisResult:
    deterministic: list[Finding] = field(default_factory=list)
    heuristics: list[Finding] = field(default_factory=list)
    valid: bool = True
    suspicious: bool = False

    @property
    def all_findings(self) -> list[Finding]:
        return self.deterministic + self.heuristics


def analyze_rsa(n: int, e: int) -> AnalysisResult:
    result = AnalysisResult()

    # --- Deterministic ---
    if n <= 1 or e <= 1:
        result.valid = False
        result.deterministic.append(
            Finding(
                FindingCategory.DETERMINISTIC,
                "INVALID_PARAMS",
                "critical",
                "Invalid RSA parameters",
                "n and e must both be integers greater than 1.",
            )
        )
        return result

    bits = n.bit_length()
    result.deterministic.append(
        Finding(
            FindingCategory.DETERMINISTIC,
            "BIT_LENGTH",
            "info",
            f"Modulus bit length: {bits}",
            f"Computed bit length of n is {bits} bits.",
        )
    )

    if n % 2 == 0:
        result.valid = False
        result.deterministic.append(
            Finding(
                FindingCategory.DETERMINISTIC,
                "EVEN_MODULUS",
                "critical",
                "Even modulus",
                "RSA modulus n must be odd.",
            )
        )
        return result

    if e % 2 == 0:
        result.deterministic.append(
            Finding(
                FindingCategory.DETERMINISTIC,
                "EVEN_EXPONENT",
                "warning",
                "Even public exponent",
                "Public exponent e is even, which is unusual for RSA.",
            )
        )

    if e < 3:
        result.valid = False
        result.deterministic.append(
            Finding(
                FindingCategory.DETERMINISTIC,
                "EXPONENT_TOO_SMALL",
                "critical",
                "Public exponent too small",
                f"e={e} is not a valid RSA public exponent for this auditor.",
            )
        )
        return result

    common_e = {3, 17, 65537}
    if e in common_e:
        result.deterministic.append(
            Finding(
                FindingCategory.DETERMINISTIC,
                "COMMON_EXPONENT",
                "info",
                f"Common public exponent e={e}",
                "Exponent matches a widely used RSA public exponent.",
            )
        )
    elif e.bit_length() > 64:
        result.heuristics.append(
            Finding(
                FindingCategory.HEURISTIC,
                "LARGE_EXPONENT",
                "warning",
                "Unusually large public exponent",
                "Large e values are uncommon and may indicate atypical key generation.",
            )
        )
        result.suspicious = True

    # Trial division for tiny factors (deterministic discovery of trivial weakness)
    tiny_primes = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107]
    for p in tiny_primes:
        if n % p == 0 and 1 < p < n:
            result.suspicious = True
            result.deterministic.append(
                Finding(
                    FindingCategory.DETERMINISTIC,
                    "TINY_FACTOR",
                    "critical",
                    f"Trivial factor discovered: {p}",
                    "Trial division found a tiny prime factor. The modulus is mathematically weak.",
                )
            )
            break

    # Heuristic: very small bit length
    if bits < 512:
        result.heuristics.append(
            Finding(
                FindingCategory.HEURISTIC,
                "SMALL_MODULUS",
                "warning",
                f"Small modulus ({bits} bits)",
                "Moduli under 512 bits are generally considered inadequate for modern use. "
                "This is a heuristic warning, not a factorization proof.",
            )
        )
        result.suspicious = True
    elif bits < 1024:
        result.heuristics.append(
            Finding(
                FindingCategory.HEURISTIC,
                "LEGACY_SIZE",
                "warning",
                f"Legacy-sized modulus ({bits} bits)",
                "1024-bit and smaller RSA keys are widely considered legacy. "
                "Absence of a factor does not prove security.",
            )
        )
        result.suspicious = True
    elif bits < 2048:
        result.heuristics.append(
            Finding(
                FindingCategory.HEURISTIC,
                "BELOW_CURRENT_BASELINE",
                "info",
                f"Below common 2048-bit baseline ({bits} bits)",
                "Many policies prefer ≥2048-bit RSA. This is policy guidance, not a break.",
            )
        )

    # gcd(e, n) should be 1
    g = gcd(e, n)
    if g != 1:
        result.suspicious = True
        result.deterministic.append(
            Finding(
                FindingCategory.DETERMINISTIC,
                "GCD_E_N",
                "critical",
                "gcd(e, n) ≠ 1",
                f"gcd(e, n) = {g}. This indicates a structural defect.",
            )
        )

    return result
