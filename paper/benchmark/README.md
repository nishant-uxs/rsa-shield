# RSA-Auditor Bench (v1.0)

Labeled, **synthetic** public-key fixtures for evaluating RSA public-key auditors.

## Purpose

Provide a citable, reproducible ground-truth set so tools can be compared on:

1. **Factor recovery** on planted weak classes
2. **Epistemic labeling** — whether a tool emits pass/secure-like outcomes when it did not recover a factor

This corpus is **not** an Internet measurement study and does **not** certify any key as secure.

## Contents

| Path | Role |
|------|------|
| `manifest.json` | Labels: class, expects_factor, expected_tier/method, bit length, `(N,e)` / PEM refs |
| `keys/*.pem` | Public PEMs for each fixture (invalid fixture intentionally malformed) |

## Classes

- `tiny_factor`, `smoothish_factor`, `fermat_close`, `wiener_small_d` — expect `FACTOR_FOUND`
- `normal_lab`, `legacy_size` — expect non-factor tiers (`SUSPICIOUS` / `INCONCLUSIVE`), never `SECURE`
- `invalid` — expect `INVALID_KEY`

## License / use

Educational and research evaluation only. Authorized public keys. Do not treat absence of findings as a security proof.

Regenerate PEMs from the backend fixtures module:

```powershell
..\backend\.venv\Scripts\python.exe paper\scripts\export_benchmark.py
```
