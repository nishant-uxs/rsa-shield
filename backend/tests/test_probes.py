import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Crypto.Util.number import getPrime, isPrime

from app.crypto.batch_gcd import batch_gcd
from app.crypto.fermat import fermat_factor
from app.crypto.roca import roca_fingerprint
from app.crypto.wiener import generate_wiener_weak_key, wiener_attack


def test_fermat_close_primes():
    p = getPrime(64)
    q = p + 2
    while not isPrime(q):
        q += 2
    n = p * q
    r = fermat_factor(n, max_steps=100_000)
    assert r.factor_found
    assert r.factor is not None
    assert n % r.factor == 0


def test_wiener_small_d():
    n, e, d, p, q = generate_wiener_weak_key(256)
    r = wiener_attack(n, e)
    assert r.factor_found
    assert r.factor is not None
    assert n % r.factor == 0
    assert r.private_exponent is not None


def test_roca_runs_on_normal_modulus():
    n = getPrime(128) * getPrime(128)
    r = roca_fingerprint(n)
    assert isinstance(r.fingerprint_positive, bool)
    assert "ROCA" in r.message


def test_batch_gcd_shared_factor():
    p = getPrime(32)
    q1 = getPrime(32)
    q2 = getPrime(32)
    n1 = p * q1
    n2 = p * q2
    r = batch_gcd([n1, n2], ["a", "b"])
    assert len(r.hits) == 1
    assert r.hits[0].factor == p
