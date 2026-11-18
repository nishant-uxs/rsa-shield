"""Compare fixed vs adaptive probe budgets on RSA-Auditor Bench fixtures."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.audit.orchestrator import run_audit_pipeline  # noqa: E402
from app.crypto.parser import n_to_hex  # noqa: E402
from app.services.fixtures import FIXTURES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
ECM_TIMEOUT = 2500


def _run_mode(adaptive: bool) -> list[dict[str, Any]]:
    rows = []
    for fx in FIXTURES:
        if fx["id"] == "invalid-pem":
            continue
        n = fx.get("n")
        e = int(fx.get("e") or 65537)
        if n is None:
            from app.crypto.parser import parse_pem

            parsed = parse_pem(fx["pem"])
            n_hex = n_to_hex(parsed.n)
            e = parsed.e
            expects = bool(fx.get("expects_factor"))
        else:
            n_hex = n_to_hex(int(n))
            expects = bool(fx.get("expects_factor"))

        t0 = time.perf_counter()
        result = run_audit_pipeline(
            n_hex,
            e,
            run_ecm=True,
            timeout_ms=ECM_TIMEOUT if fx["id"] != "legacy-1024" else max(ECM_TIMEOUT, 8000),
            adaptive=adaptive,
        )
        wall = (time.perf_counter() - t0) * 1000
        rows.append(
            {
                "fixture_id": fx["id"],
                "expects_factor": expects,
                "factor_found": bool(result["factor_found"]),
                "factor_method": result.get("factor_method"),
                "final_state": result["final_state"],
                "elapsed_ms": round(result.get("elapsed_ms") or wall, 2),
                "wall_ms": round(wall, 2),
                "probe_plan": result.get("probe_plan"),
                "correct": (bool(result["factor_found"]) == expects)
                if expects or fx["category"] == "weak"
                else (not result["factor_found"]),
            }
        )
    return rows


def _agg(rows: list[dict[str, Any]]) -> dict[str, Any]:
    weak = [r for r in rows if r["expects_factor"]]
    tp = sum(1 for r in weak if r["factor_found"])
    fn = sum(1 for r in weak if not r["factor_found"])
    return {
        "n": len(rows),
        "weak_fixtures": len(weak),
        "tp": tp,
        "fn": fn,
        "factor_recall": round(tp / max(len(weak), 1), 3),
        "avg_wall_ms": round(sum(r["wall_ms"] for r in rows) / max(len(rows), 1), 2),
        "avg_elapsed_ms": round(sum(r["elapsed_ms"] for r in rows) / max(len(rows), 1), 2),
        "secure_labels": sum(1 for r in rows if r["final_state"] == "SECURE"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fixed = _run_mode(False)
    adaptive = _run_mode(True)
    fa, aa = _agg(fixed), _agg(adaptive)
    speedup = None
    if aa["avg_wall_ms"] > 0:
        speedup = round(fa["avg_wall_ms"] / aa["avg_wall_ms"], 3)
    payload = {
        "study": "adaptive_probe_scheduler_ablation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ecm_timeout_ms_baseline": ECM_TIMEOUT,
        "disclaimer": (
            "Compares fixed vs feature-adaptive probe budgets on Bench fixtures. "
            "Adaptive mode must not reduce factor recall on planted weak classes."
        ),
        "fixed": {"rows": fixed, "aggregate": fa},
        "adaptive": {"rows": adaptive, "aggregate": aa},
        "speedup_factor_avg_wall": speedup,
        "recall_preserved": fa["factor_recall"] == aa["factor_recall"],
    }
    path = OUT / "adaptive_ablation.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    print("fixed", fa)
    print("adaptive", aa)
    print("speedup", speedup, "recall_preserved", payload["recall_preserved"])


if __name__ == "__main__":
    main()
