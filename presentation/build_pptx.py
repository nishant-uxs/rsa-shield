"""Generate research-numbers PowerPoint for Team Aegis."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

OUT = Path(__file__).resolve().parent / "RSA_SHIELD_Research.pptx"
BG = RGBColor(0x0B, 0x12, 0x1A)
CYAN = RGBColor(0x22, 0xD3, 0xEE)
WHITE = RGBColor(0xE8, 0xEE, 0xF5)
MUTED = RGBColor(0x9A, 0xA8, 0xB8)
AMBER = RGBColor(0xF5, 0xB9, 0x4A)


def _bg(slide) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG


def _text(slide, left, top, width, height, text: str, size: int, *, bold=False, color=WHITE) -> None:
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Calibri"


def _bullets(slide, left, top, width, height, items: list[str], size: int = 16) -> None:
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = "•  " + item
        run.font.size = Pt(size)
        run.font.color.rgb = WHITE
        run.font.name = "Calibri"
        p.space_after = Pt(10)


def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _text(s, 0.7, 2.0, 12, 1, "RSA-SHIELD", 40, bold=True, color=CYAN)
    _text(
        s,
        0.7,
        3.2,
        12,
        1.4,
        "Evidence-correct RSA public-key auditing\nResearch results · Team Aegis · Bennett University",
        18,
    )
    _text(s, 0.7, 6.5, 12, 0.5, "Mentor: Dr. Sachin Choudhary  ·  Never emits absolute SECURE", 12, color=MUTED)

    slides = [
        (
            "Problem (epistemic, not new math)",
            [
                "Scanners often treat “short probe failed” as PASS / SECURE.",
                "Cryptographically, bounded failure ≠ proof of security.",
                "Legacy / embedded RSA still appears in ICS and enterprise PKI.",
                "Need a defensive auditor with honest evidence tiers.",
            ],
        ),
        (
            "What we built",
            [
                "FastAPI + React auditor: PEM / (N,e) ingest; private keys rejected.",
                "Probes: analyzer, Fermat, Wiener, Pollard p−1, educational ROCA, ECM, batch GCD.",
                "Labels: FACTOR_FOUND · SUSPICIOUS · INCONCLUSIVE · NO_WEAKNESS… · INVALID — never SECURE.",
                "RSA-Auditor Bench v1.0 + evaluation endpoints for reproducible tables.",
            ],
        ),
        (
            "Headline numbers (frozen dumps)",
            [
                "Bake-off overconfidence: RSA-SHIELD 0.0 vs badkeys 0.75.",
                "ROCA calibration (CT tip n=500): FP 75% → 0.2%; agreement 25% → 99.8%.",
                "Adaptive scheduler: 1473.92 → 975.75 ms mean wall (1.511×); recall 1.0.",
                "Multi-log CT tip: 12,010 unique moduli; chunked batch-GCD 0 hits (81172.63 ms).",
                "CT probe sample (800): 0 SECURE labels emitted.",
            ],
        ),
        (
            "ROCA: before → after calibration",
            [
                "Legacy educational fingerprint over-triggered on modern CT moduli (~75% FP vs badkeys).",
                "Swept (ratio_threshold, min_gcd) against badkeys ROCA finding as reference.",
                "Chosen calibrated profile: ratio_threshold=0.99, min_gcd=2 (shipped default).",
                "Positive hits stay SUSPICIOUS only — fingerprint ≠ Coppersmith factorization.",
            ],
        ),
        (
            "Adaptive probe scheduler",
            [
                "Fixed budgets waste work on 2048-bit CT-like keys (Fermat rarely helps).",
                "Planner shrinks/skips Fermat and trims Pollard/ECM for large bit-lengths.",
                "Keeps aggressive budgets for small/legacy keys and large-e Wiener cases.",
                "Bench: same planted-factor recall (1.0), lower mean latency (1.511×).",
            ],
        ),
        (
            "Sir live demo script (~3 min)",
            [
                "Open http://127.0.0.1:5173 → Sir Demo.",
                "Run: weak-ecm → fermat-close → wiener-small-d → normal-demo.",
                "Point at evidence timeline; stress never-SECURE on normal-demo.",
                "Optional: Evaluation page for paper tables; Related Work for positioning.",
            ],
        ),
        (
            "Limitations (say these out loud)",
            [
                "Not a new general factorization algorithm.",
                "CT study is a tip sample, not a billion-certificate census.",
                "badkeys is a fingerprint reference, not Infineon ground truth.",
                "Authorized public keys only; inconclusive ≠ certification.",
            ],
        ),
    ]

    for title, bullets in slides:
        s = prs.slides.add_slide(prs.slide_layouts[6])
        _bg(s)
        _text(s, 0.6, 0.4, 12, 0.7, title, 26, bold=True, color=CYAN)
        _bullets(s, 0.7, 1.4, 12, 5.2, bullets)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _text(s, 0.7, 2.3, 12, 1, "Know your keys. Never fake SECURE.", 32, bold=True, color=CYAN)
    _text(
        s,
        0.7,
        3.5,
        12,
        1.5,
        "Team Aegis · Bennett University\nPaper: paper/rsa_shield_ieee.pdf · Demo: /app/demo",
        16,
    )
    _text(s, 0.7, 6.5, 12, 0.4, "Questions welcome", 12, color=MUTED)

    prs.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
