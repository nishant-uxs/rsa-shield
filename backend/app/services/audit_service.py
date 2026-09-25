from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.orchestrator import run_audit_pipeline
from app.core.enums import AuditState, JobStatus
from app.crypto.parser import ParseError, n_to_hex, parse_modulus_exponent, parse_pem
from app.database.models import Audit, AuditFinding, EcmRun, Report, RsaKey, User


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _modulus_preview(hex_n: str) -> str:
    if len(hex_n) <= 24:
        return hex_n
    return f"{hex_n[:10]}…{hex_n[-10:]}"


async def ensure_demo_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == "auditor"))
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(username="auditor", display_name="Team Aegis Auditor")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_key_from_pem(db: AsyncSession, pem: str, label: str = "", source: str = "upload") -> RsaKey:
    parsed = parse_pem(pem)
    return await _persist_key(db, parsed.n, parsed.e, parsed.bit_length, parsed.fingerprint, label, source)


async def create_key_from_raw(db: AsyncSession, n: str, e: int, label: str = "", source: str = "manual") -> RsaKey:
    parsed = parse_modulus_exponent(n, e)
    return await _persist_key(db, parsed.n, parsed.e, parsed.bit_length, parsed.fingerprint, label, source)


async def _persist_key(
    db: AsyncSession, n: int, e: int, bit_length: int, fingerprint: str, label: str, source: str
) -> RsaKey:
    existing = await db.execute(select(RsaKey).where(RsaKey.fingerprint == fingerprint))
    found = existing.scalar_one_or_none()
    if found:
        return found
    key = RsaKey(
        key_id=_uid("key"),
        label=label or f"RSA-{bit_length}",
        source=source,
        algorithm="RSA",
        modulus_hex=n_to_hex(n),
        exponent=e,
        bit_length=bit_length,
        fingerprint=fingerprint,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return key


def key_to_dict(key: RsaKey) -> dict[str, Any]:
    return {
        "id": key.id,
        "key_id": key.key_id,
        "label": key.label,
        "source": key.source,
        "algorithm": key.algorithm,
        "bit_length": key.bit_length,
        "exponent": key.exponent,
        "fingerprint": key.fingerprint,
        "modulus_preview": _modulus_preview(key.modulus_hex),
        "created_at": key.created_at,
    }


async def list_keys(
    db: AsyncSession, *, q: str | None = None, skip: int = 0, limit: int = 50
) -> tuple[list[RsaKey], int]:
    stmt = select(RsaKey)
    count_stmt = select(func.count()).select_from(RsaKey)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((RsaKey.label.ilike(like)) | (RsaKey.key_id.ilike(like)) | (RsaKey.fingerprint.ilike(like)))
        count_stmt = select(func.count()).select_from(RsaKey).where(
            (RsaKey.label.ilike(like)) | (RsaKey.key_id.ilike(like)) | (RsaKey.fingerprint.ilike(like))
        )
    total = (await db.execute(count_stmt)).scalar_one()
    rows = (await db.execute(stmt.order_by(RsaKey.created_at.desc()).offset(skip).limit(limit))).scalars().all()
    return list(rows), int(total)


async def get_key(db: AsyncSession, key_id: str) -> RsaKey | None:
    result = await db.execute(select(RsaKey).where(RsaKey.key_id == key_id))
    return result.scalar_one_or_none()


async def create_and_run_audit(
    db: AsyncSession,
    key: RsaKey,
    *,
    run_ecm: bool = True,
    timeout_ms: int | None = None,
    curves: int | None = None,
    b1: int | None = None,
) -> Audit:
    audit = Audit(
        audit_id=_uid("aud"),
        key_id=key.id,
        status=JobStatus.RUNNING.value,
        ecm_config_json={"run_ecm": run_ecm, "timeout_ms": timeout_ms, "curves": curves, "b1": b1},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    try:
        result = run_audit_pipeline(
            key.modulus_hex,
            key.exponent,
            run_ecm=run_ecm,
            timeout_ms=timeout_ms,
            curves=curves,
            b1=b1,
        )
        audit.status = JobStatus.COMPLETED.value
        audit.final_state = result["final_state"]
        audit.factor_found = result["factor_found"]
        audit.factor_hex = result["factor_hex"]
        audit.cofactor_hex = result["cofactor_hex"]
        audit.elapsed_ms = result["elapsed_ms"]
        audit.checks_json = result["checks"]
        audit.warnings_json = result["warnings"]
        audit.recommendations_json = result["recommendations"]
        audit.timeline_json = result["timeline"]
        audit.ecm_config_json = result["ecm_config"]
        audit.completed_at = _utcnow()

        for f in result["findings"]:
            db.add(
                AuditFinding(
                    audit_id=audit.id,
                    category=f["category"],
                    code=f["code"],
                    severity=f["severity"],
                    title=f["title"],
                    detail=f["detail"],
                )
            )

        if result.get("ecm") is not None:
            ecm = result["ecm"]
            db.add(
                EcmRun(
                    audit_id=audit.id,
                    status=JobStatus.TIMED_OUT.value if ecm.get("timed_out") else JobStatus.COMPLETED.value,
                    curves_requested=(result["ecm_config"] or {}).get("curves") or 0,
                    curves_tried=ecm.get("curves_tried") or 0,
                    b1=(result["ecm_config"] or {}).get("b1") or 0,
                    timeout_ms=(result["ecm_config"] or {}).get("timeout_ms") or 0,
                    elapsed_ms=ecm.get("elapsed_ms"),
                    factor_found=bool(ecm.get("factor_found")),
                    factor_hex=result.get("factor_hex"),
                    message=ecm.get("message") or "",
                    completed_at=_utcnow(),
                )
            )
        await db.commit()
        await db.refresh(audit)
        return audit
    except Exception as exc:  # noqa: BLE001 — persist failure state
        audit.status = JobStatus.FAILED.value
        audit.final_state = AuditState.INVALID_KEY.value
        audit.error_message = str(exc)
        audit.completed_at = _utcnow()
        await db.commit()
        await db.refresh(audit)
        return audit


async def get_audit(db: AsyncSession, audit_id: str) -> Audit | None:
    result = await db.execute(select(Audit).where(Audit.audit_id == audit_id))
    return result.scalar_one_or_none()


async def list_audits(db: AsyncSession, *, skip: int = 0, limit: int = 50) -> tuple[list[Audit], int]:
    total = (await db.execute(select(func.count()).select_from(Audit))).scalar_one()
    rows = (
        await db.execute(select(Audit).order_by(Audit.created_at.desc()).offset(skip).limit(limit))
    ).scalars().all()
    return list(rows), int(total)


async def audit_to_out(db: AsyncSession, audit: Audit) -> dict[str, Any]:
    key = await db.get(RsaKey, audit.key_id)
    findings = (
        await db.execute(select(AuditFinding).where(AuditFinding.audit_id == audit.id))
    ).scalars().all()
    ecm_run = (
        await db.execute(
            select(EcmRun).where(EcmRun.audit_id == audit.id).order_by(EcmRun.id.desc())
        )
    ).scalars().first()

    finding_dicts = [
        {
            "category": f.category,
            "code": f.code,
            "severity": f.severity,
            "title": f.title,
            "detail": f.detail,
        }
        for f in findings
    ]
    ecm = None
    if ecm_run:
        ecm = {
            "status": ecm_run.status,
            "curves_tried": ecm_run.curves_tried,
            "curves_requested": ecm_run.curves_requested,
            "b1": ecm_run.b1,
            "timeout_ms": ecm_run.timeout_ms,
            "elapsed_ms": ecm_run.elapsed_ms,
            "factor_found": ecm_run.factor_found,
            "message": ecm_run.message,
            "timed_out": ecm_run.status == JobStatus.TIMED_OUT.value,
        }

    return {
        "id": audit.id,
        "audit_id": audit.audit_id,
        "key_id": key.key_id if key else "",
        "status": audit.status,
        "final_state": audit.final_state,
        "factor_found": audit.factor_found,
        "factor_hex": audit.factor_hex,
        "cofactor_hex": audit.cofactor_hex,
        "elapsed_ms": audit.elapsed_ms,
        "checks": [f for f in finding_dicts if f["category"] == "DETERMINISTIC"],
        "warnings": [f for f in finding_dicts if f["category"] == "HEURISTIC"],
        "findings": finding_dicts,
        "recommendations": audit.recommendations_json or [],
        "timeline": audit.timeline_json or [],
        "ecm": ecm,
        "ecm_config": audit.ecm_config_json,
        "bit_length": key.bit_length if key else None,
        "exponent": key.exponent if key else None,
        "key_label": key.label if key else None,
        "created_at": audit.created_at,
        "completed_at": audit.completed_at,
        "error_message": audit.error_message,
    }


async def dashboard_summary(db: AsyncSession) -> dict[str, Any]:
    total_keys = (await db.execute(select(func.count()).select_from(RsaKey))).scalar_one()
    total_audits = (await db.execute(select(func.count()).select_from(Audit))).scalar_one()

    async def count_state(state: str) -> int:
        return int(
            (
                await db.execute(select(func.count()).select_from(Audit).where(Audit.final_state == state))
            ).scalar_one()
        )

    factor_found = await count_state(AuditState.FACTOR_FOUND.value)
    suspicious = await count_state(AuditState.SUSPICIOUS.value)
    inconclusive = await count_state(AuditState.INCONCLUSIVE.value)
    no_weakness = await count_state(AuditState.NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS.value)
    invalid = await count_state(AuditState.INVALID_KEY.value)

    avg = (
        await db.execute(select(func.avg(Audit.elapsed_ms)).where(Audit.elapsed_ms.is_not(None)))
    ).scalar_one()

    recent_rows = (
        await db.execute(select(Audit).order_by(Audit.created_at.desc()).limit(8))
    ).scalars().all()
    recent = [await audit_to_out(db, a) for a in recent_rows]

    # key size buckets
    keys = (await db.execute(select(RsaKey))).scalars().all()
    size_dist: dict[str, int] = {"<512": 0, "512-1023": 0, "1024-2047": 0, "≥2048": 0}
    for k in keys:
        b = k.bit_length
        if b < 512:
            size_dist["<512"] += 1
        elif b < 1024:
            size_dist["512-1023"] += 1
        elif b < 2048:
            size_dist["1024-2047"] += 1
        else:
            size_dist["≥2048"] += 1

    activity = []
    for a in recent_rows[:12]:
        activity.append(
            {
                "audit_id": a.audit_id,
                "state": a.final_state,
                "at": a.created_at.isoformat() if a.created_at else None,
                "elapsed_ms": a.elapsed_ms,
            }
        )

    return {
        "total_keys": int(total_keys),
        "total_audits": int(total_audits),
        "factor_found": factor_found,
        "suspicious": suspicious,
        "inconclusive": inconclusive,
        "no_weakness": no_weakness,
        "invalid": invalid,
        "avg_audit_ms": float(avg) if avg is not None else None,
        "recent_audits": recent,
        "risk_distribution": {
            "FACTOR_FOUND": factor_found,
            "SUSPICIOUS": suspicious,
            "INCONCLUSIVE": inconclusive,
            "NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS": no_weakness,
            "INVALID_KEY": invalid,
        },
        "key_size_distribution": size_dist,
        "activity": activity,
    }


async def create_report(db: AsyncSession, audit: Audit) -> Report:
    out = await audit_to_out(db, audit)
    key = await db.get(RsaKey, audit.key_id)
    content = {
        "branding": {"product": "RSA-SHIELD", "team": "Team Aegis", "institution": "Bennett University"},
        "executive_summary": {
            "final_state": audit.final_state,
            "factor_found": audit.factor_found,
            "interpretation": _interpret(audit.final_state),
        },
        "key_information": key_to_dict(key) if key else {},
        "parameter_analysis": out.get("checks", []),
        "heuristic_warnings": out.get("warnings", []),
        "ecm_analysis": out.get("ecm"),
        "evidence": {
            "factor_hex": audit.factor_hex,
            "cofactor_hex": audit.cofactor_hex,
            "factor_found": audit.factor_found,
        },
        "recommendations": audit.recommendations_json or [],
        "limitations": [
            "Absence of a discovered factor is not mathematical proof of security.",
            "ECM is a budgeted probe and does not break properly generated modern RSA within typical limits.",
            "Only authorized public keys/moduli should be audited.",
        ],
        "audit_metadata": {
            "audit_id": audit.audit_id,
            "status": audit.status,
            "elapsed_ms": audit.elapsed_ms,
            "created_at": audit.created_at.isoformat() if audit.created_at else None,
            "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
            "ecm_config": audit.ecm_config_json,
        },
        "timeline": audit.timeline_json or [],
    }
    report = Report(
        report_id=_uid("rpt"),
        audit_id=audit.id,
        format="json",
        content_json=content,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


def _interpret(state: str | None) -> str:
    return {
        AuditState.FACTOR_FOUND.value: "Mathematical evidence of modulus weakness: a non-trivial factor was discovered.",
        AuditState.SUSPICIOUS.value: "Heuristic warnings were raised. This is not the same as factorization evidence.",
        AuditState.INCONCLUSIVE.value: "Configured ECM budget did not yield a factor. This is inconclusive, not a security proof.",
        AuditState.NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS.value: "Configured deterministic checks did not flag an issue. This is not a formal security proof.",
        AuditState.INVALID_KEY.value: "Input could not be validated as an RSA public key/modulus.",
    }.get(state or "", "No interpretation available.")


# silence unused import warning helpers
secrets  # noqa: B018 — reserved for future API tokens
ParseError  # noqa: B018
