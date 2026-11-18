"""Personal end-to-end verification: every headline number + cite key vs frozen dumps."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEX = (ROOT / "paper" / "rsa_shield_ieee.tex").read_text(encoding="utf-8")
BIB = (ROOT / "paper" / "references.bib").read_text(encoding="utf-8")
DATA = ROOT / "paper" / "data"
ROCA_PY = (ROOT / "backend" / "app" / "crypto" / "roca.py").read_text(encoding="utf-8")

fails: list[str] = []
oks: list[str] = []


def ok(msg: str) -> None:
    oks.append(msg)
    print("OK ", msg)


def fail(msg: str) -> None:
    fails.append(msg)
    print("FAIL", msg)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def must(s: str, label: str) -> None:
    if s not in TEX:
        fail(f"missing in tex: {label} = {s!r}")
    else:
        ok(f"tex has {label}={s}")


def main() -> int:
    # --- bakeoff ---
    b = load("bakeoff.json")
    by_tool = {a["tool"]: a for a in b["aggregates"]}
    shield_a = by_tool["rsa_shield_full"]
    bad_a = by_tool["badkeys"]
    must(str(shield_a["overconfidence_rate"]), "shield overconf")
    must(str(shield_a["factor_recall"]), "shield recall")
    must(str(bad_a["overconfidence_rate"]), "badkeys overconf")
    must(str(bad_a["factor_recall"]), "badkeys recall")
    must(f"TP${{=}}{shield_a['tp']}", "shield TP")
    must(f"FN${{=}}{shield_a['fn']}", "shield FN")
    must(f"TP${{=}}{bad_a['tp']}", "badkeys TP")
    must(f"FN${{=}}{bad_a['fn']}", "badkeys FN")
    must(
        f"{shield_a['overconfidence_numerator']}/{shield_a['overconfidence_denominator']}",
        "shield overconf fraction",
    )
    must(
        f"{bad_a['overconfidence_numerator']}/{bad_a['overconfidence_denominator']}",
        "badkeys overconf fraction",
    )
    rows = b["rows"]
    shield = [r for r in rows if r["tool"] == "rsa_shield_full"]
    s_over = sum(1 for r in shield if r.get("emitted_secure_or_pass_like"))
    if abs(shield_a["overconfidence_rate"] - 0.0) > 1e-9:
        fail("shield overconf not 0")
    else:
        ok(f"bakeoff shield rows={len(shield)} overconf_emits={s_over} tp={shield_a['tp']}")

    # --- adaptive ---
    ad = load("adaptive_ablation.json")
    must(str(ad["speedup_factor_avg_wall"]), "adaptive speedup")
    must(str(ad["fixed"]["aggregate"]["avg_wall_ms"]), "fixed wall")
    must(str(ad["adaptive"]["aggregate"]["avg_wall_ms"]), "adaptive wall")
    if not ad.get("recall_preserved") or ad["adaptive"]["aggregate"]["factor_recall"] != 1.0:
        fail("adaptive recall not preserved")
    else:
        ok("adaptive recall preserved + 1.0")
    must("TP${=}5", "adaptive TP=5")

    # --- CT ---
    ct = load("ct_measurement.json")
    must(str(ct["unique_moduli"]), "ct unique")
    must(str(ct["batch_gcd"]["hit_count"]), "ct gcd hits")
    must(str(ct["batch_gcd"]["elapsed_ms"]), "ct gcd ms")
    must(str(ct["collection"]["collect_seconds"]), "ct collect")
    eps = ct["evidence_probe_sample"]
    must(str(eps["roca_fingerprint_hits"]), "ct roca hits")
    must(str(eps["sample_size"]), "ct sample")
    must(str(eps["tier_counts"]["SUSPICIOUS"]), "ct suspicious")
    must(str(eps["tier_counts"]["NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS"]), "ct no_weak")
    if eps["secure_labels_emitted"] != 0:
        fail("ct emitted SECURE")
    else:
        ok("ct never SECURE")
    rate = round(eps["roca_fingerprint_hits"] / eps["sample_size"] * 100, 2)
    must(f"{rate}", "ct legacy roca pct")
    must(str(ct["collection"]["entries_seen"]), "ct entries_seen")
    hist = ct["bitlength_histogram"]
    must(str(hist["2048"]), "ct 2048 count")
    must(str(hist["4096"]), "ct 4096 count")
    must(str(hist["3072"]), "ct 3072 count")
    per = ct["collection"]["per_log"]
    adds = [p["unique_added"] for p in per]
    must(f"${adds[0]}$+${adds[1]}$+${adds[2]}$", "ct per-log adds")

    # --- ROCA calibration ---
    cal = load("roca_calibration.json")
    ls, cs = cal["legacy_stats"], cal["calibrated_stats"]
    if ls["edu_positive"] != 375 or ls["n"] != 500:
        fail(f"legacy cal stats unexpected {ls}")
    if cs["edu_positive"] != 1 or cs["n"] != 500:
        fail(f"calibrated stats unexpected {cs}")
    if abs(ls["fp_rate"] - 0.75) > 1e-9 or abs(cs["fp_rate"] - 0.002) > 1e-9:
        fail("fp rates mismatch")
    if abs(cs["agreement_rate"] - 0.998) > 1e-9:
        fail("agreement mismatch")
    if cal["chosen_calibrated_profile"]["ratio_threshold"] != 0.99:
        fail("threshold mismatch")
    must("375/500", "cal legacy positives")
    must("1/500", "cal calibrated fp count")
    must("0.2\\%", "cal fp pct tex")
    must("99.8\\%", "cal agree pct tex")
    must("0.9973", "fp reduction")
    must("0.99", "thr")
    ok("calibration numeric invariants")

    # --- ROCA parity ---
    rp = load("roca_parity.json")
    leg = rp["ct_tip"]["aggregate_legacy"]
    calp = rp["ct_tip"]["aggregate_calibrated"]
    if leg["n"] != 400 or abs(leg["edu_positive_rate"] - 0.7475) > 1e-9:
        fail(f"parity legacy unexpected {leg}")
    if abs(leg["agreement_rate"] - 0.2525) > 1e-9:
        fail("parity legacy agree")
    if calp["n"] != 400 or calp["agreement_rate"] != 1.0:
        fail(f"parity calibrated unexpected {calp}")
    must("25.25\\%", "parity legacy agree")
    must("100\\%", "parity cal agree")
    ba = rp["bench"]["aggregate_calibrated"]
    if ba["n"] != 7 or ba["agreement_rate"] != 1.0:
        fail(f"bench cal agree unexpected {ba}")
    must("7/7", "bench/suite 7/7")
    ok("parity invariants")

    # --- suite timings ---
    suite = load("suite.json")
    for r in suite["rows"]:
        must(str(r["elapsed_ms"]), f"suite {r['fixture_id']} ms")
    if suite["hint_matches"] != suite["total"]:
        fail("suite hint matches != total")
    else:
        ok(f"suite {suite['hint_matches']}/{suite['total']}")

    # --- ablation ---
    abl = load("ablation.json")
    for k, v in abl["summary"].items():
        must(str(v["avg_ms"]), f"ablation {k}")
        must(str(v["hit_rate"] if v["hit_rate"] is not None else "0.00"), f"ablation rate {k}")

    # --- comparison ---
    cmp = load("comparison.json")
    for a in cmp["aggregates"]:
        must(str(a["avg_ms"]), f"cmp {a['config_id']}")
    full = next(x for x in cmp["aggregates"] if x["config_id"] == "full_shield")
    if full["precision"] != 1.0 or full["recall"] != 1.0:
        fail("full_shield P/R")
    else:
        ok("full_shield P/R=1")
    must("861.14", "full avg ms")

    # --- batch ---
    bat = load("batch_gcd_benchmark.json")
    for r in bat:
        n = r["key_count"]
        must(str(r["naive_pairwise_ms"]), f"batch naive {n}")
        must(str(r["subquadratic_tree_ms"]), f"batch tree {n}")
        if not r.get("parity_verified"):
            fail(f"batch parity failed n={n}")
    must("1.93", "batch speedup 1000")
    must("0.82", "batch speedup 20")
    must("79{,}800", "pairs 400 formatted")
    must("19{,}900", "pairs 200 formatted")

    # --- corpus ---
    corp = load("corpus.json")
    if corp["secure_labels_emitted"] != 0:
        fail("corpus SECURE")
    must(str(corp["batch_gcd"]["pairs_checked"]), "corpus pairs_checked")
    msg = corp["batch_gcd"].get("message", "")
    if "0.31" not in msg and "0.31" not in TEX:
        fail("corpus gcd 0.31 ms missing")
    else:
        must("0.31", "corpus gcd ms")
    must(str(corp["corpus_size"]), "corpus size")
    if corp["batch_gcd"].get("hit_count") != 1:
        fail("corpus gcd hit_count != 1")
    else:
        ok(f"corpus size={corp['corpus_size']} secure=0 gcd_hits=1")

    # --- code profile lock ---
    if '"ratio_threshold": 0.99' not in ROCA_PY or '"min_gcd": 2' not in ROCA_PY:
        fail("roca.py calibrated constants mismatch")
    else:
        ok("code calibrated profile matches paper")

    # --- citations ---
    cites = set(re.findall(r"\\cite\{([^}]+)\}", TEX))
    keys = set(m.group(1).strip() for m in re.finditer(r"@\w+\{([^,]+),", BIB))
    missing = set()
    used = set()
    for c in cites:
        for k in c.split(","):
            k = k.strip()
            if not k:
                continue
            used.add(k)
            if k not in keys:
                missing.add(k)
    if missing:
        fail(f"cite missing from bib: {sorted(missing)}")
    else:
        ok(f"all cite keys resolve ({len(used)} used / {len(keys)} bib)")
    unused = sorted(keys - used)
    print("INFO unused bib keys:", unused or "none")

    print("\n==== PERSONAL VERIFY ====")
    print(f"OK={len(oks)} FAIL={len(fails)}")
    for fmsg in fails:
        print(" -", fmsg)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
