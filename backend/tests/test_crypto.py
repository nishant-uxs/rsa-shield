import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crypto.analyzer import analyze_rsa
from app.crypto.parser import ParseError, parse_modulus_exponent, parse_pem
from app.ecm.engine import ecm_factor
from app.services.fixtures import N_TINY, N_WEAK


def test_parse_raw_ok():
    p = parse_modulus_exponent(str(N_TINY), 65537)
    assert p.n == N_TINY
    assert p.e == 65537


def test_reject_private_pem():
    pem = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF6PZGFleJKY3
-----END RSA PRIVATE KEY-----"""
    try:
        parse_pem(pem)
        assert False, "should reject"
    except ParseError as e:
        assert "Private" in e.message or "private" in e.message.lower()


def test_tiny_factor_analysis():
    r = analyze_rsa(N_TINY, 65537)
    assert any(f.code == "TINY_FACTOR" for f in r.deterministic)


def test_ecm_finds_weak_factor():
    result = ecm_factor(N_WEAK, timeout_ms=15000, curves=60, B1=10000)
    assert result.factor_found is True
    assert result.factor is not None
    assert N_WEAK % result.factor == 0
