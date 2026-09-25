"""RSA public-key parsing. Rejects private keys. Never crashes on malformed input."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long


class ParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class ParsedRsaPublicKey:
    n: int
    e: int
    bit_length: int
    fingerprint: str
    source_format: str


_PRIVATE_MARKERS = (
    "BEGIN RSA PRIVATE KEY",
    "BEGIN PRIVATE KEY",
    "BEGIN ENCRYPTED PRIVATE KEY",
)


def _fingerprint(n: int, e: int) -> str:
    raw = f"{n:x}:{e}".encode()
    return hashlib.sha256(raw).hexdigest()


def parse_pem(pem_text: str) -> ParsedRsaPublicKey:
    text = (pem_text or "").strip()
    if not text:
        raise ParseError("Empty PEM input.")
    upper = text.upper()
    for marker in _PRIVATE_MARKERS:
        if marker in upper:
            raise ParseError(
                "Private key material detected. RSA-SHIELD only accepts public keys/moduli "
                "and will not persist private keys."
            )
    try:
        key = RSA.import_key(text)
    except (ValueError, IndexError, TypeError) as exc:
        raise ParseError(
            "Unable to parse RSA public key. Verify that the supplied PEM is valid."
        ) from exc
    if key.has_private():
        raise ParseError(
            "Parsed key contains private components. Upload a public key only."
        )
    n = int(key.n)
    e = int(key.e)
    if n <= 1 or e <= 1:
        raise ParseError("Invalid RSA parameters: n and e must be integers > 1.")
    return ParsedRsaPublicKey(
        n=n,
        e=e,
        bit_length=n.bit_length(),
        fingerprint=_fingerprint(n, e),
        source_format="PEM",
    )


def parse_modulus_exponent(n_str: str, e: int) -> ParsedRsaPublicKey:
    raw = (n_str or "").strip().replace(" ", "").replace("\n", "")
    if not raw:
        raise ParseError("Modulus n is required.")
    try:
        if raw.lower().startswith("0x"):
            n = int(raw, 16)
        elif re.fullmatch(r"[0-9]+", raw):
            n = int(raw, 10)
        elif re.fullmatch(r"[0-9a-fA-F]+", raw):
            n = int(raw, 16)
        else:
            raise ValueError("unrecognized")
    except ValueError as exc:
        raise ParseError("Modulus must be a decimal or hexadecimal integer.") from exc
    if e is None or int(e) <= 1:
        raise ParseError("Public exponent e must be an integer > 1.")
    e = int(e)
    if n <= 1:
        raise ParseError("Modulus n must be > 1.")
    if n % 2 == 0:
        raise ParseError("Modulus n appears even; RSA moduli must be odd composites of primes.")
    return ParsedRsaPublicKey(
        n=n,
        e=e,
        bit_length=n.bit_length(),
        fingerprint=_fingerprint(n, e),
        source_format="RAW",
    )


def parse_der_bytes(data: bytes) -> ParsedRsaPublicKey:
    if not data:
        raise ParseError("Empty DER input.")
    if len(data) > 64 * 1024:
        raise ParseError("DER payload exceeds size limit.")
    try:
        key = RSA.import_key(data)
    except (ValueError, IndexError, TypeError) as exc:
        raise ParseError("Unable to parse DER-encoded RSA public key.") from exc
    if key.has_private():
        raise ParseError("DER payload contains private key material.")
    n = int(key.n)
    e = int(key.e)
    return ParsedRsaPublicKey(
        n=n,
        e=e,
        bit_length=n.bit_length(),
        fingerprint=_fingerprint(n, e),
        source_format="DER",
    )


def n_to_hex(n: int) -> str:
    return format(n, "x")


def hex_to_int(h: str) -> int:
    return int(h, 16)
