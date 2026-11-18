"""Adaptive probe budgeting for RSA-SHIELD.

Chooses Fermat steps / Pollard B1 / ECM timeout from public-key features.
Does not invent new cryptanalysis — only schedules classical probes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbePlan:
    fermat_steps: int
    pollard_b1: int
    pollard_timeout_ms: int
    ecm_timeout_ms: int
    ecm_curves: int
    ecm_b1: int
    run_fermat: bool
    run_wiener: bool
    run_pollard: bool
    run_ecm: bool
    rationale: str


def plan_probes(
    *,
    bits: int,
    e: int,
    base_ecm_timeout_ms: int,
    base_ecm_curves: int,
    base_ecm_b1: int,
    run_ecm: bool,
) -> ProbePlan:
    """Feature-driven budgets. Large modern moduli get cheaper Fermat/Pollard."""
    reasons: list[str] = []

    run_fermat = True
    run_wiener = True
    run_pollard = True
    do_ecm = run_ecm

    fermat_steps = 25_000
    pollard_b1 = min(50_000, max(10_000, base_ecm_b1))
    pollard_timeout_ms = min(1500, max(500, base_ecm_timeout_ms // 2))
    ecm_timeout = base_ecm_timeout_ms
    ecm_curves = base_ecm_curves
    ecm_b1 = base_ecm_b1

    if e.bit_length() > 64:
        reasons.append("large_e->prioritize_wiener")
        # Wiener stays on; shrink Fermat slightly
        fermat_steps = min(fermat_steps, 5_000)

    if bits < 768:
        reasons.append("small_bits->aggressive_fermat_pollard")
        fermat_steps = max(fermat_steps, 50_000)
        pollard_b1 = max(pollard_b1, 50_000)
        pollard_timeout_ms = max(pollard_timeout_ms, 1500)
        ecm_timeout = max(ecm_timeout, base_ecm_timeout_ms)
    elif bits < 1024:
        reasons.append("legacy_bits->medium_budgets")
        fermat_steps = 25_000
        pollard_b1 = 30_000
    elif bits < 2048:
        reasons.append("mid_bits->trim_fermat")
        fermat_steps = 5_000
        pollard_b1 = 20_000
        pollard_timeout_ms = min(pollard_timeout_ms, 800)
        ecm_timeout = min(ecm_timeout, max(1500, base_ecm_timeout_ms // 2))
        ecm_curves = min(ecm_curves, max(15, base_ecm_curves // 2))
    else:
        # Modern 2048+ CT-like keys: Fermat near-twin search is low-yield / expensive
        reasons.append("modern_bits->skip_fermat_shrink_ecm")
        run_fermat = False
        fermat_steps = 0
        pollard_b1 = 10_000
        pollard_timeout_ms = min(600, pollard_timeout_ms)
        ecm_timeout = min(1000, base_ecm_timeout_ms)
        ecm_curves = min(10, base_ecm_curves)
        # Still allow ECM if caller requested, but cheap
        do_ecm = run_ecm

    if not reasons:
        reasons.append("default_budgets")

    return ProbePlan(
        fermat_steps=fermat_steps,
        pollard_b1=pollard_b1,
        pollard_timeout_ms=pollard_timeout_ms,
        ecm_timeout_ms=ecm_timeout,
        ecm_curves=ecm_curves,
        ecm_b1=ecm_b1,
        run_fermat=run_fermat,
        run_wiener=run_wiener,
        run_pollard=run_pollard,
        run_ecm=do_ecm,
        rationale="+".join(reasons),
    )
