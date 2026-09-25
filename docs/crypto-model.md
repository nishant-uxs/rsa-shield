# Crypto model

## Inputs

- RSA public PEM
- Raw modulus `n` + exponent `e`
- DER (API-ready via parser helpers)

Private keys are rejected and never stored.

## Deterministic checks

- Parameter validity
- Bit length
- Tiny trial factors
- gcd(e, n)

## Heuristics

- Legacy/small modulus sizes
- Unusual exponents

## ECM

Lenstra ECM stage-style Weierstrass probing with timeouts and curve budgets.

- Factor found ⇒ `FACTOR_FOUND` (evidence)
- Timeout / no factor ⇒ `INCONCLUSIVE` (not secure)
