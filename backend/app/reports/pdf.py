from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch


def build_pdf_report(content: dict[str, Any], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=0.7 * inch, rightMargin=0.7 * inch)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=styles["Title"], textColor=HexColor("#0E7490"), fontSize=18)
    h = ParagraphStyle("H", parent=styles["Heading2"], textColor=HexColor("#1A1F2E"), fontSize=12, spaceBefore=10)
    body = ParagraphStyle("B", parent=styles["BodyText"], fontSize=9, leading=12)

    story = []
    brand = content.get("branding", {})
    story.append(Paragraph("RSA-SHIELD Security Audit Report", title))
    story.append(Paragraph(f"{brand.get('team', 'Team Aegis')} · {brand.get('institution', 'Bennett University')}", body))
    story.append(Spacer(1, 8))

    meta = content.get("audit_metadata", {})
    exe = content.get("executive_summary", {})
    story.append(Paragraph("1. Executive Summary", h))
    story.append(Paragraph(f"<b>Final state:</b> {exe.get('final_state')}", body))
    story.append(Paragraph(f"<b>Factor found:</b> {exe.get('factor_found')}", body))
    story.append(Paragraph(exe.get("interpretation", ""), body))

    story.append(Paragraph("2. Key Information", h))
    key = content.get("key_information", {})
    for k, v in key.items():
        story.append(Paragraph(f"<b>{k}:</b> {v}", body))

    story.append(Paragraph("3. Parameter Analysis (Deterministic)", h))
    for item in content.get("parameter_analysis", []):
        story.append(Paragraph(f"• [{item.get('severity')}] {item.get('title')}: {item.get('detail')}", body))

    story.append(Paragraph("4. Heuristic Warnings", h))
    warns = content.get("heuristic_warnings", [])
    if not warns:
        story.append(Paragraph("None.", body))
    for item in warns:
        story.append(Paragraph(f"• {item.get('title')}: {item.get('detail')}", body))

    story.append(Paragraph("5. ECM Analysis", h))
    ecm = content.get("ecm_analysis") or {}
    story.append(Paragraph(str(ecm), body))

    story.append(Paragraph("6. Evidence", h))
    ev = content.get("evidence", {})
    story.append(Paragraph(f"factor_found={ev.get('factor_found')} factor={ev.get('factor_hex')} cofactor={ev.get('cofactor_hex')}", body))

    story.append(Paragraph("7. Recommendations", h))
    for r in content.get("recommendations", []):
        story.append(Paragraph(f"• {r}", body))

    story.append(Paragraph("8. Limitations", h))
    for r in content.get("limitations", []):
        story.append(Paragraph(f"• {r}", body))

    story.append(Paragraph("9. Audit Metadata", h))
    story.append(Paragraph(f"audit_id={meta.get('audit_id')} elapsed_ms={meta.get('elapsed_ms')} created={meta.get('created_at')}", body))

    doc.build(story)
    return out_path
