"""Audit orchestration: validate → analyze → ECM → classify → persist fields."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.enums import AuditState, FindingCategory, JobStatus
from app.crypto.analyzer import AnalysisResult, analyze_rsa
from app.crypto.parser import hex_to_int
from app.ecm.engine import EcmResult, ecm_factor


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def classify(
    analysis: AnalysisResult,
    ecm: EcmResult | None,
    *,
    run_ecm: bool,
) -> AuditState:
    if not analysis.valid:
        return AuditState.INVALID_KEY
    if ecm and ecm.factor_found:
        return AuditState.FACTOR_FOUND
    # Tiny factor already in deterministic findings
    if any(f.code == "TINY_FACTOR" for f in analysis.deterministic):
        return AuditState.FACTOR_FOUND
    if analysis.suspicious:
        return AuditState.SUSPICIOUS
    if run_ecm and ecm is not None:
        # Ran ECM, no factor → inconclusive (never "secure")
        return AuditState.INCONCLUSIVE
    return AuditState.NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS


def recommendations_for(state: AuditState) -> list[str]:
    base = [
        "Failure to factor a modulus does NOT prove the key is secure.",
        "Only audit keys you are authorized to analyze.",
    ]
    if state == AuditState.FACTOR_FOUND:
        return [
            "Non-trivial factor evidence indicates the modulus is mathematically weak.",
            "Rotate the affected key/certificate immediately on authorized infrastructure.",
            "Investigate key-generation entropy and device firmware provenance.",
            *base,
        ]
    if state == AuditState.SUSPICIOUS:
        return [
            "Heuristic warnings were raised; review parameter policy and generation practices.",
            "Consider re-keying legacy-sized moduli as part of modernization.",
            *base,
        ]
    if state == AuditState.INCONCLUSIVE:
        return [
            "ECM did not discover a factor within the configured budget.",
            "Increase budget only for authorized lab analysis; do not treat this as a security proof.",
            *base,
        ]
    if state == AuditState.INVALID_KEY:
        return ["Provide a valid RSA public key or modulus/exponent pair.", *base]
    return [
        "Configured deterministic checks did not flag an issue; continue policy-based key management.",
        *base,
    ]


def run_audit_pipeline(
    n_hex: str,
    e: int,
    *,
    run_ecm: bool = True,
    timeout_ms: int | None = None,
    curves: int | None = None,
    b1: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    timeout_ms = timeout_ms or settings.default_ecm_timeout_ms
    curves = curves or settings.default_ecm_curves
    b1 = b1 or settings.default_ecm_b1

    timeline: list[dict[str, Any]] = []
    t0 = _utcnow()
    timeline.append({"at": t0.isoformat(), "event": "AUDIT_STARTED", "detail": "Validation and analysis started"})

    n = hex_to_int(n_hex)
    analysis = analyze_rsa(n, e)
    timeline.append(
        {
            "at": _utcnow().isoformat(),
            "event": "ANALYSIS_COMPLETE",
            "detail": f"Deterministic={len(analysis.deterministic)} Heuristic={len(analysis.heuristics)}",
        }
    )

    ecm: EcmResult | None = None
    if run_ecm and analysis.valid:
        timeline.append({"at": _utcnow().isoformat(), "event": "ECM_STARTED", "detail": f"timeout_ms={timeout_ms} curves={curves}"})
        ecm = ecm_factor(n, timeout_ms=timeout_ms, curves=curves, B1=b1)
        timeline.append(
            {
                "at": _utcnow().isoformat(),
                "event": "ECM_FINISHED",
                "detail": ecm.message,
            }
        )

    # If tiny factor found deterministically, synthesize ECM-like evidence
    factor_hex = None
    cofactor_hex = None
    factor_found = False
    if ecm and ecm.factor_found and ecm.factor is not None:
        factor_found = True
        factor_hex = format(ecm.factor, "x")
        cofactor_hex = format(ecm.cofactor or (n // ecm.factor), "x")
    else:
        for f in analysis.deterministic:
            if f.code == "TINY_FACTOR":
                # extract from detail is fragile; recompute
                for p in range(3, 200, 2):
                    if n % p == 0 and 1 < p < n:
                        factor_found = True
                        factor_hex = format(p, "x")
                        cofactor_hex = format(n // p, "x")
                        break

    state = classify(analysis, ecm, run_ecm=run_ecm)
    if factor_found:
        state = AuditState.FACTOR_FOUND

    findings = []
    for f in analysis.all_findings:
        findings.append(
            {
                "category": f.category.value,
                "code": f.code,
                "severity": f.severity,
                "title": f.title,
                "detail": f.detail,
            }
        )
    if ecm is not None:
        findings.append(
            {
                "category": FindingCategory.ECM_EVIDENCE.value,
                "code": "ECM_RESULT",
                "severity": "critical" if ecm.factor_found else "info",
                "title": "ECM factorization attempt",
                "detail": ecm.message,
            }
        )

    elapsed = None
    if ecm:
        elapsed = ecm.elapsed_ms
    else:
        elapsed = (_utcnow() - t0).total_seconds() * 1000

    timeline.append({"at": _utcnow().isoformat(), "event": "AUDIT_CLASSIFIED", "detail": state.value})

    return {
        "final_state": state.value,
        "factor_found": factor_found,
        "factor_hex": factor_hex,
        "cofactor_hex": cofactor_hex,
        "elapsed_ms": elapsed,
        "findings": findings,
        "warnings": [f for f in findings if f["category"] == FindingCategory.HEURISTIC.value],
        "checks": [f for f in findings if f["category"] == FindingCategory.DETERMINISTIC.value],
        "recommendations": recommendations_for(state),
        "timeline": timeline,
        "ecm": None
        if ecm is None
        else {
            "factor_found": ecm.factor_found,
            "curves_tried": ecm.curves_tried,
            "elapsed_ms": ecm.elapsed_ms,
            "timed_out": ecm.timed_out,
            "message": ecm.message,
            "status": JobStatus.TIMED_OUT.value
            if ecm.timed_out
            else (JobStatus.COMPLETED.value if not ecm.factor_found or ecm.factor_found else JobStatus.COMPLETED.value),
        },
        "ecm_config": {"timeout_ms": timeout_ms, "curves": curves, "b1": b1, "run_ecm": run_ecm},
        "job_status": JobStatus.COMPLETED.value,
    }
