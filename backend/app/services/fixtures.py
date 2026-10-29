"""Controlled educational fixtures. Never targets external systems."""

from __future__ import annotations

from Crypto.PublicKey import RSA
from Crypto.Util.number import getPrime, isPrime


# Tiny factors — deterministic trial division finds these immediately.
N_TINY = 101 * 1031  # 104131
E = 65537

# Weak ECM/demo factor: prime ~6 digits — found by engine trial (≤1e6) / ECM; above analyzer tiny list.
P_WEAK = 100003
Q_WEAK = 32416190071
N_WEAK = P_WEAK * Q_WEAK

# Distant ~64-bit primes. Gap is large enough that a 25k-step Fermat probe does not factor them.
P_NORMAL = 14207201142986081273
Q_NORMAL = 11399710733968215583
N_NORMAL = P_NORMAL * Q_NORMAL

# Fixed Wiener demo (small d). Exponent does not fit in a 64-bit int column.
N_WIENER = 2481545804494113232096604789576025074500577845743602173217
E_WIENER = 165107158544877572609780949974738783268249968586186155449


def _pem_from_ne(n: int, e: int = E) -> str:
    return RSA.construct((n, e)).export_key("PEM").decode()


def _fermat_close_modulus(bits: int = 128) -> tuple[int, int, int]:
    """Two close primes so Fermat succeeds quickly."""
    half = bits // 2
    p = getPrime(half)
    q = p + 2
    while not isPrime(q):
        q += 2
    return p * q, p, q


def build_fixtures() -> list[dict]:
    legacy_pem = RSA.generate(1024).publickey().export_key("PEM").decode()
    n_fermat, _, _ = _fermat_close_modulus(128)
    n_w, e_w = N_WIENER, E_WIENER

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
            "id": "fermat-close",
            "name": "Fermat near-twin primes demo",
            "description": "Modulus with intentionally close primes (|p−q| tiny) so Fermat factorization recovers factors.",
            "category": "weak",
            "pem": _pem_from_ne(n_fermat),
            "n": str(n_fermat),
            "e": E,
            "expected_hint": "FACTOR_FOUND (FERMAT)",
        },
        {
            "id": "wiener-small-d",
            "name": "Wiener small private exponent demo",
            "description": "Public key with intentionally small d so continued-fraction Wiener attack recovers factors.",
            "category": "weak",
            "pem": _pem_from_ne(n_w, e_w),
            "n": str(n_w),
            "e": e_w,
            "expected_hint": "FACTOR_FOUND (WIENER)",
        },
        {
            "id": "normal-demo",
            "name": "Normal demonstration RSA key",
            "description": "Balanced primes under 512 bits. Size heuristic marks SUSPICIOUS; a short ECM budget does not factor it and is not a security proof.",
            "category": "normal",
            "pem": _pem_from_ne(N_NORMAL),
            "n": str(N_NORMAL),
            "e": E,
            "expected_hint": "SUSPICIOUS or INCONCLUSIVE",
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
