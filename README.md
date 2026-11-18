# RSA-SHIELD

**RSA Key Security Auditor for Legacy Critical Infrastructure**  
Team Aegis · Bennett University · Mentor: Dr. Sachin Choudhary

## Overview

RSA-SHIELD is a software-only cybersecurity platform that accepts RSA **public** keys/moduli, analyzes cryptographic properties, runs budgeted Lenstra ECM factorization attempts, and produces evidence-tiered audit results.

**Important:** failure to factor a key is **never** labeled “SECURE”.

Result states:

- `FACTOR_FOUND`
- `SUSPICIOUS`
- `INCONCLUSIVE`
- `NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS`
- `INVALID_KEY`

## Architecture

```mermaid
flowchart TB
  U[User] --> FE[React Dashboard]
  FE --> API[FastAPI]
  API --> ORCH[Audit Orchestrator]
  ORCH --> P[RSA Parser]
  ORCH --> A[Key Analyzer]
  ORCH --> E[ECM Engine]
  ORCH --> R[Risk / Report]
  ORCH --> DB[(SQLite / PostgreSQL)]
```

## Tech stack

| Layer | Stack |
|-------|--------|
| Frontend | React, TypeScript, Vite, Tailwind CSS v4, Recharts, React Router |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, PyCryptodome |
| Crypto | RSA parse/analyze + Lenstra ECM (budgeted) |
| Data | SQLite by default (`rsa_shield.db`) |

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://127.0.0.1:5173

### Tests

```bash
cd backend
.venv\Scripts\python -m pytest -q
```

## Demo walkthrough (~3 min)

1. Open landing → **Sir Demo** (`/app/demo`) — preferred for faculty
2. Run weak-ecm → fermat-close → wiener-small-d → normal-demo
3. Open audit details → review evidence + timeline
4. Emphasize: inconclusive / no-weakness ≠ secure
5. Optional: **Evaluation** page for paper tables; deck at `/deck/`

## Research artifacts

- IEEE paper: `paper/rsa_shield_ieee.pdf`
- Overleaf Beamer: `presentation/rsa_shield_beamer.tex`
- Team explainer: `docs/EXPLAIN_FOR_TEAM_AND_SIR.md`
- Verify paper numbers: `.\scripts\verify_paper.ps1`

## Security considerations

- Public keys/moduli only; private keys rejected
- Input size limits; no shelling out
- ECM timeouts / curve budgets
- Authorized / lab keys only

## Limitations

- Educational prototype ECM — not a claim to break modern strong RSA
- No factor within budget is inconclusive
- SQLite default (swap `DATABASE_URL` for Postgres)

## License / academic use

College project prototype for cybersecurity coursework at Bennett University.
