# RSA-SHIELD — humne exactly kya kiya? (Team + Sir explainer)

**Team Aegis · Bennett University · Mentor: Dr. Sachin Choudhary**

Ye note tumhe, team ko, aur sir ko 5–7 minute mein samjhane ke liye hai. Numbers paper ke frozen dumps se hain — invent nahi kiye.

---

## 1) Project ek line mein

**RSA-SHIELD** ek *defensive* RSA public-key auditor hai jo public keys / moduli check karta hai, budgeted classical probes chalata hai, aur **kabhi absolute `SECURE` label nahi deta**.

Kyunki: “factor nahi mila” ≠ “key mathematically secure hai”.

---

## 2) Naya attack invent nahi kiya

Humne RSA / ECM / Wiener / Fermat / ROCA *invent* nahi kiye. Contribution **systems + evaluation** hai:

| Piece | Matlab |
|--------|--------|
| Evidence tiers | `FACTOR_FOUND` / `SUSPICIOUS` / `INCONCLUSIVE` / `NO_WEAKNESS…` / `INVALID` — never `SECURE` |
| RSA-Auditor Bench | Labeled weak fixtures for regression + paper tables |
| Epistemic bake-off | Tools compare: factor recovery **and** overconfidence (empty = OK-like) |
| Public CT tip sample | Multi-log Certificate Transparency tip (~12k moduli) |
| ROCA calibration | Educational fingerprint thresholds tuned vs `badkeys` |
| Adaptive scheduler | Bit-length / `e`-aware budgets → faster, same recall |

---

## 3) Headline measured numbers (yaad rakhna)

1. **Bake-off overconfidence:** RSA-SHIELD **0.0** vs `badkeys` **0.75** (Bench).
2. **ROCA calibration (CT tip n=500 vs badkeys):** legacy FP **75% → calibrated 0.2%**; agreement **25% → 99.8%**.
3. **Adaptive scheduler:** mean wall **1473.92 ms → 975.75 ms** = **1.511×** faster; factor recall still **1.0**.
4. **CT multi-log tip:** **12,010** unique moduli; chunked batch-GCD **0** shared-factor hits in **81172.63 ms**.
5. **Never-SECURE:** CT probe sample (800 keys) emitted **0** `SECURE` labels.

---

## 4) Sir ko demo kaise dikhana hai (~3 min)

Live app: `http://127.0.0.1:5173` → **Sir Demo** (`/app/demo`)

Order:

1. **Weak ECM** → expect `FACTOR_FOUND`
2. **Fermat-close** → expect `FACTOR_FOUND`
3. **Wiener small-d** → expect `FACTOR_FOUND`
4. **Normal demo** → expect *not* `SECURE` (INCONCLUSIVE / NO_WEAKNESS…)

Phir bolna: “Weak keys pe evidence milta hai; strong-looking key pe bhi hum SECURE nahi likhte.”

Extra:

- **Evaluation** page → research tables (fixtures / ablation / compare)
- **Related Work** → honest positioning (packaging + evidence, not new math)

---

## 5) Paper kahan hai

- TeX: `paper/rsa_shield_ieee.tex`
- PDF: `paper/rsa_shield_ieee.pdf`
- Frozen data: `paper/data/*.json`
- Figures: `paper/figures/`
- Claims audit: `python paper/scripts/audit_paper_claims.py`

---

## 6) PPT / deck

- Browser deck: `presentation/index.html` (arrows / Space)
- Also served at: `http://127.0.0.1:5173/deck/index.html` jab frontend chal raha ho
- PowerPoint: `presentation/RSA_SHIELD_Research.pptx` (agar generate ho chuka ho)

Focus slides: problem → never-SECURE → bake-off numbers → ROCA calibration → CT → adaptive → demo → limitations.

---

## 7) Common sir questions — short answers

**Q: Naya cryptanalysis algorithm?**  
A: Nahi. Classical probes ko orchestrate + evidence-correct labels + reproducible bench.

**Q: Internet pe kitne weak keys?**  
A: Full census nahi. Multi-log **tip sample** 12,010 moduli; 0 GCD hits in that sample.

**Q: ROCA 75% matlab Infineon compromise?**  
A: Nahi — legacy educational fingerprint over-trigger. Calibrated profile FP ~0.2% vs `badkeys`. Fingerprint ≠ Coppersmith factorization.

**Q: Adaptive se accuracy ghatti?**  
A: Bench pe factor recall same **1.0**, latency **1.511×** better.

**Q: Production certify kar sakte ho?**  
A: Nahi. Authorized public keys only; inconclusive ≠ certification.

---

## 8) Files quick map

```
backend/app/crypto/     probes (fermat, wiener, ecm, roca, pollard, batch_gcd)
backend/app/audit/      orchestrator + adaptive planner
frontend/src/pages/     UI (Demo, Lab, Evaluation, …)
paper/                  IEEE paper + data + figures + scripts
presentation/           team deck
docs/EXPLAIN_…          this note
```

---

* Jab numbers update karo: dump JSON → regenerate figures → audit_paper_claims → recompile PDF.*
