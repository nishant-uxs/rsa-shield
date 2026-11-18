"""Controlled educational fixtures. Never targets external systems.

All moduli below are frozen for reproducible RSA-Auditor Bench / paper dumps.
"""

from __future__ import annotations

from Crypto.PublicKey import RSA


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

# Frozen near-twin Fermat demo (|p−q|=54).
P_FERMAT = 9223372036854875869
Q_FERMAT = 9223372036854875923
N_FERMAT = P_FERMAT * Q_FERMAT

# Pollard's p-1 demo: 641 divides F5; 641-1=640 is B1-smooth.
N_POLLARD_P1 = 641 * 6700417

# Frozen 1024-bit public key (public material only).
N_LEGACY_1024 = int(
    "153592992512716466888850220916194539089158400241293992137444396041683584104727854498923400114256028781743713031180197017986077384629728093859647528152512950305645782249062182039585271862061005574173988834279589896197616896118213377030936141266811918831300936650508062613641459451304463298018714248038541695617"
)
LEGACY_1024_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDauUMyaQ7XSFsKCbATKELutgDt
NmfYzXQAB1PP+uB8xtBa8wMPcxuiZjxFjtoqhVEGOVuPpsvi7OlX59/Ck+unr68P
zclo2qsXFHNGUu3XnzJ8E+wRqicevsx9GV9GMgKlj2U/RNt+i8OR1WljVKHqtxE5
XFSSeM1niw4L5RQagQIDAQAB
-----END PUBLIC KEY-----
"""


def _pem_from_ne(n: int, e: int = E) -> str:
    return RSA.construct((n, e)).export_key("PEM").decode()


def build_fixtures() -> list[dict]:
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
            "expects_factor": True,
            "expected_method": "ECM",
            "expected_tier": "FACTOR_FOUND",
            "bench_class": "smoothish_factor",
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
            "expects_factor": True,
            "expected_method": "TINY_FACTOR",
            "expected_tier": "FACTOR_FOUND",
            "bench_class": "tiny_factor",
        },
        {
            "id": "fermat-close",
            "name": "Fermat near-twin primes demo",
            "description": "Modulus with intentionally close primes (|p−q| tiny) so Fermat factorization recovers factors.",
            "category": "weak",
            "pem": _pem_from_ne(N_FERMAT),
            "n": str(N_FERMAT),
            "e": E,
            "expected_hint": "FACTOR_FOUND (FERMAT)",
            "expects_factor": True,
            "expected_method": "FERMAT",
            "expected_tier": "FACTOR_FOUND",
            "bench_class": "fermat_close",
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
            "expects_factor": True,
            "expected_method": "WIENER",
            "expected_tier": "FACTOR_FOUND",
            "bench_class": "wiener_small_d",
        },
        {
            "id": "pollard-p1",
            "name": "Pollard p-1 smooth-order demo",
            "description": "Modulus with a factor p where p-1 is B1-smooth so budgeted Pollard p-1 recovers p.",
            "category": "weak",
            "pem": _pem_from_ne(N_POLLARD_P1),
            "n": str(N_POLLARD_P1),
            "e": E,
            "expected_hint": "FACTOR_FOUND (POLLARD_P1)",
            "expects_factor": True,
            "expected_method": "POLLARD_P1",
            "expected_tier": "FACTOR_FOUND",
            "bench_class": "pollard_p1_smooth",
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
            "expects_factor": False,
            "expected_method": None,
            "expected_tier": "SUSPICIOUS",
            "bench_class": "normal_lab",
        },
        {
            "id": "legacy-1024",
            "name": "Legacy-size RSA-1024 public key",
            "description": "Frozen 1024-bit RSA public key. Likely heuristic legacy-size warning; ECM usually inconclusive.",
            "category": "normal",
            "pem": LEGACY_1024_PEM,
            "n": str(N_LEGACY_1024),
            "e": E,
            "expected_hint": "SUSPICIOUS or INCONCLUSIVE",
            "expects_factor": False,
            "expected_method": None,
            "expected_tier": "SUSPICIOUS",
            "bench_class": "legacy_size",
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
            "expects_factor": False,
            "expected_method": None,
            "expected_tier": "INVALID_KEY",
            "bench_class": "invalid",
        },
    ]


FIXTURES = build_fixtures()


def get_fixture(fixture_id: str) -> dict | None:
    for f in FIXTURES:
        if f["id"] == fixture_id:
            return f
    return None
