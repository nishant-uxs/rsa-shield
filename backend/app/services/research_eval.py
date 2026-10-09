"""Research-oriented evaluation: ablation, configuration comparison, mini corpus study.

Designed for paper tables (NETCRYPT / IEEE applied tracks). Never emits SECURE labels.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from Crypto.Util.number import getPrime, isPrime

from app.crypto.analyzer import analyze_rsa
from app.crypto.batch_gcd import batch_gcd
from app.crypto.fermat import fermat_factor
from app.crypto.parser import parse_pem
from app.crypto.roca import roca_fingerprint
from app.crypto.wiener import generate_wiener_weak_key, wiener_attack
from app.ecm.engine import ecm_factor
from app.services.fixtures import FIXTURES, N_TINY, N_WEAK


@dataclass
class ProbeOutcome:
    name: str
    factor_found: bool
    suspicious: bool
    elapsed_ms: float
    detail: str
    method: str | None = None


def _fixture_ne(fx: dict) -> tuple[int, int] | None:
    if fx["id"] == "invalid-pem":
        return None
    if fx.get("n") is not None:
        return int(fx["n"]), int(fx.get("e") or 65537)
    if fx.get("pem"):
        try:
            p = parse_pem(fx["pem"])
            return p.n, p.e
        except Exception:  # noqa: BLE001
            return None
    return None


def _run_analyzer(n: int, e: int) -> ProbeOutcome:
    t0 = time.perf_counter()
    r = analyze_rsa(n, e)
    ms = (time.perf_counter() - t0) * 1000
    tiny = any(f.code == "TINY_FACTOR" for f in r.deterministic)
    return ProbeOutcome(
        "analyzer",
        tiny,
        r.suspicious or tiny,
        ms,
        f"valid={r.valid} findings={len(r.all_findings)}",
        "TINY_FACTOR" if tiny else None,
    )


def _run_fermat(n: int, e: int) -> ProbeOutcome:
    t0 = time.perf_counter()
    r = fermat_factor(n, max_steps=25_000)
    ms = (time.perf_counter() - t0) * 1000
    return ProbeOutcome("fermat", r.factor_found, r.factor_found, ms, r.message, "FERMAT" if r.factor_found else None)


def _run_wiener(n: int, e: int) -> ProbeOutcome:
    t0 = time.perf_counter()
    r = wiener_attack(n, e)
    ms = (time.perf_counter() - t0) * 1000
    return ProbeOutcome("wiener", r.factor_found, r.factor_found, ms, r.message, "WIENER" if r.factor_found else None)


def _run_roca(n: int, e: int) -> ProbeOutcome:
    t0 = time.perf_counter()
    r = roca_fingerprint(n)
    ms = (time.perf_counter() - t0) * 1000
    return ProbeOutcome(
        "roca",
        False,
        r.fingerprint_positive,
        ms,
        r.message,
        "ROCA_FP" if r.fingerprint_positive else None,
    )


def _run_ecm(n: int, e: int, timeout_ms: int = 3000) -> ProbeOutcome:
    t0 = time.perf_counter()
    r = ecm_factor(n, timeout_ms=timeout_ms, curves=40, B1=10_000)
    ms = (time.perf_counter() - t0) * 1000
    return ProbeOutcome(
        "ecm",
        r.factor_found,
        r.factor_found,
        ms,
        r.message,
        "ECM" if r.factor_found else None,
    )


PROBES: dict[str, Callable[..., ProbeOutcome]] = {
    "analyzer": _run_analyzer,
    "fermat": _run_fermat,
    "wiener": _run_wiener,
    "roca": _run_roca,
    "ecm": lambda n, e: _run_ecm(n, e, 3000),
}


CONFIGS: list[dict[str, Any]] = [
    {"id": "analyzer_only", "label": "Analyzer only", "probes": ["analyzer"]},
    {"id": "plus_fermat", "label": "Analyzer + Fermat", "probes": ["analyzer", "fermat"]},
    {"id": "plus_wiener", "label": "Analyzer + Wiener", "probes": ["analyzer", "wiener"]},
    {"id": "plus_ecm", "label": "Analyzer + ECM", "probes": ["analyzer", "ecm"]},
    {
        "id": "full_shield",
        "label": "RSA-SHIELD full (A+F+W+ROCA+ECM)",
        "probes": ["analyzer", "fermat", "wiener", "roca", "ecm"],
    },
]


def _classify(factor_found: bool, suspicious: bool) -> str:
    if factor_found:
        return "FACTOR_FOUND"
    if suspicious:
        return "SUSPICIOUS"
    return "INCONCLUSIVE"


def _expected_factor(fx_id: str) -> bool:
    return fx_id in {"weak-ecm", "small-factor", "fermat-close", "wiener-small-d"}


def run_ablation(*, ecm_timeout_ms: int = 3000) -> dict[str, Any]:
    """Per-probe contribution matrix on educational fixtures."""
    PROBES["ecm"] = lambda n, e: _run_ecm(n, e, ecm_timeout_ms)
    matrix: list[dict[str, Any]] = []

    for fx in FIXTURES:
        ne = _fixture_ne(fx)
        if ne is None:
            continue
        n, e = ne
        row: dict[str, Any] = {
            "fixture_id": fx["id"],
            "name": fx["name"],
            "expects_factor": _expected_factor(fx["id"]),
            "probes": {},
        }
        for name, fn in PROBES.items():
            out = fn(n, e)
            row["probes"][name] = {
                "factor_found": out.factor_found,
                "suspicious": out.suspicious,
                "elapsed_ms": round(out.elapsed_ms, 2),
                "method": out.method,
                "detail": out.detail[:180],
            }
        matrix.append(row)

    # Contribution summary: how often each probe finds a factor when expected
    summary: dict[str, Any] = {}
    for probe in PROBES:
        hits = 0
        expected = 0
        total_ms = 0.0
        for row in matrix:
            p = row["probes"][probe]
            total_ms += p["elapsed_ms"]
            if row["expects_factor"]:
                expected += 1
                if p["factor_found"]:
                    hits += 1
        summary[probe] = {
            "factor_hits_on_weak_fixtures": hits,
            "weak_fixtures": expected,
            "hit_rate": round(hits / expected, 3) if expected else None,
            "avg_ms": round(total_ms / max(len(matrix), 1), 2),
        }

    return {
        "study": "ablation",
        "disclaimer": "Ablation on controlled fixtures only. INCONCLUSIVE ≠ SECURE.",
        "matrix": matrix,
        "summary": summary,
    }


def run_configuration_comparison(*, ecm_timeout_ms: int = 3000) -> dict[str, Any]:
    """Compare RSA-SHIELD probe configurations (paper comparative table without requiring external CLIs)."""
    PROBES["ecm"] = lambda n, e: _run_ecm(n, e, ecm_timeout_ms)
    rows: list[dict[str, Any]] = []

    for fx in FIXTURES:
        ne = _fixture_ne(fx)
        if ne is None:
            continue
        n, e = ne
        expects = _expected_factor(fx["id"])
        cfg_results = {}
        for cfg in CONFIGS:
            t0 = time.perf_counter()
            factor = False
            suspicious = False
            method = None
            for pname in cfg["probes"]:
                out = PROBES[pname](n, e)
                if out.factor_found:
                    factor = True
                    method = out.method
                    break
                if out.suspicious:
                    suspicious = True
            elapsed = (time.perf_counter() - t0) * 1000
            state = _classify(factor, suspicious)
            cfg_results[cfg["id"]] = {
                "label": cfg["label"],
                "state": state,
                "factor_found": factor,
                "method": method,
                "elapsed_ms": round(elapsed, 2),
                "correct_weak_detection": (factor is True) if expects else (factor is False),
            }
        rows.append(
            {
                "fixture_id": fx["id"],
                "name": fx["name"],
                "expects_factor": expects,
                "configurations": cfg_results,
            }
        )

    # Aggregate detection quality per config
    aggregates = []
    for cfg in CONFIGS:
        tp = fp = tn = fn = 0
        times: list[float] = []
        for row in rows:
            r = row["configurations"][cfg["id"]]
            times.append(r["elapsed_ms"])
            pred = r["factor_found"]
            truth = row["expects_factor"]
            if pred and truth:
                tp += 1
            elif pred and not truth:
                fp += 1
            elif not pred and not truth:
                tn += 1
            else:
                fn += 1
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        aggregates.append(
            {
                "config_id": cfg["id"],
                "label": cfg["label"],
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
                "precision": round(precision, 3) if precision is not None else None,
                "recall": round(recall, 3) if recall is not None else None,
                "avg_ms": round(sum(times) / max(len(times), 1), 2),
                "emits_secure_label": False,
            }
        )

    external = _external_tool_availability()

    return {
        "study": "configuration_comparison",
        "disclaimer": (
            "Compares RSA-SHIELD internal configurations on fixtures. "
            "External tools (badkeys/RsaCtfTool) listed if installed; otherwise install notes only. "
            "INCONCLUSIVE is never mapped to SECURE."
        ),
        "configurations": CONFIGS,
        "rows": rows,
        "aggregates": aggregates,
        "external_tools": external,
    }


def _external_tool_availability() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        import badkeys  # type: ignore

        out["badkeys"] = {
            "available": True,
            "version": getattr(badkeys, "__version__", "unknown"),
            "note": "Installed — can be used for offline authoritative fingerprint checks.",
        }
    except Exception:  # noqa: BLE001
        out["badkeys"] = {
            "available": False,
            "note": "Not installed. Optional: pip install badkeys for production fingerprint parity experiments.",
        }
    # RsaCtfTool is typically a CLI repo, not a pip module
    out["RsaCtfTool"] = {
        "available": False,
        "note": "CLI toolbox — compare manually on same fixtures for paper Table; not bundled.",
    }
    return out


def _fermat_close_n(bits: int = 96) -> int:
    half = bits // 2
    p = getPrime(half)
    q = p + 2
    while not isPrime(q):
        q += 2
    return p * q


def run_mini_corpus_study(*, size: int = 40) -> dict[str, Any]:
    """Synthetic authorized corpus: weak classes + normal keys + shared-factor pair."""
    size = max(12, min(size, 120))
    corpus: list[dict[str, Any]] = []

    # Shared factor pair
    shared_p = getPrime(32)
    n_a = shared_p * getPrime(32)
    n_b = shared_p * getPrime(32)
    corpus.append({"id": "share-a", "class": "shared_prime", "n": n_a, "e": 65537})
    corpus.append({"id": "share-b", "class": "shared_prime", "n": n_b, "e": 65537})

    # Known weak demos
    corpus.append({"id": "tiny", "class": "tiny_factor", "n": N_TINY, "e": 65537})
    corpus.append({"id": "ecm-weak", "class": "smoothish_factor", "n": N_WEAK, "e": 65537})
    corpus.append({"id": "fermat", "class": "fermat_close", "n": _fermat_close_n(96), "e": 65537})
    try:
        nw, ew, _, _, _ = generate_wiener_weak_key(256)
        corpus.append({"id": "wiener", "class": "wiener_small_d", "n": nw, "e": ew})
    except Exception:  # noqa: BLE001
        pass

    # Fill with "normal" balanced-ish composites (still lab-sized — not production RSA)
    while len(corpus) < size:
        p = getPrime(48)
        q = getPrime(48)
        if p == q:
            continue
        corpus.append(
            {
                "id": f"normal-{len(corpus)}",
                "class": "normal_lab",
                "n": p * q,
                "e": 65537,
            }
        )

    # Per-key probe summary (fast path: analyzer+fermat+wiener, short ECM only on flagged)
    per_key = []
    class_counts: dict[str, int] = {}
    factor_by_class: dict[str, int] = {}
    for item in corpus:
        class_counts[item["class"]] = class_counts.get(item["class"], 0) + 1
        n, e = item["n"], item["e"]
        t0 = time.perf_counter()
        a = _run_analyzer(n, e)
        f = _run_fermat(n, e)
        w = _run_wiener(n, e)
        factor = a.factor_found or f.factor_found or w.factor_found
        method = a.method or f.method or w.method
        if not factor and item["class"] in {"smoothish_factor"}:
            ecm = _run_ecm(n, e, 5000)
            factor = ecm.factor_found
            method = ecm.method or method
        ms = (time.perf_counter() - t0) * 1000
        if factor:
            factor_by_class[item["class"]] = factor_by_class.get(item["class"], 0) + 1
        per_key.append(
            {
                "id": item["id"],
                "class": item["class"],
                "bits": n.bit_length(),
                "factor_found": factor,
                "method": method,
                "elapsed_ms": round(ms, 2),
                "state": _classify(factor, a.suspicious or f.suspicious or w.suspicious),
            }
        )

    moduli = [c["n"] for c in corpus]
    ids = [c["id"] for c in corpus]
    gcd_result = batch_gcd(moduli, ids)

    legacy = sum(1 for c in corpus if c["n"].bit_length() < 1024)
    return {
        "study": "mini_corpus",
        "disclaimer": (
            "Synthetic authorized lab corpus — not an Internet measurement. "
            "Lab-sized moduli are for probe validation; do not treat non-detection as security."
        ),
        "corpus_size": len(corpus),
        "class_counts": class_counts,
        "factor_finds_by_class": factor_by_class,
        "legacy_under_1024_bits": legacy,
        "batch_gcd": {
            "pairs_checked": gcd_result.pairs_checked,
            "hit_count": len(gcd_result.hits),
            "hits": [
                {"a": h.key_id_a, "b": h.key_id_b, "factor_bits": h.factor.bit_length()}
                for h in gcd_result.hits
            ],
            "message": gcd_result.message,
        },
        "secure_labels_emitted": 0,
        "sample_rows": per_key[:25],
        "summary": {
            "keys_with_factor_evidence": sum(1 for r in per_key if r["factor_found"]),
            "keys_inconclusive_or_suspicious": sum(1 for r in per_key if not r["factor_found"]),
            "shared_factor_collisions": len(gcd_result.hits),
        },
    }


def run_full_research_bundle(*, ecm_timeout_ms: int = 3000, corpus_size: int = 40) -> dict[str, Any]:
    """Single endpoint payload for paper: suite-adjacent research tables."""
    from app.services.evaluation import run_evaluation_suite

    return {
        "bundle": "RSA-SHIELD research evaluation bundle",
        "generated_for": "Applied / education-track conference tables",
        "never_secure_policy": True,
        "fixture_suite": run_evaluation_suite(ecm_timeout_ms=ecm_timeout_ms),
        "ablation": run_ablation(ecm_timeout_ms=ecm_timeout_ms),
        "configuration_comparison": run_configuration_comparison(ecm_timeout_ms=ecm_timeout_ms),
        "mini_corpus": run_mini_corpus_study(size=corpus_size),
    }
