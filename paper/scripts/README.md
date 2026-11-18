# Paper evaluation scripts

Regenerate dumps, figures, and verify every number cited in `rsa_shield_ieee.tex`.

| Script | Purpose |
|--------|---------|
| `dump_eval_data.py` | Fixture suite / ablation / comparison / corpus / batch-GCD JSON |
| `run_tool_bakeoff.py` | Epistemic bake-off vs badkeys |
| `ct_measurement.py` | Multi-log public CT tip sample |
| `run_roca_parity.py` | Legacy vs calibrated ROCA vs badkeys |
| `run_roca_calibration.py` | Threshold sweep → `roca_calibration.json` |
| `run_adaptive_ablation.py` | Fixed vs adaptive scheduler |
| `generate_figures.py` | PDF/PNG figures from frozen JSON |
| `audit_paper_claims.py` | Structural claim audit |
| `personal_verify_paper.py` | End-to-end number + citation verify |
| `verify_numbers.py` | Quick dump echo |

## Verify before camera-ready

```powershell
..\backend\.venv\Scripts\python.exe paper\scripts\personal_verify_paper.py
..\backend\.venv\Scripts\python.exe paper\scripts\audit_paper_claims.py
```

Expect `FAIL=0` on both.
