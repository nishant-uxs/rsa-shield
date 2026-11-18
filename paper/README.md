# RSA-SHIELD Research Paper (IEEE)

Focused IEEE conference draft for **RSA-SHIELD**: evidence-tiered RSA public-key auditing with budgeted multi-probe factorization and subquadratic inventory Batch-GCD.

## Title
> **RSA-SHIELD: An Evidence-Tiered Auditing Framework for RSA Public Keys with Subquadratic Batch-GCD and Budgeted Multi-Probe Factorization**

### Authors (unmask for camera-ready)
- Nishant Agarwal, Adarsh Agrahari, Shubh Jadiya
- Mentor: Dr. Sachin Choudhary — Bennett University

Double-blind builds keep authors anonymous in `rsa_shield_ieee.tex`.

## Deliverables

| File | Role |
|------|------|
| [`rsa_shield_ieee.tex`](./rsa_shield_ieee.tex) | IEEE conference source (honest claims + measured tables) |
| [`rsa_shield_ieee.pdf`](./rsa_shield_ieee.pdf) | Compiled PDF |
| [`references.bib`](./references.bib) | BibTeX |
| [`data/`](./data/) | Measured JSON dumps (suite, ablation, comparison, corpus, batch-GCD) |
| [`figures/`](./figures/) | Pipeline + result figures (PDF/PNG) |
| [`scripts/dump_eval_data.py`](./scripts/dump_eval_data.py) | Regenerate JSON from backend eval services |
| [`scripts/generate_figures.py`](./scripts/generate_figures.py) | Regenerate figures from JSON |

ACM twin files may lag; treat IEEE as the source of truth for this revision.

## Honest contributions (paper-safe)

1. Never-Claim-SECURE evidence taxonomy  
2. Budgeted multi-probe pipeline (analyze → Fermat → Wiener → ROCA fingerprint → ECM)  
3. Bernstein product/remainder-tree Batch-GCD with pairwise baseline  
4. Reproducible evaluation artifact (fixtures, ablation, config P/R, mini corpus)

**Not claimed as shipped features:** automated PQC CBOM, Mosca scoring product, hybrid TLS CSR generation, distributed Spark/Ray Batch-GCD, Internet-scale measurement.

## Measured headline results (local dump)

- Fixture suite: **7/7** hint matches; **0** SECURE labels  
- Full configuration: precision **1.0**, recall **1.0**, FP **0**  
- Epistemic bake-off: RSA-SHIELD recall **1.0** / overconfidence **0.0**; badkeys recall **0.75** / overconfidence **0.75**  
- Batch-GCD at $N=1000$: tree **645.79 ms** vs naive **1246.17 ms** (**1.93×**)  
- Mini corpus ($n=40$): **4** single-key factor finds; **1** shared-factor batch-GCD hit; SECURE labels **0**  
- CT tip sample: **12010** unique moduli; chunked batch-GCD hits **0**  
- ROCA calibration ($n=500$): FP **75% → 0.2%**; agreement **99.8%** (thr=`0.99`)  
- Adaptive scheduler: **1473.92 → 975.75 ms** (**1.511×**); recall **1.0**  
- Dump timestamp (core suite): **2026-11-13**; Bench **v1.0**; PDF target: **~6 pages**

## Verify every number + citation

```powershell
.\backend\.venv\Scripts\python.exe paper\scripts\personal_verify_paper.py
.\scripts\verify_paper.ps1
```

Expect `FAIL=0`.
## Regenerate results + figures

```powershell
cd "<repo>"
.\backend\.venv\Scripts\python.exe paper\scripts\dump_eval_data.py
.\backend\.venv\Scripts\python.exe paper\scripts\generate_figures.py
```

## Compile IEEE PDF

```bash
cd paper
pdflatex rsa_shield_ieee.tex
bibtex rsa_shield_ieee
pdflatex rsa_shield_ieee.tex
pdflatex rsa_shield_ieee.tex
```

Overleaf: upload `rsa_shield_ieee.tex`, `references.bib`, and the `figures/` directory; compiler pdfLaTeX.
