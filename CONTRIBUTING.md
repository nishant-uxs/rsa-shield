# Contributing (Team Aegis)

## Commits

Use Conventional Commits, one logical change per commit:

- `feat(crypto): …` — probes / orchestrator
- `feat(paper): …` — tex, data, figures
- `feat(frontend): …` — UI / demo
- `docs(…): …` — README, explainer, decks
- `chore: …` — ignore, cleanup
- `test: …` — pytest

## Before paper PRs

```powershell
.\scripts\verify_paper.ps1
```

Do not invent metrics. Freeze dumps under `paper/data/` and cite them.
