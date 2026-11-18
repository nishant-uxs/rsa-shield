# RSA-SHIELD — Research Presentation (Team Aegis)

Numbers-focused deck for team / faculty demos.

## Open

1. **Overleaf / Beamer (best for sir):** upload `rsa_shield_beamer.tex` — see `OVERLEAF.md`
2. **Beamer PDF:** `presentation/rsa_shield_beamer.pdf` (after `pdflatex`)
3. **Browser deck:** open `presentation/index.html` (←/→ or Space)
4. **Live with app:** http://127.0.0.1:5173/deck/index.html
5. **PowerPoint:** `presentation/RSA_SHIELD_Research.pptx`

## Regenerate PPTX

```bash
backend\.venv\Scripts\python.exe presentation\build_pptx.py
```

## Team

- Team Aegis · Bennett University
- Mentor: Dr. Sachin Choudhary

## Headline numbers (locked)

| Result | Value |
|--------|--------|
| Bake-off overconfidence | 0.0 vs badkeys 0.75 |
| ROCA FP (legacy → calibrated) | 75% → 0.2% (n=500) |
| Adaptive speedup | 1.511× at recall 1.0 |
| CT tip moduli | 12,010 · GCD hits 0 |

## Sir demo

http://127.0.0.1:5173/app/demo

Explainer: `docs/EXPLAIN_FOR_TEAM_AND_SIR.md`
