"""Dump measured evaluation JSON for the IEEE paper tables/figures."""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.crypto.batch_gcd import benchmark_batch_gcd_scaling  # noqa: E402
from app.services.evaluation import run_evaluation_suite  # noqa: E402
from app.services.research_eval import (  # noqa: E402
    run_ablation,
    run_configuration_comparison,
    run_mini_corpus_study,
)

OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(parents=True, exist_ok=True)

ECM_TIMEOUT_MS = 2500
CORPUS_SIZE = 40
BATCH_SIZES = [20, 50, 100, 200, 400, 1000]


def _write(name: str, payload: object) -> None:
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"wrote {path.name}")


def main() -> None:
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "ecm_timeout_ms": ECM_TIMEOUT_MS,
        "corpus_size": CORPUS_SIZE,
        "batch_gcd_sizes": BATCH_SIZES,
        "emits_secure_label": False,
        "bench_version": "1.0.0",
    }
    _write("meta.json", meta)

    suite = run_evaluation_suite(ecm_timeout_ms=ECM_TIMEOUT_MS)
    _write("suite.json", suite)

    ablation = run_ablation(ecm_timeout_ms=ECM_TIMEOUT_MS)
    _write("ablation.json", ablation)

    comparison = run_configuration_comparison(ecm_timeout_ms=ECM_TIMEOUT_MS)
    _write("comparison.json", comparison)

    corpus = run_mini_corpus_study(size=CORPUS_SIZE)
    _write("corpus.json", corpus)

    batch = benchmark_batch_gcd_scaling(BATCH_SIZES)
    _write("batch_gcd_benchmark.json", batch)

    # Bake-off is a separate script (optional badkeys); invoke in-process.
    bakeoff_script = Path(__file__).resolve().parent / "run_tool_bakeoff.py"
    if bakeoff_script.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("run_tool_bakeoff", bakeoff_script)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()

    print("done")


if __name__ == "__main__":
    main()
