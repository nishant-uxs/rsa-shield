"""Calibrate educational ROCA thresholds against badkeys on a public CT tip sample.

Sweeps (ratio_threshold, min_gcd) to minimize false positives vs badkeys' roca
finding, then writes paper/data/roca_calibration.json and prints the chosen config.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.crypto.roca import (  # noqa: E402
    extract_roca_features,
    roca_fingerprint,
)

OUT = Path(__file__).resolve().parents[1] / "data"
CT_LOG = "https://ct.googleapis.com/logs/us1/argon2026h2/"


def _badkeys_roca(n: int, e: int) -> bool:
    import badkeys  # type: ignore

    findings = badkeys.checkrsa(n, e) or {}
    return "roca" in findings


def _fetch_ct(limit: int = 500) -> list[tuple[int, int, int]]:
    import base64
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import rsa

    def read_u24(buf: bytes, off: int) -> tuple[int, int]:
        return int.from_bytes(buf[off : off + 3], "big"), off + 3

    def der_from_leaf(leaf_b64: str) -> bytes | None:
        raw = base64.b64decode(leaf_b64)
        if len(raw) < 15:
            return None
        entry_type = int.from_bytes(raw[10:12], "big")
        off = 12
        if entry_type != 0:
            return None
        length, off = read_u24(raw, off)
        der = raw[off : off + length]
        return der if len(der) == length else None

    base = CT_LOG.rstrip("/") + "/"
    req = urllib.request.Request(base + "ct/v1/get-sth", headers={"User-Agent": "RSA-SHIELD-ROCA-Cal/1.0"})
    sth = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    tree_size = int(sth["tree_size"])
    idx = max(0, tree_size - 50_000)
    out: list[tuple[int, int, int]] = []
    seen: set[int] = set()
    pages = 0
    while len(out) < limit and pages < 3000 and idx < tree_size:
        end = min(idx + 31, tree_size - 1)
        url = f"{base}ct/v1/get-entries?start={idx}&end={end}"
        req = urllib.request.Request(url, headers={"User-Agent": "RSA-SHIELD-ROCA-Cal/1.0"})
        try:
            payload = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
        except Exception:  # noqa: BLE001
            time.sleep(1.0)
            pages += 1
            idx = end + 1
            continue
        for ent in payload.get("entries") or []:
            der = der_from_leaf(ent["leaf_input"])
            if der is None:
                try:
                    extra = base64.b64decode(ent.get("extra_data") or "")
                    if len(extra) >= 3:
                        ln = int.from_bytes(extra[0:3], "big")
                        der = extra[3 : 3 + ln] if len(extra) >= 3 + ln else None
                except Exception:  # noqa: BLE001
                    der = None
            if not der:
                continue
            try:
                cert = x509.load_der_x509_certificate(der)
                pub = cert.public_key()
                if not isinstance(pub, rsa.RSAPublicKey):
                    continue
                nums = pub.public_numbers()
                if nums.n in seen:
                    continue
                seen.add(nums.n)
                out.append((nums.n, nums.e, pub.key_size))
            except Exception:  # noqa: BLE001
                continue
            if len(out) >= limit:
                break
        pages += 1
        idx = end + 1
        time.sleep(0.03)
        if pages % 40 == 0:
            print(f"  fetch pages={pages} unique={len(out)}", flush=True)
    return out


def _decide(feat: dict[str, Any], ratio_thr: float, min_gcd: int, min_bits: int) -> bool:
    return (
        feat["bits"] >= min_bits
        and feat["gcd_n1_M"] >= min_gcd
        and feat["ratio"] >= ratio_thr
    )


def _stats(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    n = len(rows)
    edu = sum(1 for r in rows if r[key])
    auth = sum(1 for r in rows if r["badkeys_roca"])
    fp = sum(1 for r in rows if r[key] and not r["badkeys_roca"])
    fn = sum(1 for r in rows if (not r[key]) and r["badkeys_roca"])
    tp = sum(1 for r in rows if r[key] and r["badkeys_roca"])
    tn = sum(1 for r in rows if (not r[key]) and (not r["badkeys_roca"]))
    return {
        "n": n,
        "edu_positive": edu,
        "edu_positive_rate": round(edu / max(n, 1), 4),
        "badkeys_roca": auth,
        "fp_vs_badkeys": fp,
        "fp_rate": round(fp / max(n, 1), 4),
        "fn_vs_badkeys": fn,
        "tp": tp,
        "tn": tn,
        "agreement_rate": round((tp + tn) / max(n, 1), 4),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Fetching CT tip sample for calibration...", flush=True)
    moduli = _fetch_ct(limit=500)
    print(f"fetched {len(moduli)} unique RSA moduli", flush=True)

    base_rows = []
    for n, e, bits in moduli:
        feat = extract_roca_features(n)
        auth = _badkeys_roca(n, e)
        legacy = roca_fingerprint(n, profile="legacy")
        base_rows.append(
            {
                "bits": bits,
                "features": feat,
                "badkeys_roca": auth,
                "legacy_positive": bool(legacy.fingerprint_positive),
                "legacy_score": legacy.score,
            }
        )

    ratio_grid = [0.72, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.99]
    gcd_grid = [2, 6, 14, 30, 42, 78, 210]
    candidates = []
    for thr in ratio_grid:
        for mg in gcd_grid:
            labeled = []
            for r in base_rows:
                pos = _decide(r["features"], thr, mg, 512)
                labeled.append({**r, "cal_positive": pos})
            st = _stats(labeled, "cal_positive")
            # Prefer: minimize FP, then maximize agreement, then higher thr (more conservative)
            score = (st["fp_vs_badkeys"], -st["agreement_rate"], -thr, mg)
            candidates.append(
                {
                    "ratio_threshold": thr,
                    "min_gcd": mg,
                    "min_bits": 512,
                    "stats": st,
                    "sort_key": score,
                }
            )

    candidates.sort(key=lambda c: c["sort_key"])
    best = candidates[0]
    # Drop sort_key for JSON
    for c in candidates:
        c.pop("sort_key", None)

    # Apply chosen config as calibrated positives
    for r in base_rows:
        r["calibrated_positive"] = _decide(
            r["features"],
            best["ratio_threshold"],
            best["min_gcd"],
            best["min_bits"],
        )
        # shrink features for JSON size
        r["features"] = {
            "gcd_n1_M": r["features"]["gcd_n1_M"],
            "ratio": r["features"]["ratio"],
            "bits": r["features"]["bits"],
        }

    legacy_stats = _stats(
        [{**r, "legacy_positive": r["legacy_positive"]} for r in base_rows],
        "legacy_positive",
    )
    cal_stats = _stats(
        [{**r, "calibrated_positive": r["calibrated_positive"]} for r in base_rows],
        "calibrated_positive",
    )

    fp_reduction = None
    if legacy_stats["fp_rate"] > 0:
        fp_reduction = round(
            (legacy_stats["fp_rate"] - cal_stats["fp_rate"]) / legacy_stats["fp_rate"], 4
        )

    payload = {
        "study": "roca_threshold_calibration",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "Calibration minimizes educational false positives vs badkeys ROCA on a CT tip sample. "
            "badkeys is a fingerprint reference, not proof of Infineon compromise. "
            "Calibrated heuristic remains SUSPICIOUS-only, never a factorization claim."
        ),
        "sample_size": len(base_rows),
        "log_url": CT_LOG,
        "legacy_profile": {"ratio_threshold": 0.72, "min_gcd": 2, "min_bits": 512},
        "chosen_calibrated_profile": {
            "ratio_threshold": best["ratio_threshold"],
            "min_gcd": best["min_gcd"],
            "min_bits": best["min_bits"],
        },
        "legacy_stats": legacy_stats,
        "calibrated_stats": cal_stats,
        "fp_rate_reduction": fp_reduction,
        "top_candidates": candidates[:10],
    }
    path = OUT / "roca_calibration.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    print("legacy", legacy_stats)
    print("calibrated", cal_stats)
    print("chosen", payload["chosen_calibrated_profile"], "fp_reduction", fp_reduction)


if __name__ == "__main__":
    main()
