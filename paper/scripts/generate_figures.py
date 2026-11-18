"""Generate IEEE-friendly figures from paper/data JSON dumps."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"
FIGS = Path(__file__).resolve().parents[1] / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

# Grayscale-safe IEEE palette
C0 = "#1a1a1a"
C1 = "#4d4d4d"
C2 = "#808080"
C3 = "#b3b3b3"
ACCENT = "#2c5f8a"


def _save(fig: plt.Figure, name: str) -> None:
    for ext in ("pdf", "png"):
        out = FIGS / f"{name}.{ext}"
        fig.savefig(out, bbox_inches="tight", dpi=300)
        print(f"wrote {out.name}")
    plt.close(fig)


def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")
    stages = [
        (0.25, "Parse\nPEM/n+e"),
        (1.9, "Analyze"),
        (3.4, "Fermat"),
        (4.8, "Wiener"),
        (6.2, "ROCA\nfp"),
        (7.7, "Pollard\np-1"),
        (9.3, "Budgeted\nECM"),
        (10.9, "Evidence\ntiers"),
    ]
    for x, label in stages:
        box = FancyBboxPatch(
            (x - 0.55, 0.85),
            1.15,
            1.3,
            boxstyle="round,pad=0.05,rounding_size=0.12",
            linewidth=1.1,
            edgecolor=C0,
            facecolor="#f2f2f2",
        )
        ax.add_patch(box)
        ax.text(x + 0.02, 1.5, label, ha="center", va="center", fontsize=8, color=C0)
    for i in range(len(stages) - 1):
        x0 = stages[i][0] + 0.62
        x1 = stages[i + 1][0] - 0.58
        ax.annotate(
            "",
            xy=(x1, 1.5),
            xytext=(x0, 1.5),
            arrowprops=dict(arrowstyle="->", color=C1, lw=1.2),
        )
    ax.set_title("RSA-SHIELD multi-probe audit pipeline", fontsize=10, pad=6)
    _save(fig, "fig_pipeline")


def fig_ablation_latency() -> None:
    ablation = json.loads((DATA / "ablation.json").read_text(encoding="utf-8"))
    summary = ablation["summary"]
    labels = ["analyzer", "fermat", "wiener", "roca", "ecm"]
    ms = [summary[k]["avg_ms"] for k in labels]
    hits = [summary[k]["factor_hits_on_weak_fixtures"] for k in labels]
    weak = summary["analyzer"]["weak_fixtures"]

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
    axes[0].bar(labels, ms, color=[C1, ACCENT, C1, C2, C0])
    axes[0].set_ylabel("Avg latency (ms)")
    axes[0].set_title("Per-probe average latency")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].set_yscale("log")
    axes[0].grid(axis="y", linestyle=":", alpha=0.5)

    axes[1].bar(labels, hits, color=[C1, ACCENT, C1, C2, C0])
    axes[1].set_ylabel(f"Factor hits / {weak} weak fixtures")
    axes[1].set_ylim(0, weak)
    axes[1].set_title("Probe contribution on weak fixtures")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(axis="y", linestyle=":", alpha=0.5)

    fig.tight_layout()
    _save(fig, "fig_ablation_latency")


def fig_config_recall() -> None:
    comparison = json.loads((DATA / "comparison.json").read_text(encoding="utf-8"))
    aggs = comparison["aggregates"]
    labels = ["Analyzer", "+Fermat", "+Wiener", "+ECM", "Full\nSHIELD"]
    precision = [a["precision"] for a in aggs]
    recall = [a["recall"] for a in aggs]
    x = range(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    ax.bar([i - width / 2 for i in x], precision, width, label="Precision", color=ACCENT)
    ax.bar([i + width / 2 for i in x], recall, width, label="Recall", color=C1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score")
    ax.set_title("Configuration comparison on controlled fixtures")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    for i, a in enumerate(aggs):
        ax.text(i, 1.05, f"FP={a['fp']}", ha="center", fontsize=7, color=C1)
    fig.tight_layout()
    _save(fig, "fig_config_recall")


def fig_batch_gcd_scale() -> None:
    rows = json.loads((DATA / "batch_gcd_benchmark.json").read_text(encoding="utf-8"))
    n = [r["key_count"] for r in rows]
    naive = [r["naive_pairwise_ms"] for r in rows]
    tree = [r["subquadratic_tree_ms"] for r in rows]

    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    ax.plot(n, naive, "o-", color=C1, label="Naive pairwise $O(N^2)$")
    ax.plot(n, tree, "s-", color=ACCENT, label="Product/remainder tree")
    ax.set_xlabel("Moduli count $N$")
    ax.set_ylabel("Runtime (ms)")
    ax.set_title("Batch-GCD scaling (one planted shared prime)")
    ax.legend(frameon=False)
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    _save(fig, "fig_batch_gcd_scale")


def fig_corpus_states() -> None:
    corpus = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))
    counts = corpus["class_counts"]
    factors = corpus.get("factor_finds_by_class", {})
    labels = list(counts.keys())
    vals = [counts[k] for k in labels]
    factor_vals = [factors.get(k, 0) for k in labels]

    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    x = range(len(labels))
    ax.bar(x, vals, color=C3, label="Keys in class", edgecolor=C0, linewidth=0.6)
    ax.bar(x, factor_vals, color=ACCENT, label="Factor evidence", edgecolor=C0, linewidth=0.6)
    ax.set_xticks(list(x))
    ax.set_xticklabels([l.replace("_", "\n") for l in labels], fontsize=7)
    ax.set_ylabel("Count")
    ax.set_title(
        f"Mini corpus (n={corpus['corpus_size']}): classes and factor hits; "
        f"batch-GCD hits={corpus['batch_gcd']['hit_count']}; SECURE labels=0"
    )
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    _save(fig, "fig_corpus_states")


def fig_bakeoff() -> None:
    path = DATA / "bakeoff.json"
    if not path.exists():
        print("skip fig_bakeoff (no bakeoff.json)")
        return
    bake = json.loads(path.read_text(encoding="utf-8"))
    aggs = [a for a in bake["aggregates"] if a.get("available")]
    if not aggs:
        print("skip fig_bakeoff (no available tools)")
        return
    labels = []
    recall = []
    overconf = []
    for a in aggs:
        labels.append(a["tool"].replace("_", "\n"))
        recall.append(a["factor_recall"] if a["factor_recall"] is not None else 0.0)
        overconf.append(a["overconfidence_rate"] if a["overconfidence_rate"] is not None else 0.0)

    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    x = range(len(labels))
    width = 0.36
    ax.bar([i - width / 2 for i in x], recall, width, label="Factor recall", color=ACCENT)
    ax.bar([i + width / 2 for i in x], overconf, width, label="Overconfidence rate", color=C1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Rate")
    ax.set_title("Epistemic bake-off on RSA-Auditor Bench")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    _save(fig, "fig_bakeoff")


def fig_ct_measurement() -> None:
    path = DATA / "ct_measurement.json"
    if not path.exists():
        print("skip fig_ct_measurement")
        return
    ct = json.loads(path.read_text(encoding="utf-8"))
    bits = ct.get("bitlength_histogram") or {}
    tiers = ct.get("evidence_probe_sample", {}).get("tier_counts") or {}

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    b_labels = list(bits.keys())
    b_vals = [bits[k] for k in b_labels]
    axes[0].bar(b_labels, b_vals, color=ACCENT, edgecolor=C0, linewidth=0.6)
    axes[0].set_xlabel("Modulus bits")
    axes[0].set_ylabel("Unique moduli")
    axes[0].set_title(f"Public CT sample (n={ct.get('unique_moduli')})")
    axes[0].grid(axis="y", linestyle=":", alpha=0.5)

    t_labels = list(tiers.keys())
    t_vals = [tiers[k] for k in t_labels]
    short = [l.replace("NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS", "NO_WEAKNESS\n(by checks)") for l in t_labels]
    axes[1].bar(range(len(short)), t_vals, color=C1, edgecolor=C0, linewidth=0.6)
    axes[1].set_xticks(range(len(short)))
    axes[1].set_xticklabels(short, fontsize=7)
    axes[1].set_ylabel("Count")
    axes[1].set_title(
        f"Evidence tiers on probe sample (SECURE="
        f"{ct.get('evidence_probe_sample', {}).get('secure_labels_emitted', 0)})"
    )
    axes[1].grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    _save(fig, "fig_ct_measurement")


def fig_roca_parity() -> None:
    """Before/after calibration bars (legacy vs calibrated vs badkeys)."""
    path = DATA / "roca_parity.json"
    cal_path = DATA / "roca_calibration.json"
    if not path.exists() and not cal_path.exists():
        print("skip fig_roca_parity")
        return
    legacy = calibrated = None
    n = None
    if path.exists():
        d = json.loads(path.read_text(encoding="utf-8"))
        tip = d.get("ct_tip") or {}
        legacy = tip.get("aggregate_legacy") or tip.get("aggregate")
        calibrated = tip.get("aggregate_calibrated") or tip.get("aggregate")
        if legacy:
            n = legacy.get("n")
    if cal_path.exists():
        c = json.loads(cal_path.read_text(encoding="utf-8"))
        legacy = {
            "edu_false_positive_rate_vs_badkeys": c["legacy_stats"]["fp_rate"],
            "agreement_rate": c["legacy_stats"]["agreement_rate"],
            "edu_positive_rate": c["legacy_stats"]["edu_positive_rate"],
        }
        calibrated = {
            "edu_false_positive_rate_vs_badkeys": c["calibrated_stats"]["fp_rate"],
            "agreement_rate": c["calibrated_stats"]["agreement_rate"],
            "edu_positive_rate": c["calibrated_stats"]["edu_positive_rate"],
        }
        n = c.get("sample_size") or c["legacy_stats"]["n"]
    if not legacy or not calibrated:
        print("skip fig_roca_parity (incomplete)")
        return
    labels = ["Legacy FP", "Calibrated FP", "Legacy agree", "Calibrated agree"]
    vals = [
        legacy.get("edu_false_positive_rate_vs_badkeys", 0) * 100,
        calibrated.get("edu_false_positive_rate_vs_badkeys", 0) * 100,
        legacy.get("agreement_rate", 0) * 100,
        calibrated.get("agreement_rate", 0) * 100,
    ]
    fig, ax = plt.subplots(figsize=(6.4, 2.55))
    ax.bar(labels, vals, color=[C1, ACCENT, C0, C2], edgecolor=C0, linewidth=0.5)
    ax.set_ylabel("Rate (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"ROCA calibration vs badkeys (CT tip n={n})")
    ax.tick_params(axis="x", labelsize=7)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    _save(fig, "fig_roca_parity")


def fig_adaptive() -> None:
    path = DATA / "adaptive_ablation.json"
    if not path.exists():
        print("skip fig_adaptive")
        return
    d = json.loads(path.read_text(encoding="utf-8"))
    fa = d["fixed"]["aggregate"]
    aa = d["adaptive"]["aggregate"]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8))
    axes[0].bar(["Fixed", "Adaptive"], [fa["avg_wall_ms"], aa["avg_wall_ms"]], color=[C1, ACCENT])
    axes[0].set_ylabel("Avg wall time (ms)")
    axes[0].set_title("Scheduler latency")
    axes[0].grid(axis="y", linestyle=":", alpha=0.5)
    axes[1].bar(["Fixed", "Adaptive"], [fa["factor_recall"], aa["factor_recall"]], color=[C1, ACCENT])
    axes[1].set_ylim(0, 1.15)
    axes[1].set_ylabel("Factor recall")
    axes[1].set_title(f"Recall preserved (speedup={d.get('speedup_factor_avg_wall')}x)")
    axes[1].grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    _save(fig, "fig_adaptive")


def main() -> None:
    fig_pipeline()
    fig_ablation_latency()
    fig_config_recall()
    fig_batch_gcd_scale()
    fig_corpus_states()
    fig_bakeoff()
    fig_ct_measurement()
    fig_roca_parity()
    fig_adaptive()
    print("figures ready")


if __name__ == "__main__":
    main()
