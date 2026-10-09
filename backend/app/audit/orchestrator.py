"""Audit orchestration: validate → analyze → Fermat/Wiener/ROCA → ECM → classify."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.enums import AuditState, FindingCategory, JobStatus
from app.crypto.analyzer import AnalysisResult, analyze_rsa
from app.crypto.fermat import FermatResult, fermat_factor
from app.crypto.parser import hex_to_int
from app.crypto.roca import RocaResult, roca_fingerprint
from app.crypto.wiener import WienerResult, wiener_attack
from app.ecm.engine import EcmResult, ecm_factor


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def classify(
    analysis: AnalysisResult,
    ecm: EcmResult | None,
    *,
    run_ecm: bool,
    factor_found: bool = False,
    roca_positive: bool = False,
) -> AuditState:
    if not analysis.valid:
        return AuditState.INVALID_KEY
    if factor_found or (ecm and ecm.factor_found):
        return AuditState.FACTOR_FOUND
    if any(f.code == "TINY_FACTOR" for f in analysis.deterministic):
        return AuditState.FACTOR_FOUND
    if analysis.suspicious or roca_positive:
        return AuditState.SUSPICIOUS
    if run_ecm and ecm is not None:
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
            "Heuristic warnings were raised (size, ROCA fingerprint, or atypical parameters).",
            "Re-verify fingerprints with authoritative tools (e.g. badkeys / crocs-muni/roca) when flagged.",
            "Consider re-keying legacy-sized moduli as part of modernization.",
            *base,
        ]
    if state == AuditState.INCONCLUSIVE:
        return [
            "Configured probes (ECM / Fermat / Wiener) did not discover a factor within budget.",
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

    findings: list[dict[str, Any]] = []
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

    factor_hex = None
    cofactor_hex = None
    factor_found = False
    factor_method = None

    # Tiny factor from analyzer
    if any(f.code == "TINY_FACTOR" for f in analysis.deterministic):
        for p in range(3, 200, 2):
            if n % p == 0 and 1 < p < n:
                factor_found = True
                factor_hex = format(p, "x")
                cofactor_hex = format(n // p, "x")
                factor_method = "TINY_FACTOR"
                break

    fermat: FermatResult | None = None
    wiener: WienerResult | None = None
    roca: RocaResult | None = None

    if analysis.valid and not factor_found:
        fermat = fermat_factor(n, max_steps=25_000)
        timeline.append({"at": _utcnow().isoformat(), "event": "FERMAT_DONE", "detail": fermat.message})
        findings.append(
            {
                "category": FindingCategory.DETERMINISTIC.value
                if fermat.factor_found
                else FindingCategory.HEURISTIC.value,
                "code": "FERMAT_PROBE",
                "severity": "critical" if fermat.factor_found else "info",
                "title": "Fermat near-prime probe",
                "detail": fermat.message,
            }
        )
        if fermat.factor_found and fermat.factor:
            factor_found = True
            factor_hex = format(fermat.factor, "x")
            cofactor_hex = format(fermat.cofactor or (n // fermat.factor), "x")
            factor_method = "FERMAT"

    if analysis.valid and not factor_found:
        wiener = wiener_attack(n, e)
        timeline.append({"at": _utcnow().isoformat(), "event": "WIENER_DONE", "detail": wiener.message})
        findings.append(
            {
                "category": FindingCategory.DETERMINISTIC.value
                if wiener.factor_found
                else FindingCategory.HEURISTIC.value,
                "code": "WIENER_PROBE",
                "severity": "critical" if wiener.factor_found else "info",
                "title": "Wiener small-d probe",
                "detail": wiener.message,
            }
        )
        if wiener.factor_found and wiener.factor:
            factor_found = True
            factor_hex = format(wiener.factor, "x")
            cofactor_hex = format(wiener.cofactor or (n // wiener.factor), "x")
            factor_method = "WIENER"

    if analysis.valid:
        roca = roca_fingerprint(n)
        timeline.append({"at": _utcnow().isoformat(), "event": "ROCA_FINGERPRINT", "detail": roca.detail})
        findings.append(
            {
                "category": FindingCategory.HEURISTIC.value,
                "code": "ROCA_FINGERPRINT",
                "severity": "warning" if roca.fingerprint_positive else "info",
                "title": "ROCA fingerprint probe",
                "detail": f"{roca.message} ({roca.detail})",
            }
        )
        if roca.fingerprint_positive:
            analysis.suspicious = True

    ecm: EcmResult | None = None
    if run_ecm and analysis.valid and not factor_found:
        timeline.append(
            {"at": _utcnow().isoformat(), "event": "ECM_STARTED", "detail": f"timeout_ms={timeout_ms} curves={curves}"}
        )
        ecm = ecm_factor(n, timeout_ms=timeout_ms, curves=curves, B1=b1)
        timeline.append({"at": _utcnow().isoformat(), "event": "ECM_FINISHED", "detail": ecm.message})
        findings.append(
            {
                "category": FindingCategory.ECM_EVIDENCE.value,
                "code": "ECM_RESULT",
                "severity": "critical" if ecm.factor_found else "info",
                "title": "ECM factorization attempt",
                "detail": ecm.message,
            }
        )
        if ecm.factor_found and ecm.factor is not None:
            factor_found = True
            factor_hex = format(ecm.factor, "x")
            cofactor_hex = format(ecm.cofactor or (n // ecm.factor), "x")
            factor_method = "ECM"

    roca_positive = bool(roca and roca.fingerprint_positive)
    state = classify(
        analysis,
        ecm,
        run_ecm=run_ecm,
        factor_found=factor_found,
        roca_positive=roca_positive,
    )
    if factor_found:
        state = AuditState.FACTOR_FOUND

    elapsed = (_utcnow() - t0).total_seconds() * 1000
    if ecm:
        elapsed = max(elapsed, ecm.elapsed_ms)

    timeline.append({"at": _utcnow().isoformat(), "event": "AUDIT_CLASSIFIED", "detail": state.value})

    return {
        "final_state": state.value,
        "factor_found": factor_found,
        "factor_hex": factor_hex,
        "cofactor_hex": cofactor_hex,
        "factor_method": factor_method,
        "elapsed_ms": elapsed,
        "findings": findings,
        "warnings": [f for f in findings if f["category"] == FindingCategory.HEURISTIC.value],
        "checks": [f for f in findings if f["category"] == FindingCategory.DETERMINISTIC.value],
        "recommendations": recommendations_for(state),
        "timeline": timeline,
        "probes": {
            "fermat": None
            if fermat is None
            else {"factor_found": fermat.factor_found, "steps": fermat.steps, "message": fermat.message},
            "wiener": None
            if wiener is None
            else {
                "factor_found": wiener.factor_found,
                "convergents_tried": wiener.convergents_tried,
                "message": wiener.message,
            },
            "roca": None
            if roca is None
            else {
                "fingerprint_positive": roca.fingerprint_positive,
                "score": roca.score,
                "detail": roca.detail,
                "message": roca.message,
            },
        },
        "ecm": None
        if ecm is None
        else {
            "factor_found": ecm.factor_found,
            "curves_tried": ecm.curves_tried,
            "elapsed_ms": ecm.elapsed_ms,
            "timed_out": ecm.timed_out,
            "message": ecm.message,
            "status": JobStatus.TIMED_OUT.value if ecm.timed_out else JobStatus.COMPLETED.value,
        },
        "ecm_config": {"timeout_ms": timeout_ms, "curves": curves, "b1": b1, "run_ecm": run_ecm},
        "job_status": JobStatus.COMPLETED.value,
    }
