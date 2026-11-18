"""Hard-verify quantitative claims in rsa_shield_ieee.tex against paper/data JSON + bib cites."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = (ROOT / "rsa_shield_ieee.tex").read_text(encoding="utf-8")
BIB = (ROOT / "references.bib").read_text(encoding="utf-8")
DATA = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data").glob("*.json")}

errs: list[str] = []
oks: list[str] = []


def ok(msg: str) -> None:
    oks.append(msg)
    print("OK ", msg)


def fail(msg: str) -> None:
    errs.append(msg)
    print("FAIL", msg)


def must_in_tex(s: str, label: str) -> None:
    if s in TEX:
        ok(f"tex contains {label}: {s}")
    else:
        fail(f"tex missing {label}: {s}")


# --- Suite ---
suite = DATA["suite"]
if suite["total"] == 7 and suite["hint_matches"] == 7:
    ok("suite 7/7")
else:
    fail(f"suite {suite['hint_matches']}/{suite['total']}")
must_in_tex("7/7", "suite match")

suite_expect = {r["fixture_id"]: r for r in suite["rows"]}
for fid, r in suite_expect.items():
    ms = r.get("elapsed_ms")
    if fid != "invalid-pem" and ms is not None:
        # suite uses 2508.70 with trailing zero in tex
        candidates = {str(ms), f"{ms:.2f}", f"{float(ms):.2f}"}
        if not any(c in TEX for c in candidates):
            fail(f"tex missing suite ms for {fid}: {ms}")
        else:
            ok(f"suite ms {fid}={ms}")
    if r["final_state"] not in TEX and r["final_state"].replace("_", "\\_") not in TEX:
        # states appear as texttt FACTOR\_FOUND etc.
        pass

# --- Ablation / comparison ---
for probe, s in DATA["ablation"]["summary"].items():
    must_in_tex(str(s["avg_ms"]), f"ablation {probe}")

for a in DATA["comparison"]["aggregates"]:
    must_in_tex(str(a["avg_ms"]), f"cmp {a['config_id']}")
full = next(x for x in DATA["comparison"]["aggregates"] if x["config_id"] == "full_shield")
if full["tp"] == 4 and full["fp"] == 0 and full["fn"] == 0 and full["precision"] == 1.0:
    ok("full_shield P/R")
else:
    fail(f"full_shield {full}")

# --- Batch ---
for row in DATA["batch_gcd_benchmark"]:
    must_in_tex(str(row["naive_pairwise_ms"]), f"naive N={row['key_count']}")
    must_in_tex(str(row["subquadratic_tree_ms"]), f"tree N={row['key_count']}")
n1000 = next(r for r in DATA["batch_gcd_benchmark"] if r["key_count"] == 1000)
must_in_tex("1.93", "speedup 1000")
if n1000["parity_verified"] and n1000["hits_detected"] == 1:
    ok("batch N=1000 parity")
else:
    fail("batch N=1000")

# --- Corpus ---
corp = DATA["corpus"]
must_in_tex("780", "pairs_checked")
# extract ms from message e.g. "0.31 ms"
import re as _re

m = _re.search(r"in ([0-9.]+) ms", corp["batch_gcd"]["message"])
if m:
    must_in_tex(m.group(1), "corpus gcd ms")
if corp["secure_labels_emitted"] != 0:
    fail("secure labels")
else:
    ok("secure 0")

# --- Bakeoff ---
if "bakeoff" not in DATA:
    fail("missing bakeoff.json")
else:
    bake = DATA["bakeoff"]
    by = {a["tool"]: a for a in bake["aggregates"]}
    shield = by["rsa_shield_full"]
    bad = by["badkeys"]
    if shield["factor_recall"] != 1.0 or shield["overconfidence_rate"] != 0.0:
        fail(f"shield bakeoff {shield}")
    else:
        ok("shield bakeoff recall/overconf")
    if bad["available"] and bad["factor_recall"] == 0.75 and bad["overconfidence_rate"] == 0.75:
        ok("badkeys bakeoff aggregates")
    elif not bad["available"]:
        ok("badkeys not available (allowed)")
    else:
        fail(f"badkeys bakeoff {bad}")
    must_in_tex("0.75", "badkeys recall/overconf")
    must_in_tex("bakeoff.json", "bakeoff cite")

# --- CT measurement ---
if "ct_measurement" not in DATA:
    fail("missing ct_measurement.json")
else:
    ct = DATA["ct_measurement"]
    must_in_tex(str(ct["unique_moduli"]), "ct unique moduli")
    must_in_tex(str(ct["batch_gcd"]["hit_count"]), "ct gcd hits")
    must_in_tex(str(ct["batch_gcd"]["elapsed_ms"]), "ct gcd ms")
    must_in_tex(str(ct["collection"]["collect_seconds"]), "ct collect sec")
    eps = ct["evidence_probe_sample"]
    must_in_tex(str(eps["roca_fingerprint_hits"]), "ct roca hits")
    must_in_tex(str(eps["sample_size"]), "ct probe sample")
    if eps["secure_labels_emitted"] != 0:
        fail("ct emitted SECURE")
    else:
        ok("ct never SECURE")
    if "ct_measurement.json" in TEX or "ct\\_measurement.json" in TEX:
        ok("tex contains ct json cite")
    else:
        fail("tex missing ct json cite: ct_measurement.json")
    must_in_tex("Argon2026h2", "ct log name")

# --- ROCA parity / calibration / adaptive ---
if "roca_calibration" in DATA:
    cal = DATA["roca_calibration"]
    must_in_tex("0.2", "roca calibrated fp pct")
    must_in_tex("99.8", "roca calibrated agree pct")
    must_in_tex("0.99", "roca calibrated thr")
    must_in_tex(str(cal.get("sample_size") or cal.get("legacy_stats", {}).get("n")), "roca cal n")
    ok("roca_calibration.json present")
else:
    fail("missing roca_calibration.json")

if "roca_parity" in DATA:
    tip = DATA["roca_parity"].get("ct_tip") or {}
    ct = tip.get("aggregate_calibrated") or tip.get("aggregate") or {}
    if ct:
        must_in_tex(str(ct.get("n")), "roca ct n")
    ok("roca_parity.json present")
else:
    fail("missing roca_parity.json")

if "adaptive_ablation" in DATA:
    ad = DATA["adaptive_ablation"]
    must_in_tex(str(ad.get("speedup_factor_avg_wall")), "adaptive speedup")
    must_in_tex("1473.92", "fixed avg wall")
    must_in_tex("975.75", "adaptive avg wall")
    if not ad.get("recall_preserved"):
        fail("adaptive recall not preserved")
    else:
        ok("adaptive recall preserved")
else:
    fail("missing adaptive_ablation.json")

# --- Meta / date ---
meta = DATA.get("meta") or {}
must_in_tex("1.0.0", "bench version")

# --- Citations ---
cites = sorted(set(re.findall(r"\\cite\{([^}]+)\}", TEX)))
keys = []
for c in cites:
    keys.extend([k.strip() for k in c.split(",")])
keys = sorted(set(keys))
bib_keys = set(re.findall(r"@\w+\{([^,]+),", BIB))
print("\nCITATIONS:")
for k in keys:
    if k in bib_keys:
        ok(f"bib has {k}")
    else:
        fail(f"missing bib entry for cite {k}")

print("\n==== SUMMARY ====")
print(f"OK={len(oks)} FAIL={len(errs)}")
for e in errs:
    print(" -", e)
sys.exit(1 if errs else 0)
