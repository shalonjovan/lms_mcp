"""Document generation — creates PDF and DOCX submission files."""

import logging
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)

from config.settings import GENERATED_DIR
from app.documents.templates import get_student_info

logger = logging.getLogger(__name__)


def _build_absolute_path(
    assignment_id: str, title: str, ext: str
) -> Path:
    """Build output path: generated/{assignment_id}_{slugified_title}.{ext}."""
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
    safe_title = safe_title.strip().replace(" ", "_")[:60]
    fname = f"{assignment_id}_{safe_title}.{ext}"
    return GENERATED_DIR / fname


def generate_docx(
    assignment_id: str,
    title: str,
    subject: str,
    solution_markdown: str,
) -> Path:
    """Generate a DOCX file from markdown solution content.

    Returns:
        Path to the generated DOCX file.
    """
    out_path = _build_absolute_path(assignment_id, title, "docx")
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.2)
        section.right_margin = Inches(1.2)

    info = get_student_info()
    today = datetime.now().strftime("%B %d, %Y")

    # Header block
    header_items = [
        ("Name", info["name"]),
        ("Reg No", info["reg_no"]),
        ("Subject", subject),
        ("Date", today),
    ]
    for label, value in header_items:
        p = doc.add_paragraph()
        run_label = p.add_run(f"{label}: ")
        run_label.bold = True
        run_label.font.size = Pt(11)
        run_value = p.add_run(value)
        run_value.font.size = Pt(11)

    # Separator
    doc.add_paragraph("─" * 60)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_t = p_title.add_run(title)
    run_t.bold = True
    run_t.font.size = Pt(16)

    # Simple markdown → DOCX conversion
    for line in solution_markdown.split("\n"):
        line = line.rstrip()
        if not line:
            doc.add_paragraph("")
        elif line.startswith("# "):
            p = doc.add_paragraph()
            run = p.add_run(line[2:])
            run.bold = True
            run.font.size = Pt(16)
        elif line.startswith("## "):
            p = doc.add_paragraph()
            run = p.add_run(line[3:])
            run.bold = True
            run.font.size = Pt(14)
        elif line.startswith("### "):
            p = doc.add_paragraph()
            run = p.add_run(line[4:])
            run.bold = True
            run.font.size = Pt(12)
        elif line.startswith("```"):
            # Code block — skip markers, content inline
            pass
        elif line.startswith("- ") or line.startswith("* "):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif line.startswith("1. "):
            doc.add_paragraph(line[3:], style="List Number")
        else:
            p = doc.add_paragraph(line)
            for run in p.runs:
                run.font.size = Pt(11)

    doc.save(str(out_path))
    logger.info(f"Generated DOCX: {out_path}")
    return out_path


def generate_pdf(
    assignment_id: str,
    title: str,
    subject: str,
    solution_markdown: str,
) -> Path:
    """Generate a PDF file from markdown solution content.

    Returns:
        Path to the generated PDF file.
    """
    out_path = _build_absolute_path(assignment_id, title, "pdf")
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        topMargin=inch,
        bottomMargin=inch,
        leftMargin=1.2 * inch,
        rightMargin=1.2 * inch,
    )

    styles = getSampleStyleSheet()
    info = get_student_info()
    today = datetime.now().strftime("%B %d, %Y")

    elements = []

    # Header
    for label, value in [
        ("Name", info["name"]),
        ("Reg No", info["reg_no"]),
        ("Subject", subject),
        ("Date", today),
    ]:
        text = f"<b>{label}:</b>  {value}"
        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 2))

    elements.append(Spacer(1, 12))

    # Title
    title_style = ParagraphStyle(
        "Title2", parent=styles["Title"], alignment=1, spaceAfter=20
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))

    # Content
    for line in solution_markdown.split("\n"):
        line = line.rstrip()
        if not line:
            elements.append(Spacer(1, 6))
        elif line.startswith("# "):
            elements.append(Paragraph(line[2:], styles["Heading1"]))
        elif line.startswith("## "):
            elements.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("### "):
            elements.append(Paragraph(line[4:], styles["Heading3"]))
        elif line.startswith("```"):
            pass
        elif line.startswith("- ") or line.startswith("* "):
            elements.append(Paragraph(f"&bull; {line[2:]}", styles["Normal"]))
        else:
            elements.append(Paragraph(line, styles["Normal"]))

    doc.build(elements)
    logger.info(f"Generated PDF: {out_path}")
    return out_path
