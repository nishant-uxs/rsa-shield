import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.research_eval import (
    run_ablation,
    run_configuration_comparison,
    run_mini_corpus_study,
)


def test_ablation_has_summary():
    r = run_ablation(ecm_timeout_ms=1500)
    assert "summary" in r
    assert "fermat" in r["summary"]
    assert r["summary"]["fermat"]["weak_fixtures"] >= 1


def test_comparison_aggregates():
    r = run_configuration_comparison(ecm_timeout_ms=1500)
    assert r["aggregates"]
    full = next(a for a in r["aggregates"] if a["config_id"] == "full_shield")
    assert full["emits_secure_label"] is False
    assert full["recall"] is None or full["recall"] >= 0


def test_mini_corpus_shared_factor():
    r = run_mini_corpus_study(size=20)
    assert r["corpus_size"] >= 12
    assert r["secure_labels_emitted"] == 0
    assert r["batch_gcd"]["hit_count"] >= 1
