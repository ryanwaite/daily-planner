"""PDF layout engine — two-page US Letter template using reportlab."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
)

from daily_planner.models import BriefingData
from daily_planner.pdf.page_one import build_page_one_stories
from daily_planner.pdf.page_two import build_page_two_stories

# Landscape US Letter: swap width and height
PAGE_WIDTH, PAGE_HEIGHT = letter[1], letter[0]  # 792 × 612 pt
LANDSCAPE = (PAGE_WIDTH, PAGE_HEIGHT)
MARGIN = 0.5 * inch
GUTTER = 0.25 * inch


def render_briefing_pdf(briefing: BriefingData) -> Path:
    """Render a two-page PDF from briefing data. Returns the output file path."""
    output_dir = briefing.config.resolved_output_path
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = _format_filename(briefing.date)
    pdf_path = output_dir / filename

    doc = BaseDocTemplate(
        str(pdf_path),
        pagesize=LANDSCAPE,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    # --- Page 1: three-column layout ---
    usable_w = PAGE_WIDTH - 2 * MARGIN
    usable_h = PAGE_HEIGHT - 2 * MARGIN
    col3_w = (usable_w - 2 * GUTTER) / 3

    frames_p1 = [
        Frame(MARGIN, MARGIN, col3_w, usable_h, id="calendar"),
        Frame(MARGIN + col3_w + GUTTER, MARGIN, col3_w, usable_h, id="today"),
        Frame(MARGIN + 2 * (col3_w + GUTTER), MARGIN, col3_w, usable_h, id="tomorrow"),
    ]

    # --- Page 2: two-column layout ---
    col2_w = (usable_w - GUTTER) / 2
    frames_p2 = [
        Frame(MARGIN, MARGIN, col2_w, usable_h, id="repo_left"),
        Frame(MARGIN + col2_w + GUTTER, MARGIN, col2_w, usable_h, id="repo_right"),
    ]

    pt1 = PageTemplate(id="page_one", frames=frames_p1, onPage=_page_one_header(briefing))
    pt2 = PageTemplate(id="page_two", frames=frames_p2, onPage=_page_two_header(briefing))

    doc.addPageTemplates([pt1, pt2])

    # Build story
    styles = _build_styles(briefing.config.page_one_font_size, briefing.config.page_two_font_size)
    story: list = []

    # Page 1 content
    story.extend(build_page_one_stories(briefing, styles))

    # Switch to page 2
    story.append(NextPageTemplate("page_two"))
    story.append(PageBreak())

    # Page 2 content
    story.extend(build_page_two_stories(briefing, styles))

    doc.build(story)
    return pdf_path


def _format_filename(d: date) -> str:
    """Format filename as 'YYYY-MM-DD dddd.pdf' per FR-007."""
    return f"{d.strftime('%Y-%m-%d')} {d.strftime('%A')}.pdf"


def _format_display_date(d: date) -> str:
    """Format display date as 'dddd, MMMM D, YYYY' per FR-007."""
    # strftime %B = full month, %-d = day without leading zero
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}, {d.year}"


def _page_one_header(briefing: BriefingData):
    """Return a callback that draws the page-one header."""
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 12)
        display_date = _format_display_date(briefing.date)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 0.35 * inch, f"Morning Briefing — {display_date}")
        canvas.restoreState()
    return draw


def _page_two_header(briefing: BriefingData):
    """Return a callback that draws the page-two header."""
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 0.35 * inch, "Repository Activity")
        canvas.restoreState()
    return draw


def _build_styles(p1_font_size: float, p2_font_size: float) -> dict[str, ParagraphStyle]:
    """Build paragraph styles for both pages."""
    base = getSampleStyleSheet()
    return {
        "p1_heading": ParagraphStyle(
            "p1_heading",
            parent=base["Heading4"],
            fontSize=p1_font_size + 2,
            spaceAfter=4,
            leading=p1_font_size + 4,
        ),
        "p1_body": ParagraphStyle(
            "p1_body",
            parent=base["Normal"],
            fontSize=p1_font_size,
            leading=p1_font_size + 3,
            spaceAfter=2,
        ),
        "p1_error": ParagraphStyle(
            "p1_error",
            parent=base["Normal"],
            fontSize=p1_font_size,
            leading=p1_font_size + 3,
            textColor="red",
            spaceAfter=2,
        ),
        "p2_heading": ParagraphStyle(
            "p2_heading",
            parent=base["Heading4"],
            fontSize=p2_font_size + 2,
            spaceAfter=4,
            leading=p2_font_size + 4,
        ),
        "p2_body": ParagraphStyle(
            "p2_body",
            parent=base["Normal"],
            fontSize=p2_font_size,
            leading=p2_font_size + 3,
            spaceAfter=2,
        ),
        "p2_error": ParagraphStyle(
            "p2_error",
            parent=base["Normal"],
            fontSize=p2_font_size,
            leading=p2_font_size + 3,
            textColor="red",
            spaceAfter=2,
        ),
    }
