from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto.parser import ParseError
from app.database.session import get_db
from app.schemas.api import (
    AuditCreate,
    AuditOut,
    DashboardSummary,
    KeyCreatePem,
    KeyCreateRaw,
    KeyOut,
    ReportOut,
    TestLabRunRequest,
)
from app.services import audit_service
from app.services.fixtures import FIXTURES, get_fixture

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "RSA-SHIELD"}


@router.post("/keys/pem", response_model=KeyOut)
async def upload_pem(body: KeyCreatePem, db: AsyncSession = Depends(get_db)):
    try:
        key = await audit_service.create_key_from_pem(db, body.pem, body.label, body.source)
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return audit_service.key_to_dict(key)


@router.post("/keys/raw", response_model=KeyOut)
async def upload_raw(body: KeyCreateRaw, db: AsyncSession = Depends(get_db)):
    try:
        key = await audit_service.create_key_from_raw(db, body.n, body.e, body.label, body.source)
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return audit_service.key_to_dict(key)


@router.get("/keys")
async def keys(
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await audit_service.list_keys(db, q=q, skip=skip, limit=limit)
    return {"total": total, "items": [audit_service.key_to_dict(k) for k in rows]}


@router.get("/keys/{key_id}", response_model=KeyOut)
async def key_detail(key_id: str, db: AsyncSession = Depends(get_db)):
    key = await audit_service.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return audit_service.key_to_dict(key)


@router.post("/audits", response_model=AuditOut)
async def start_audit(body: AuditCreate, db: AsyncSession = Depends(get_db)):
    key = await audit_service.get_key(db, body.key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    audit = await audit_service.create_and_run_audit(
        db,
        key,
        run_ecm=body.run_ecm,
        timeout_ms=body.timeout_ms,
        curves=body.curves,
        b1=body.b1,
    )
    return await audit_service.audit_to_out(db, audit)


@router.get("/audits")
async def audits(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await audit_service.list_audits(db, skip=skip, limit=limit)
    items = [await audit_service.audit_to_out(db, a) for a in rows]
    return {"total": total, "items": items}


@router.get("/audits/{audit_id}", response_model=AuditOut)
async def audit_detail(audit_id: str, db: AsyncSession = Depends(get_db)):
    audit = await audit_service.get_audit(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return await audit_service.audit_to_out(db, audit)


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def dashboard(db: AsyncSession = Depends(get_db)):
    return await audit_service.dashboard_summary(db)


@router.get("/test-lab/fixtures")
async def test_lab_fixtures():
    return {
        "items": [
            {
                "id": f["id"],
                "name": f["name"],
                "description": f["description"],
                "category": f["category"],
                "expected_hint": f["expected_hint"],
            }
            for f in FIXTURES
        ]
    }


@router.post("/test-lab/run", response_model=AuditOut)
async def test_lab_run(body: TestLabRunRequest, db: AsyncSession = Depends(get_db)):
    fixture = get_fixture(body.fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Unknown fixture")
    try:
        if fixture.get("pem"):
            key = await audit_service.create_key_from_pem(
                db, fixture["pem"], label=fixture["name"], source=f"test-lab:{fixture['id']}"
            )
        elif fixture.get("n") is not None:
            key = await audit_service.create_key_from_raw(
                db, str(fixture["n"]), int(fixture["e"]), label=fixture["name"], source=f"test-lab:{fixture['id']}"
            )
        else:
            raise HTTPException(status_code=400, detail="Fixture has no usable key material")
    except ParseError as exc:
        # Represent invalid fixture as a synthetic failed audit response shape
        raise HTTPException(status_code=400, detail=exc.message) from exc

    audit = await audit_service.create_and_run_audit(
        db, key, run_ecm=body.run_ecm, timeout_ms=body.timeout_ms
    )
    return await audit_service.audit_to_out(db, audit)


@router.post("/reports/{audit_id}", response_model=ReportOut)
async def generate_report(audit_id: str, db: AsyncSession = Depends(get_db)):
    audit = await audit_service.get_audit(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    report = await audit_service.create_report(db, audit)
    return {
        "report_id": report.report_id,
        "audit_id": audit.audit_id,
        "format": report.format,
        "content": report.content_json or {},
        "created_at": report.created_at,
    }


@router.post("/inventory/batch-gcd")
async def inventory_batch_gcd(db: AsyncSession = Depends(get_db)):
    """Pairwise shared-factor scan over stored public moduli (authorized inventory only)."""
    return await audit_service.inventory_batch_gcd(db)


@router.get("/evaluation/suite")
async def evaluation_suite(ecm_timeout_ms: int = Query(3000, ge=500, le=30_000)):
    """Reproducible fixture evaluation for demos / paper tables (never claims SECURE)."""
    from app.services.evaluation import run_evaluation_suite

    return run_evaluation_suite(ecm_timeout_ms=ecm_timeout_ms)


@router.get("/research/related-work")
async def related_work():
    """Positioning vs prior tools — honest gap statement for academic framing."""
    return {
        "product": "RSA-SHIELD",
        "positioning": (
            "Evidence-tiered educational public-key auditing platform with budgeted probes. "
            "Not a novel factorization algorithm and not an Internet-scale measurement study."
        ),
        "items": [
            {
                "name": "Mining Your Ps and Qs (Heninger et al., USENIX Security 2012)",
                "focus": "Internet-scale shared RSA factors via batch GCD",
                "gap_vs_us": "We provide inventory-scale pairwise GCD for authorized keys only, not IPv4 scans.",
            },
            {
                "name": "ROCA (CCS 2017) + crocs-muni/roca",
                "focus": "Infineon key fingerprint + Coppersmith factorization",
                "gap_vs_us": "We ship an educational fingerprint heuristic; authoritative re-check recommended.",
            },
            {
                "name": "badkeys (Hanno Böck)",
                "focus": "Production checker for known vulnerable key classes",
                "gap_vs_us": "Broader vuln coverage; we emphasize evidence tiers + lab pedagogy + ECM budget.",
            },
            {
                "name": "RsaCtfTool",
                "focus": "Multi-attack CTF factorization toolbox",
                "gap_vs_us": "Attack-oriented CLI; we are an audit UI with never-SECURE classification.",
            },
            {
                "name": "Fermat in the wild (ePrint 2023) / RSAScan",
                "focus": "Close-prime / GPU weak-key scanning at scale",
                "gap_vs_us": "We include a budgeted Fermat probe for near-twins inside the audit pipeline.",
            },
        ],
        "our_contributions": [
            "End-to-end audit pipeline: parse → analyze → Fermat → Wiener → ROCA fingerprint → ECM",
            "Evidence taxonomy that forbids absolute SECURE labels",
            "Controlled Test Lab fixtures + reproducible evaluation suite endpoint",
            "Inventory batch-GCD for shared-factor collisions among stored public keys",
        ],
    }
