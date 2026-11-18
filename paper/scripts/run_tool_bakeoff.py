"""Epistemic bake-off: RSA-SHIELD vs optional badkeys / RsaCtfTool on RSA-Auditor Bench.

Defensive evaluation only. RsaCtfTool is probed for availability; offensive unbounded
attack modes are not executed. badkeys is a fingerprint scanner (optional dependency).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.evaluation import run_evaluation_suite  # noqa: E402
from app.services.fixtures import FIXTURES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
BENCH = Path(__file__).resolve().parents[1] / "benchmark" / "manifest.json"
ECM_TIMEOUT_MS = 2500


def _load_manifest() -> dict[str, Any]:
    if BENCH.exists():
        return json.loads(BENCH.read_text(encoding="utf-8"))
    # Fallback labels from fixtures
    return {
        "version": "fixtures-inline",
        "fixtures": [
            {
                "id": fx["id"],
                "expects_factor": bool(fx.get("expects_factor")),
                "expected_tier": fx.get("expected_tier"),
            }
            for fx in FIXTURES
        ],
    }


def _shield_rows(suite: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for r in suite["rows"]:
        state = r["final_state"]
        factor = bool(r.get("factor_found"))
        # Never-SECURE policy: only explicit SECURE would count; shield never emits it.
        pass_like = state in {"SECURE", "PASS", "OK", "SAFE"}
        rows.append(
            {
                "tool": "rsa_shield_full",
                "fixture_id": r["fixture_id"],
                "available": True,
                "recovered_factor": factor,
                "factor_method": r.get("factor_method"),
                "label_or_state": state,
                "emitted_secure_or_pass_like": pass_like,
                "elapsed_ms": r.get("elapsed_ms"),
                "detail": None,
            }
        )
    return rows


def _run_badkeys() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    meta: dict[str, Any] = {"available": False}
    rows: list[dict[str, Any]] = []
    try:
        import badkeys  # type: ignore
    except Exception as exc:  # noqa: BLE001
        meta = {
            "available": False,
            "note": f"Not installed ({exc}). Optional: pip install badkeys && badkeys --update-bl",
        }
        for fx in FIXTURES:
            rows.append(
                {
                    "tool": "badkeys",
                    "fixture_id": fx["id"],
                    "available": False,
                    "recovered_factor": False,
                    "factor_method": None,
                    "label_or_state": "NOT_INSTALLED",
                    "emitted_secure_or_pass_like": False,
                    "elapsed_ms": None,
                    "detail": meta["note"],
                }
            )
        return rows, meta

    meta = {
        "available": True,
        "version": getattr(badkeys, "__version__", "unknown"),
        "note": "Fingerprint/blocklist scanner; empty findings often treated as OK by operators.",
    }

    for fx in FIXTURES:
        fid = fx["id"]
        if fid == "invalid-pem":
            t0 = time.perf_counter()
            try:
                out = badkeys.checkpubkey(fx["pem"])
                detail = str(out)
                findings = out if isinstance(out, dict) else {}
            except Exception as exc:  # noqa: BLE001
                detail = f"error:{exc}"
                findings = {"parse_error": True}
            ms = round((time.perf_counter() - t0) * 1000, 2)
            # Parse failure is not a pass-like "secure" claim.
            rows.append(
                {
                    "tool": "badkeys",
                    "fixture_id": fid,
                    "available": True,
                    "recovered_factor": False,
                    "factor_method": None,
                    "label_or_state": "ERROR" if "error:" in detail else ("FINDINGS" if findings else "EMPTY"),
                    "emitted_secure_or_pass_like": False,
                    "elapsed_ms": ms,
                    "detail": detail[:500],
                }
            )
            continue

        n = int(fx["n"]) if fx.get("n") is not None else None
        e = int(fx["e"] or 65537)
        t0 = time.perf_counter()
        try:
            findings = badkeys.checkrsa(n, e) if n is not None else {}
            detail = json.dumps(findings, default=str)
        except Exception as exc:  # noqa: BLE001
            findings = {}
            detail = f"error:{exc}"
        ms = round((time.perf_counter() - t0) * 1000, 2)

        # Treat factorization-like or structural hits as "recovered_factor"/vuln evidence.
        factorish_keys = {"smallfactors", "fermat", "smalld", "roca", "pattern", "blocksize"}
        hit_keys = set(findings.keys()) if isinstance(findings, dict) else set()
        recovered = bool(hit_keys & factorish_keys) or bool(findings)
        # Empty findings ⇒ operators commonly read as pass/OK (epistemic overconfidence risk).
        pass_like = (not findings) and ("error:" not in detail)

        rows.append(
            {
                "tool": "badkeys",
                "fixture_id": fid,
                "available": True,
                "recovered_factor": recovered,
                "factor_method": ",".join(sorted(hit_keys)) if hit_keys else None,
                "label_or_state": "FINDINGS" if findings else "EMPTY_OK_LIKE",
                "emitted_secure_or_pass_like": pass_like,
                "elapsed_ms": ms,
                "detail": detail[:500],
            }
        )
    return rows, meta


def _run_rsactftool_availability() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Availability-only probe. Do not execute offensive CTF attack pipelines."""
    exe = shutil.which("RsaCtfTool") or shutil.which("rsactftool")
    available = exe is not None
    meta = {
        "available": available,
        "path": exe,
        "note": (
            "CLI present but offensive/unbounded public-key attack modes are out of scope "
            "for this defensive epistemic bake-off; recorded as availability-only."
            if available
            else "Not installed. Availability-only in bake-off (no offensive CTF execution)."
        ),
    }
    rows = []
    for fx in FIXTURES:
        rows.append(
            {
                "tool": "RsaCtfTool",
                "fixture_id": fx["id"],
                "available": available,
                "recovered_factor": False,
                "factor_method": None,
                "label_or_state": "AVAILABILITY_ONLY" if available else "NOT_INSTALLED",
                "emitted_secure_or_pass_like": False,
                "elapsed_ms": None,
                "detail": meta["note"],
            }
        )
    return rows, meta


