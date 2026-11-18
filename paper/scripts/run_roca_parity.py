"""ROCA fingerprint parity: educational RSA-SHIELD heuristic vs badkeys.

Compares positive/negative calls on:
  1) RSA-Auditor Bench fixtures
  2) A fresh public CT tip sample (optional; public RFC 6962 only)

Reports both legacy and calibrated educational profiles against badkeys' roca
finding (reference fingerprint only; not Infineon ground truth).
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

from app.crypto.roca import ROCA_PROFILES, roca_fingerprint  # noqa: E402
from app.services.fixtures import FIXTURES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
CT_LOG = "https://ct.googleapis.com/logs/us1/argon2026h2/"


def _badkeys_roca(n: int, e: int) -> tuple[bool, str]:
    try:
        import badkeys  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return False, f"not_installed:{exc}"
    try:
        findings = badkeys.checkrsa(n, e) or {}
        hit = "roca" in findings
        return hit, json.dumps(findings, default=str)[:400]
    except Exception as exc:  # noqa: BLE001
        return False, f"error:{exc}"


def _score_pair(edu: bool, auth: bool) -> str:
    if edu and auth:
        return "TP_both"
    if edu and not auth:
        return "FP_edu_only"
    if (not edu) and auth:
        return "FN_edu_miss"
    return "TN_both"


def _row(source: str, rid: str, n: int, e: int, bits: int | None = None) -> dict[str, Any]:
    legacy = roca_fingerprint(n, profile="legacy")
    cal = roca_fingerprint(n, profile="calibrated")
    auth_hit, auth_detail = _badkeys_roca(n, e)
    return {
        "source": source,
        "id": rid,
        "bits": bits if bits is not None else n.bit_length(),
        "legacy_positive": bool(legacy.fingerprint_positive),
        "calibrated_positive": bool(cal.fingerprint_positive),
        "edu_positive": bool(cal.fingerprint_positive),  # default = calibrated
        "edu_score": cal.score,
        "legacy_score": legacy.score,
        "badkeys_roca": auth_hit,
        "agreement_legacy": _score_pair(bool(legacy.fingerprint_positive), auth_hit),
        "agreement_calibrated": _score_pair(bool(cal.fingerprint_positive), auth_hit),
        "agreement": _score_pair(bool(cal.fingerprint_positive), auth_hit),
        "edu_detail": cal.detail,
        "legacy_detail": legacy.detail,
        "badkeys_detail": auth_detail[:200] if source == "ct_tip" else auth_detail,
    }


def _fixture_rows() -> list[dict[str, Any]]:
    rows = []
    for fx in FIXTURES:
        if fx["id"] == "invalid-pem" or fx.get("n") is None:
            continue
        n = int(fx["n"])
        e = int(fx.get("e") or 65537)
        rows.append(_row("bench", fx["id"], n, e))
    return rows


def _fetch_ct_moduli(limit: int = 400) -> list[tuple[int, int, int]]:
    """Reuse CT leaf parsing from ct_measurement without importing heavy path issues."""
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
    req = urllib.request.Request(base + "ct/v1/get-sth", headers={"User-Agent": "RSA-SHIELD-ROCA-Parity/1.0"})
    sth = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    tree_size = int(sth["tree_size"])
    idx = max(0, tree_size - 40_000)
    out: list[tuple[int, int, int]] = []
    seen: set[int] = set()
    pages = 0
    while len(out) < limit and pages < 2500 and idx < tree_size:
        end = min(idx + 31, tree_size - 1)
        url = f"{base}ct/v1/get-entries?start={idx}&end={end}"
        req = urllib.request.Request(url, headers={"User-Agent": "RSA-SHIELD-ROCA-Parity/1.0"})
        try:
            payload = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
        except Exception:  # noqa: BLE001
            time.sleep(1.0)
            pages += 1
            idx = end + 1
            continue
        for ent in payload.get("entries") or []:
            der = der_from_leaf(ent["leaf_input"])
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
    return out


def _ct_rows(limit: int = 400) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    meta = {"attempted": True, "limit": limit}
    try:
        moduli = _fetch_ct_moduli(limit=limit)
    except Exception as exc:  # noqa: BLE001
        meta["error"] = str(exc)
        return [], meta
    meta["fetched"] = len(moduli)
    rows = [_row("ct_tip", f"ct-{i}", n, e, bits) for i, (n, e, bits) in enumerate(moduli)]
    return rows, meta


def _aggregate(rows: list[dict[str, Any]], *, positive_key: str, agreement_key: str) -> dict[str, Any]:
    counts = {"TP_both": 0, "FP_edu_only": 0, "FN_edu_miss": 0, "TN_both": 0}
    for r in rows:
        counts[r[agreement_key]] = counts.get(r[agreement_key], 0) + 1
    n = max(len(rows), 1)
    edu_pos = sum(1 for r in rows if r[positive_key])
    auth_pos = sum(1 for r in rows if r["badkeys_roca"])
    return {
        "n": len(rows),
        "counts": counts,
        "edu_positive_rate": round(edu_pos / n, 4),
        "badkeys_roca_rate": round(auth_pos / n, 4),
        "edu_false_positive_rate_vs_badkeys": round(counts["FP_edu_only"] / n, 4),
        "agreement_rate": round((counts["TP_both"] + counts["TN_both"]) / n, 4),
    }


def _bundle(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": rows,
        "aggregate_legacy": _aggregate(rows, positive_key="legacy_positive", agreement_key="agreement_legacy"),
        "aggregate_calibrated": _aggregate(
            rows, positive_key="calibrated_positive", agreement_key="agreement_calibrated"
        ),
        # Default aggregate = calibrated (shipped profile)
        "aggregate": _aggregate(rows, positive_key="calibrated_positive", agreement_key="agreement_calibrated"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    bench_rows = _fixture_rows()
    ct_rows, ct_meta = _ct_rows(limit=400)
    all_rows = bench_rows + ct_rows
    payload = {
        "study": "roca_fingerprint_parity",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "badkeys ROCA finding used as reference fingerprint only. "
            "Neither tool proves Coppersmith factorization. "
            "Legacy educational profile over-triggers; calibrated is the shipped default."
        ),
        "elapsed_s": round(time.perf_counter() - t0, 2),
        "profiles": ROCA_PROFILES,
        "badkeys_available": not any(
            str(r.get("badkeys_detail", "")).startswith("not_installed") for r in bench_rows
        ),
        "bench": _bundle(bench_rows),
        "ct_tip": {"meta": ct_meta, **(_bundle(ct_rows) if ct_rows else {"aggregate": None})},
        "combined": _bundle(all_rows) if all_rows else {"aggregate": None},
    }
    path = OUT / "roca_parity.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    print("bench legacy", payload["bench"]["aggregate_legacy"])
    print("bench calibrated", payload["bench"]["aggregate_calibrated"])
    print("ct legacy", (payload["ct_tip"].get("aggregate_legacy")))
    print("ct calibrated", (payload["ct_tip"].get("aggregate_calibrated")))


if __name__ == "__main__":
    main()
