"""Page 2: two-column layout — repository activity summaries."""

from __future__ import annotations

from reportlab.platypus import FrameBreak, Paragraph, Spacer

from daily_planner.models import BriefingData, RepoSummary


def build_page_two_stories(briefing: BriefingData, styles: dict) -> list:
    """Build Platypus flowables for the two-column repo activity page."""
    if not briefing.repo_summaries:
        return [Paragraph("No repositories configured", styles["p2_body"])]

    story: list = []
    mid = (len(briefing.repo_summaries) + 1) // 2

    # Left column
    for summary in briefing.repo_summaries[:mid]:
        story.extend(_build_repo_section(summary, styles))

    story.append(FrameBreak())

    # Right column
    for summary in briefing.repo_summaries[mid:]:
        story.extend(_build_repo_section(summary, styles))

    return story


def _build_repo_section(summary: RepoSummary, styles: dict) -> list:
    """Render a single repo's activity section."""
    items: list = []

    repo_label = f"{summary.repo.owner}/{summary.repo.name}"
    items.append(Paragraph(f"<b>{_escape(repo_label)}</b>", styles["p2_heading"]))

    if summary.error:
        items.append(Paragraph(
            f"Unavailable — {_escape(summary.error)}",
            styles["p2_error"],
        ))
    elif summary.narrative:
        items.append(Paragraph(_escape(summary.narrative), styles["p2_body"]))
    elif summary.activities:
        # Raw activity fallback
        items.append(Paragraph(
            "<i>Summarisation unavailable — showing raw activity</i>",
            styles["p2_error"],
        ))
        for activity in summary.activities:
            atype = activity.activity_type
            title = _escape(activity.title)
            author = _escape(activity.author)
            line = f"• [{atype}] {title} — {author}"
            items.append(Paragraph(line, styles["p2_body"]))
    else:
        items.append(Paragraph("No recent activity", styles["p2_body"]))

    items.append(Spacer(1, 8))
    return items


def _escape(text: str) -> str:
    """Escape XML special characters for reportlab Paragraphs."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