def _aggregates(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    expects = {f["id"]: bool(f.get("expects_factor")) for f in manifest["fixtures"]}
    # Also map from FIXTURES for invalid etc.
    for fx in FIXTURES:
        expects.setdefault(fx["id"], bool(fx.get("expects_factor")))

    tools = sorted({r["tool"] for r in rows})
    out = []
    for tool in tools:
        trows = [r for r in rows if r["tool"] == tool]
        if not trows or not trows[0].get("available"):
            out.append(
                {
                    "tool": tool,
                    "available": False,
                    "tp": None,
                    "fp": None,
                    "fn": None,
                    "tn": None,
                    "factor_recall": None,
                    "false_factor_rate": None,
                    "overconfidence_rate": None,
                    "overconfidence_numerator": None,
                    "overconfidence_denominator": None,
                    "never_emits_secure_by_policy": tool == "rsa_shield_full",
                }
            )
            continue

        # Skip invalid-pem from factor P/R; still include in overconfidence denom if non-factor.
        tp = fp = tn = fn = 0
        non_factor_cases = 0
        overconf = 0
        for r in trows:
            fid = r["fixture_id"]
            if fid == "invalid-pem":
                # Not a factor-class fixture.
                if not r["recovered_factor"]:
                    non_factor_cases += 1
                    if r["emitted_secure_or_pass_like"]:
                        overconf += 1
                continue
            truth = expects.get(fid, False)
            pred = bool(r["recovered_factor"])
            if pred and truth:
                tp += 1
            elif pred and not truth:
                fp += 1
            elif not pred and not truth:
                tn += 1
            else:
                fn += 1
            if not pred:
                non_factor_cases += 1
                if r["emitted_secure_or_pass_like"]:
                    overconf += 1

        recall = tp / (tp + fn) if (tp + fn) else None
        fpr = fp / (fp + tn) if (fp + tn) else None
        oc = overconf / non_factor_cases if non_factor_cases else 0.0
        out.append(
            {
                "tool": tool,
                "available": True,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "factor_recall": round(recall, 3) if recall is not None else None,
                "false_factor_rate": round(fpr, 3) if fpr is not None else None,
                "overconfidence_rate": round(oc, 3),
                "overconfidence_numerator": overconf,
                "overconfidence_denominator": non_factor_cases,
                "never_emits_secure_by_policy": tool == "rsa_shield_full",
            }
        )
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()
    suite = run_evaluation_suite(ecm_timeout_ms=ECM_TIMEOUT_MS)
    rows: list[dict[str, Any]] = []
    rows.extend(_shield_rows(suite))
    bad_rows, bad_meta = _run_badkeys()
    rows.extend(bad_rows)
    rsa_rows, rsa_meta = _run_rsactftool_availability()
    rows.extend(rsa_rows)

    payload = {
        "study": "epistemic_tool_bakeoff",
        "bench_version": manifest.get("version", "unknown"),
        "ecm_timeout_ms": ECM_TIMEOUT_MS,
        "disclaimer": (
            "Compares factor recovery and pass/secure-like overconfidence on RSA-Auditor Bench. "
            "RSA-SHIELD never emits SECURE. badkeys empty findings counted as OK-like. "
            "RsaCtfTool is availability-only (no offensive CTF execution)."
        ),
        "tools": {
            "rsa_shield_full": {"available": True, "note": "Full budgeted multi-probe pipeline."},
            "badkeys": bad_meta,
            "RsaCtfTool": rsa_meta,
        },
        "rows": rows,
        "aggregates": _aggregates(rows, manifest),
    }
    path = OUT / "bakeoff.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"wrote {path}")
    for a in payload["aggregates"]:
        print(a)


if __name__ == "__main__":
    main()
