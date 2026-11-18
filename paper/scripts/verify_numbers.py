import json
from pathlib import Path

d = Path(__file__).resolve().parents[1] / "data"
suite = json.loads((d / "suite.json").read_text(encoding="utf-8"))
abl = json.loads((d / "ablation.json").read_text(encoding="utf-8"))
cmp = json.loads((d / "comparison.json").read_text(encoding="utf-8"))
corp = json.loads((d / "corpus.json").read_text(encoding="utf-8"))
bat = json.loads((d / "batch_gcd_benchmark.json").read_text(encoding="utf-8"))
meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))

print("META", meta)
print("SUITE", suite["total"], suite["hint_matches"], suite["ecm_timeout_ms_baseline"])
for r in suite["rows"]:
    print(
        f"  {r['fixture_id']:16} {r['final_state']:16} {str(r.get('factor_method')):12} {r['elapsed_ms']}"
    )
print("ABLATION")
for k, v in abl["summary"].items():
    print(k, v)
print("COMPARISON")
for a in cmp["aggregates"]:
    print(a)
print(
    "CORPUS",
    corp["corpus_size"],
    corp["secure_labels_emitted"],
    corp["batch_gcd"]["hit_count"],
    corp["class_counts"],
    corp["factor_finds_by_class"],
    corp["summary"],
)
print("BATCH")
for r in bat:
    print(r)
