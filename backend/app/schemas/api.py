from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "RSA-SHIELD"


class KeyCreatePem(BaseModel):
    label: str = ""
    source: str = "upload"
    pem: str


class KeyCreateRaw(BaseModel):
    label: str = ""
    source: str = "manual"
    n: str
    e: int = 65537


class KeyOut(BaseModel):
    id: int
    key_id: str
    label: str
    source: str
    algorithm: str
    bit_length: int
    exponent: int
    fingerprint: str
    modulus_preview: str
    created_at: datetime


class AuditCreate(BaseModel):
    key_id: str
    run_ecm: bool = True
    timeout_ms: int | None = Field(default=None, ge=500, le=60_000)
    curves: int | None = Field(default=None, ge=1, le=200)
    b1: int | None = Field(default=None, ge=100, le=200_000)


class FindingOut(BaseModel):
    category: str
    code: str
    severity: str
    title: str
    detail: str


class AuditOut(BaseModel):
    id: int
    audit_id: str
    key_id: str
    status: str
    final_state: str | None
    factor_found: bool
    factor_hex: str | None = None
    cofactor_hex: str | None = None
    elapsed_ms: float | None
    checks: list[FindingOut] = []
    warnings: list[FindingOut] = []
    findings: list[FindingOut] = []
    recommendations: list[str] = []
    timeline: list[dict[str, Any]] = []
    ecm: dict[str, Any] | None = None
    ecm_config: dict[str, Any] | None = None
    bit_length: int | None = None
    exponent: int | None = None
    key_label: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None


class DashboardSummary(BaseModel):
    total_keys: int
    total_audits: int
    factor_found: int
    suspicious: int
    inconclusive: int
    no_weakness: int
    invalid: int
    avg_audit_ms: float | None
    recent_audits: list[AuditOut]
    risk_distribution: dict[str, int]
    key_size_distribution: dict[str, int]
    activity: list[dict[str, Any]]


class TestLabRunRequest(BaseModel):
    fixture_id: str
    run_ecm: bool = True
    timeout_ms: int | None = None


class ReportOut(BaseModel):
    report_id: str
    audit_id: str
    format: str
    content: dict[str, Any]
    created_at: datetime
