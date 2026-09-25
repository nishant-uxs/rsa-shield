"""Controlled educational fixtures. Never targets external systems."""

from __future__ import annotations

from Crypto.PublicKey import RSA

# Tiny factors — deterministic trial division finds these immediately.
N_TINY = 101 * 1031  # 104131
E = 65537

# Weak ECM demo: ~30-bit prime × ~35-bit prime (above tiny trial cutoff in analyzer, within ECM/trial-50k engine)
# 1000000007 is prime; 32416190071 is prime.
P_WEAK = 1000000007
Q_WEAK = 32416190071
N_WEAK = P_WEAK * Q_WEAK

# Balanced ~64-bit primes → short ECM budget typically INCONCLUSIVE (not a security proof).
P_NORMAL = 9223372036854775783
Q_NORMAL = 9223372036854775643
N_NORMAL = P_NORMAL * Q_NORMAL


def _pem_from_ne(n: int, e: int = E) -> str:
    return RSA.construct((n, e)).export_key("PEM").decode()


def build_fixtures() -> list[dict]:
    legacy_pem = RSA.generate(1024).publickey().export_key("PEM").decode()
    return [
        {
            "id": "weak-ecm",
            "name": "Intentionally weak RSA (ECM demo)",
            "description": "Composite with a ~30-bit factor so bounded factorization can succeed in the lab.",
            "category": "weak",
            "pem": _pem_from_ne(N_WEAK),
            "n": str(N_WEAK),
            "e": E,
            "expected_hint": "FACTOR_FOUND",
        },
        {
            "id": "small-factor",
            "name": "Small-factor demonstration key",
            "description": "Tiny factors discoverable by deterministic trial division.",
            "category": "weak",
            "pem": _pem_from_ne(N_TINY),
            "n": str(N_TINY),
            "e": E,
            "expected_hint": "FACTOR_FOUND",
        },
        {
            "id": "normal-demo",
            "name": "Normal demonstration RSA key",
            "description": "Balanced primes. Short ECM budget typically yields INCONCLUSIVE — not a security proof.",
            "category": "normal",
            "pem": _pem_from_ne(N_NORMAL),
            "n": str(N_NORMAL),
            "e": E,
            "expected_hint": "INCONCLUSIVE",
        },
        {
            "id": "legacy-1024",
            "name": "Legacy-size RSA-1024 public key",
            "description": "Fresh 1024-bit RSA public key. Likely heuristic legacy-size warning; ECM usually inconclusive.",
            "category": "normal",
            "pem": legacy_pem,
            "n": None,
            "e": E,
            "expected_hint": "SUSPICIOUS or INCONCLUSIVE",
        },
        {
            "id": "invalid-pem",
            "name": "Malformed PEM",
            "description": "Invalid PEM text to demonstrate graceful error handling.",
            "category": "invalid",
            "pem": "-----BEGIN PUBLIC KEY-----\nNOT_A_REAL_KEY\n-----END PUBLIC KEY-----",
            "n": None,
            "e": None,
            "expected_hint": "INVALID_KEY",
        },
    ]


FIXTURES = build_fixtures()


def get_fixture(fixture_id: str) -> dict | None:
    for f in FIXTURES:
        if f["id"] == fixture_id:
            return f
    return None
