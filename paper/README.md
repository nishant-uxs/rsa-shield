# RSA-SHIELD Research Paper

This directory contains the academic research paper for **RSA-SHIELD** in two standard peer-reviewed conference formats: **IEEE Conference Format** (`rsa_shield_ieee.tex`) and **ACM SIGCONF Format** (`rsa_shield_acm.tex`), alongside the seminal bibliography (`references.bib`) and compiled camera-ready 6-page PDFs.

---

## Paper Title
> **RSA-SHIELD: An Evidence-Tiered Auditing Framework for RSA Public-Key Infrastructure with Subquadratic Batch-GCD and Budgeted Multi-Probe Factorization**

### Authors & Affiliation (Double-Blind Review Status)
> **Note for Peer Review Submission:** The `.tex` source files and compiled PDFs currently specify **Anonymous Author(s)** and omitted institutional affiliations to strictly adhere to double-blind peer-review guidelines.
> 
> *Original Author Registry (for Camera-Ready unmasking upon acceptance):*
> - **Nishant Agarwal** (S24CSEU1512@bennett.edu.in)
> - **Adarsh Agrahari** (S24CSEU1187@bennett.edu.in)
> - **Shubh Jadiya** (S24CSEU0530@bennett.edu.in)
> - **Dr. Sachin Choudhary** (sachin.choudhary@bennett.edu.in)  
> *School of Computer Science Engineering and Technology, Bennett University, Greater Noida, India*

---

## Deliverables in this Directory

| File | Format | Page Count | Description |
|---|---|---|---|
| [`rsa_shield_ieee.tex`](./rsa_shield_ieee.tex) | LaTeX (IEEEtran) | 6 Pages | Complete paper formatted using official IEEE conference 2-column specifications (`IEEEtran.cls`). |
| [`rsa_shield_ieee.pdf`](./rsa_shield_ieee.pdf) | PDF (Camera-Ready) | **6 Pages** | Compiled publication-ready PDF using pdfTeX + BibTeX. |
| [`rsa_shield_acm.tex`](./rsa_shield_acm.tex) | LaTeX (acmart) | 6 Pages | Complete paper formatted using ACM SIGCONF specifications (`acmart.cls`, `sigconf`, `nonacm`). |
| [`rsa_shield_acm.pdf`](./rsa_shield_acm.pdf) | PDF (Camera-Ready) | **6 Pages** | Compiled publication-ready PDF with ACM typography. |
| [`references.bib`](./references.bib) | BibTeX | 15 Citations | Curated seminal references (Rivest 1978, Lenstra 1987, Wiener 1990, Heninger 2012, Bernstein 2004, Nemec 2017, NIST FIPS 203/204 2024, etc.). |

---

## Paper Highlights & Novelty

1. **Evidence-Tiered Audit Taxonomy:**
   - Deprecates the hazardous binary "PASS / SECURE" assumption.
   - Formalizes a 5-tier classification state machine: `FACTOR_FOUND`, `SUSPICIOUS`, `INCONCLUSIVE`, `NO_WEAKNESS_DETECTED`, and `INVALID_KEY`.

2. **Subquadratic Batch-GCD Engine:**
   - Implements Daniel J. Bernstein's $\mathcal{O}(N \log^2 N)$ Product and Remainder Tree algorithm.
   - Slashes execution time compared to naive $\mathcal{O}(N^2)$ pairwise GCD ($1.84\times$ speedup at $N=400$, widening at higher scales).
   - Proves Lemma 1 (Remainder Modulo Preservation) and Theorem 1 (Single-Step Common Factor Extraction).

3. **Multi-Probe Defense Pipeline:**
   - Parameter sanitizer & structural coprimality check ($\gcd(e, N)$).
   - Fermat's difference-of-squares near-twin probe.
   - Wiener's continued fractions for low private exponents ($d < \frac{1}{3}N^{1/4}$).
   - ROCA (Return of Coppersmith's Attack / CVE-2017-15361) discrete modular residue filter.
   - Budgeted Lenstra Elliptic Curve Method (ECM) factorization.

4. **Extensive Benchmarking & Comparison:**
   - Multi-criteria architectural comparison against `RsaCtfTool`, `badkeys`, `crocs-roca`, `CrypTool SanityChecker`, and `Mining Ps&Qs`.
   - Probe ablation latency table and 7-archetype synthetic corpus evaluation (100% precision, zero false positives).

5. **NIST Post-Quantum Migration (FIPS 203 / 204):**
   - Applies Mosca's Theorem for quantum risk horizons.
   - Maps legacy RSA keys to ML-KEM-768/1024 and ML-DSA-65/87.
   - Analyzes hybrid transition mechanisms (`X25519Kyber768Draft00`) to counteract "Harvest Now, Decrypt Later" (HNDL) threats.

---

## Local Compilation Instructions

### Requirements
- TeX Live or MiKTeX (with `pdflatex` and `bibtex`).
- Packages: `IEEEtran`, `acmart`, `microtype`, `booktabs`, `algorithmic`, `algorithm`.

### Building IEEE Format
```bash
pdflatex rsa_shield_ieee.tex
bibtex rsa_shield_ieee
pdflatex rsa_shield_ieee.tex
pdflatex rsa_shield_ieee.tex
```

### Building ACM Format
```bash
pdflatex rsa_shield_acm.tex
bibtex rsa_shield_acm
pdflatex rsa_shield_acm.tex
pdflatex rsa_shield_acm.tex
```

### Overleaf Import
Upload `references.bib` together with either `rsa_shield_ieee.tex` or `rsa_shield_acm.tex`. Set the compiler engine to **pdfLaTeX**.

