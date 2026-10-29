from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), default="Auditor")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    keys = relationship("RsaKey", back_populates="owner")


class RsaKey(Base):
    __tablename__ = "keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="upload")
    label: Mapped[str] = mapped_column(String(256), default="")
    algorithm: Mapped[str] = mapped_column(String(32), default="RSA")
    modulus_hex: Mapped[str] = mapped_column(Text)
    # String so Wiener-sized public exponents (>2^63) persist on SQLite.
    exponent: Mapped[str] = mapped_column(String(2048))
    bit_length: Mapped[int] = mapped_column(Integer)
    fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner = relationship("User", back_populates="keys")
    audits = relationship("Audit", back_populates="key")


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_id: Mapped[int] = mapped_column(ForeignKey("keys.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", index=True)
    final_state: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    elapsed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    factor_found: Mapped[bool] = mapped_column(Boolean, default=False)
    factor_hex: Mapped[str | None] = mapped_column(Text, nullable=True)
    cofactor_hex: Mapped[str | None] = mapped_column(Text, nullable=True)
    checks_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    warnings_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendations_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    timeline_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ecm_config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    key = relationship("RsaKey", back_populates="audits")
    findings = relationship("AuditFinding", back_populates="audit", cascade="all, delete-orphan")
    ecm_runs = relationship("EcmRun", back_populates="audit", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="audit", cascade="all, delete-orphan")


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id"), index=True)
    category: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32), default="info")
    title: Mapped[str] = mapped_column(String(256))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    audit = relationship("Audit", back_populates="findings")


class EcmRun(Base):
    __tablename__ = "ecm_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED")
    curves_requested: Mapped[int] = mapped_column(Integer, default=40)
    curves_tried: Mapped[int] = mapped_column(Integer, default=0)
    b1: Mapped[int] = mapped_column(Integer, default=50000)
    timeout_ms: Mapped[int] = mapped_column(Integer, default=8000)
    elapsed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    factor_found: Mapped[bool] = mapped_column(Boolean, default=False)
    factor_hex: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    audit = relationship("Audit", back_populates="ecm_runs")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id"), index=True)
    format: Mapped[str] = mapped_column(String(16), default="json")
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    audit = relationship("Audit", back_populates="reports")
