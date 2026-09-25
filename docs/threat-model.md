# Threat model (summary)

## Assets

- Audit history and findings
- Public moduli / fingerprints (not private keys)
- Reports

## Threat actors

- Curious students / outsiders
- Malicious uploaders of private keys or huge payloads
- Operators mistaking inconclusive for “secure”

## Attack surface

- File/PEM upload endpoints
- ECM CPU exhaustion
- Misinterpretation of results

## Mitigations

- Reject private keys
- Size limits + ECM timeouts
- Explicit result vocabulary (no SECURE)
- Lab fixtures only for demos

## Limitations

- Local prototype auth is minimal (demo user seed)
- ECM is educational/budgeted
- Operators must only audit authorized keys
