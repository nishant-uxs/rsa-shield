# Related work & positioning (RSA-SHIELD)

RSA-SHIELD is an **evidence-tiered educational public-key auditing platform**.
It does **not** claim a new factorization algorithm or an Internet-scale measurement study.

## Prior work

| Work | Focus | Relation to RSA-SHIELD |
|------|--------|-------------------------|
| Mining Your Ps and Qs (USENIX Security 2012) | Batch GCD over Internet key corpora | We implement Bernstein's subquadratic product/remainder tree O(N log^2 N) for scalable inventory sweeps |
| ROCA / crocs-muni/roca (CCS 2017) | Infineon fingerprint + Coppersmith | Educational fingerprint heuristic; re-verify with authoritative tools |
| badkeys (Böck) | Production known-vuln checker | Broader coverage; we emphasize tiers + pedagogy + ECM budget |
| RsaCtfTool | Multi-attack CTF toolbox | Attack CLI vs audit UI with never-SECURE labels |
| Fermat in the wild / RSAScan | Close primes / mass scanning | We include a budgeted Fermat probe in-pipeline |

## Our contributions (honest)

1. End-to-end pipeline: parse → analyze → Fermat → Wiener → ROCA fingerprint → budgeted ECM  
2. Evidence taxonomy forbidding absolute **SECURE** labels  
3. Controlled Test Lab fixtures + `/api/v1/evaluation/suite`  
4. Subquadratic Batch-GCD engine (Bernstein product & remainder trees, O(N log^2 N)) with empirical scaling benchmarks  
5. Full-stack artifact (React + FastAPI) for demos and coursework  
6. Research evaluation bundle: ablation, configuration precision/recall, mini synthetic corpus, and batch-GCD algorithmic scaling  

## Paper tables (API)

| Table | Endpoint |
|-------|----------|
| Fixture results | `GET /api/v1/evaluation/suite` |
| Ablation / probe contribution | `GET /api/v1/evaluation/ablation` |
| Config precision–recall | `GET /api/v1/evaluation/comparison` |
| Mini corpus + batch-GCD | `GET /api/v1/evaluation/corpus` |
| Algorithmic scaling benchmark | `GET /api/v1/evaluation/batch-gcd-benchmark` |
| All-in-one JSON | `GET /api/v1/evaluation/research-bundle` |

UI: `/app/evaluation` → download JSON bundle for camera-ready tables.

## What we do **not** claim

- Breaking modern strong RSA  
- Formal security proofs from inconclusive ECM  
- Parity with production detectors (badkeys / crocs ROCA) on all CVEs  
- Internet-scale measurement (mini corpus is synthetic / lab-sized)  
