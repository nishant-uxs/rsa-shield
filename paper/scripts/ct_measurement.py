"""Public Certificate Transparency sample measurement for RSA-SHIELD.

Fetches certificates from a *public* CT log API (RFC 6962), extracts RSA
moduli, runs batch-GCD + lightweight evidence-tiered probes (analyzer/ROCA).

This is authorized public-data research (same class as Heninger et al.), NOT
unauthorized host scanning. Results are written to paper/data/ct_measurement.json.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from cryptography import x509  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

from app.crypto.analyzer import analyze_rsa  # noqa: E402
from app.crypto.batch_gcd import batch_gcd  # noqa: E402
from app.crypto.roca import roca_fingerprint  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
DEFAULT_LOG = "https://ct.googleapis.com/logs/us1/argon2026h2/"
DEFAULT_LOGS = [
    "https://ct.googleapis.com/logs/us1/argon2026h2/",
    "https://ct.googleapis.com/logs/eu1/xenon2026h2/",
    "https://ct.cloudflare.com/logs/nimbus2026/",
]
UA = "RSA-SHIELD-CT-Research/1.0 (academic; contact=anonymous-review)"


def _get_json(url: str, timeout: float = 60.0, retries: int = 4) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.5 * (2**attempt))
    assert last is not None
    raise last


def _read_u24(buf: bytes, off: int) -> tuple[int, int]:
    return int.from_bytes(buf[off : off + 3], "big"), off + 3


def extract_der_from_leaf_input(leaf_b64: str) -> bytes | None:
    """Parse RFC 6962 MerkleTreeLeaf → X.509 DER (or None for unsupported)."""
    raw = base64.b64decode(leaf_b64)
    if len(raw) < 15:
        return None
    # Version (1) + MerkleLeafType (1) + timestamp (8) + LogEntryType (2)
    entry_type = int.from_bytes(raw[10:12], "big")
    off = 12
    if entry_type == 0:  # x509_entry
        length, off = _read_u24(raw, off)
        der = raw[off : off + length]
        return der if len(der) == length else None
    if entry_type == 1:  # precert_entry: issuer_key_hash(32) + TBSCertificate
        if len(raw) < off + 32 + 3:
            return None
        off += 32
        length, off = _read_u24(raw, off)
        # Precert TBS is not always loadable as full cert; skip for modulus extract
        return None
    return None


def rsa_from_der(der: bytes) -> tuple[int, int, int] | None:
    try:
        cert = x509.load_der_x509_certificate(der)
        pub = cert.public_key()
        if not isinstance(pub, rsa.RSAPublicKey):
            return None
        numbers = pub.public_numbers()
        return numbers.n, numbers.e, pub.key_size
    except Exception:  # noqa: BLE001
        return None


def collect_moduli(
    *,
    log_url: str,
    target_unique: int,
    page_size: int = 32,
    max_pages: int = 20000,
    start_index: int | None = None,
) -> dict[str, Any]:
    base = log_url.rstrip("/") + "/"
    sth = _get_json(base + "ct/v1/get-sth")
    tree_size = int(sth["tree_size"])
    # Sample near the recent end for a contemporary slice
    if start_index is None:
        start_index = max(0, tree_size - page_size * max_pages)
    start_index = min(start_index, max(0, tree_size - 1))

    unique: dict[int, dict[str, Any]] = {}
    pages = 0
    entries_seen = 0
    rsa_seen = 0
    parse_fail = 0
    non_rsa = 0
    t0 = time.perf_counter()
    idx = start_index

    while len(unique) < target_unique and pages < max_pages and idx < tree_size:
        end = min(idx + page_size - 1, tree_size - 1)
        url = f"{base}ct/v1/get-entries?start={idx}&end={end}"
        try:
            payload = _get_json(url)
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 503}:
                time.sleep(2.0)
                continue
            raise
        entries = payload.get("entries") or []
        if not entries:
            break
        for ent in entries:
            entries_seen += 1
            der = extract_der_from_leaf_input(ent["leaf_input"])
            if der is None:
                # x509_entry / precert_entry: first ASN.1Cert in extra_data
                try:
                    extra = base64.b64decode(ent.get("extra_data") or "")
                    if len(extra) >= 3:
                        ln = int.from_bytes(extra[0:3], "big")
                        der = extra[3 : 3 + ln] if len(extra) >= 3 + ln else None
                except Exception:  # noqa: BLE001
                    der = None
            if not der:
                parse_fail += 1
                continue
            parsed = rsa_from_der(der)
            if parsed is None:
                non_rsa += 1
                continue
            n, e, bits = parsed
            rsa_seen += 1
            if n not in unique:
                unique[n] = {"e": e, "bits": bits, "first_index": idx, "log_url": base}
        pages += 1
        idx = end + 1
        if pages % 50 == 0:
            print(
                f"  pages={pages} unique_rsa={len(unique)} entries={entries_seen} "
                f"rsa_certs={rsa_seen}",
                flush=True,
            )
        time.sleep(0.05)  # be polite to the public log

    elapsed = time.perf_counter() - t0
    return {
        "log_url": base,
        "tree_size": tree_size,
        "start_index": start_index,
        "end_index_exclusive": idx,
        "pages_fetched": pages,
        "entries_seen": entries_seen,
        "rsa_certs_seen": rsa_seen,
        "non_rsa_or_unparsed_pubkey": non_rsa,
        "leaf_parse_fail": parse_fail,
        "unique_moduli": len(unique),
        "collect_seconds": round(elapsed, 2),
        "moduli": unique,
    }


def run_measurement(
    *,
    target_unique: int = 5000,
    log_url: str = DEFAULT_LOG,
    log_urls: list[str] | None = None,
    probe_limit: int = 500,
) -> dict[str, Any]:
    logs = log_urls or [log_url]
    per_log_target = max(100, (target_unique + len(logs) - 1) // len(logs))
    print(
        f"Multi-log CT collect: {len(logs)} logs, target_total={target_unique} "
        f"(~{per_log_target}/log)",
        flush=True,
    )

    moduli_map: dict[int, dict[str, Any]] = {}
    per_log_stats: list[dict[str, Any]] = []
    for url in logs:
        need = max(0, target_unique - len(moduli_map))
        if need <= 0:
            break
        take = min(per_log_target, need)
        print(f"Collecting up to {take} unique RSA moduli from {url}", flush=True)
        coll = collect_moduli(log_url=url, target_unique=take)
        part = coll.pop("moduli")
        before = len(moduli_map)
        for n, meta in part.items():
            if n not in moduli_map:
                moduli_map[n] = meta
        coll["unique_added"] = len(moduli_map) - before
        coll["unique_after_merge"] = len(moduli_map)
        per_log_stats.append(coll)
        print(
            f"  log done: fetched_unique={coll['unique_moduli']} "
            f"added={coll['unique_added']} total={len(moduli_map)}",
            flush=True,
        )

    moduli = list(moduli_map.keys())
    print(f"Collected {len(moduli)} unique moduli across logs; running batch-GCD...", flush=True)
    coll = {
        "mode": "multi_log_tip_sample",
        "logs": logs,
        "per_log": per_log_stats,
        "unique_moduli": len(moduli),
        "collect_seconds": round(sum(x.get("collect_seconds", 0) for x in per_log_stats), 2),
        "entries_seen": sum(x.get("entries_seen", 0) for x in per_log_stats),
        "rsa_certs_seen": sum(x.get("rsa_certs_seen", 0) for x in per_log_stats),
    }

    # Chunked batch-GCD: a single product tree over thousands of 2048-bit
    # moduli is infeasible in lab memory; we scan windows of `chunk_size`,
    # then reshuffle once to catch some cross-window collisions.
    import random as _random

    chunk_size = 250
    t0 = time.perf_counter()
    all_hits = []
    seen_pairs: set[tuple[str, str]] = set()

    def _run_chunks(order: list[int], tag: str) -> None:
        for start in range(0, len(order), chunk_size):
            idxs = order[start : start + chunk_size]
            chunk = [moduli[i] for i in idxs]
            ids = [str(i) for i in idxs]
            if len(chunk) < 2:
                continue
            part = batch_gcd(chunk, key_ids=ids, method="subquadratic")
            for h in part.hits:
                pair = tuple(sorted((h.key_id_a, h.key_id_b)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                all_hits.append(h)
            print(
                f"  batch-GCD[{tag}] {start}:{start+len(chunk)} hits_chunk={len(part.hits)} "
                f"ms={part.elapsed_ms}",
                flush=True,
            )

    order1 = list(range(len(moduli)))
    _run_chunks(order1, "pass1")
    order2 = list(range(len(moduli)))
    _random.Random(0xC7).shuffle(order2)
    _run_chunks(order2, "pass2-shuffle")
    gcd_ms = (time.perf_counter() - t0) * 1000

    class _G:  # lightweight adapter for downstream JSON
        pass

    gcd_res = _G()
    gcd_res.hits = all_hits
    gcd_res.message = (
        f"Chunked batch-GCD (chunk_size={chunk_size}, 2 passes) over {len(moduli)} unique CT moduli: "
        f"{len(all_hits)} unique hit(s) in {gcd_ms:.2f} ms. "
        "Chunking may miss some cross-window shares; absence of hits is not a security proof."
    )

    # Evidence-tiered lightweight probes on a stratified sample (not full ECM)
    bit_hist = Counter(v["bits"] for v in moduli_map.values())
    ordered = sorted(moduli_map.items(), key=lambda kv: (kv[1]["bits"], kv[0]))
    sample: list[tuple[int, dict[str, Any]]] = []
    seen: set[int] = set()
    # Prefer undersized moduli first (legacy / weak size)
    for n, meta in ordered:
        if meta["bits"] < 2048 and n not in seen:
            sample.append((n, meta))
            seen.add(n)
        if len(sample) >= probe_limit:
            break
    if len(sample) < probe_limit and ordered:
        stride = max(1, len(ordered) // max(1, probe_limit - len(sample)))
        for n, meta in ordered[::stride]:
            if n not in seen:
                sample.append((n, meta))
                seen.add(n)
            if len(sample) >= probe_limit:
                break

    tier_counts: Counter[str] = Counter()
    small_moduli = 0
    roca_hits = 0
    tiny_factors = 0
    invalid = 0
    probe_rows = []
    for n, meta in sample[:probe_limit]:
        e = int(meta["e"])
        analysis = analyze_rsa(n, e)
        roca = roca_fingerprint(n)
        factor = any(f.code == "TINY_FACTOR" for f in analysis.deterministic)
        if not analysis.valid:
            tier = "INVALID_KEY"
            invalid += 1
        elif factor:
            tier = "FACTOR_FOUND"
            tiny_factors += 1
        elif analysis.suspicious or roca.fingerprint_positive:
            tier = "SUSPICIOUS"
        else:
            # Active ECM not run at Internet sample scale under lab budget
            tier = "NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS"
        if meta["bits"] < 2048:
            small_moduli += 1
        if roca.fingerprint_positive:
            roca_hits += 1
        tier_counts[tier] += 1
        probe_rows.append(
            {
                "bits": meta["bits"],
                "tier": tier,
                "roca": bool(roca.fingerprint_positive),
                "tiny_factor": factor,
            }
        )

    # Never-SECURE invariant
    secure_labels = sum(1 for r in probe_rows if r["tier"] == "SECURE")

    result = {
        "study": "public_ct_rsa_measurement",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "Public multi-log CT tip sample only. Not a full Internet census. "
            "NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS != SECURE. "
            "ECM not run on the full CT sample under lab budgets. "
            "Chunked batch-GCD may miss cross-window shares."
        ),
        "collection": coll,
        "unique_moduli": len(moduli),
        "log_count": len(logs),
        "bitlength_histogram": {str(k): v for k, v in sorted(bit_hist.items())},
        "batch_gcd": {
            "method": "subquadratic_chunked",
            "elapsed_ms": round(gcd_ms, 2),
            "hit_count": len(gcd_res.hits),
            "hits_sample": [
                {
                    "a": h.key_id_a,
                    "b": h.key_id_b,
                    "factor_bits": int(h.factor).bit_length(),
                }
                for h in gcd_res.hits[:20]
            ],
            "message": gcd_res.message,
        },
        "evidence_probe_sample": {
            "sample_size": len(probe_rows),
            "tier_counts": dict(tier_counts),
            "small_moduli_under_2048": small_moduli,
            "roca_fingerprint_hits": roca_hits,
            "tiny_factor_hits": tiny_factors,
            "invalid_keys": invalid,
            "secure_labels_emitted": secure_labels,
        },
        "novelty_claim_safe": (
            "Multi-log public-CT tip sample under evidence-tiered auditor; "
            "does not claim a new factorization algorithm or billion-cert census."
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Public CT RSA measurement for RSA-SHIELD")
    parser.add_argument("--target", type=int, default=12000, help="Unique RSA moduli target")
    parser.add_argument("--probe-limit", type=int, default=800, help="Evidence probe sample size")
    parser.add_argument("--log-url", type=str, default=DEFAULT_LOG, help="Single-log mode URL")
    parser.add_argument(
        "--multi-log",
        action="store_true",
        default=True,
        help="Fetch from DEFAULT_LOGS (Argon/Xenon/Nimbus)",
    )
    parser.add_argument("--single-log", action="store_true", help="Disable multi-log mode")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    use_multi = args.multi_log and not args.single_log
    result = run_measurement(
        target_unique=args.target,
        log_url=args.log_url,
        log_urls=DEFAULT_LOGS if use_multi else None,
        probe_limit=args.probe_limit,
    )
    # Drop raw moduli from saved JSON (keep summary only — moduli are large)
    path = OUT / "ct_measurement.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    print("unique", result["unique_moduli"])
    print("batch_gcd hits", result["batch_gcd"]["hit_count"], "ms", result["batch_gcd"]["elapsed_ms"])
    print("tiers", result["evidence_probe_sample"]["tier_counts"])
    print("secure_labels", result["evidence_probe_sample"]["secure_labels_emitted"])


if __name__ == "__main__":
    main()
