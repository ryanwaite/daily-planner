"""Page 2: two-column layout — repository activity summaries."""

from __future__ import annotations

from reportlab.platypus import FrameBreak, Paragraph, Spacer

from daily_planner.models import BriefingData, RepoSummary
from daily_planner.models.repo import ActivityItem

_TYPE_LABELS = {"commit": "Commit", "pr": "PR", "issue": "Issue"}


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
        for activity in summary.activities:
            items.extend(_build_activity(activity, styles))
    else:
        items.append(Paragraph("No recent activity", styles["p2_body"]))

    items.append(Spacer(1, 8))
    return items


def _build_activity(activity: ActivityItem, styles: dict) -> list:
    """Render a single activity item with full context."""
    items: list = []

    # Header line: type badge + title + author
    type_label = _TYPE_LABELS.get(activity.activity_type, activity.activity_type)
    state_suffix = ""
    if activity.pr_state:
        state_suffix = f" ({activity.pr_state})"
    header = (
        f"<b>[{_escape(type_label)}{_escape(state_suffix)}]</b> "
        f"{_escape(activity.title)} — <i>{_escape(activity.author)}</i>"
    )
    items.append(Paragraph(header, styles["p2_body"]))

    # Body/description
    if activity.body:
        body_text = activity.body.strip()
        if len(body_text) >= 297:
            body_text = body_text[:297] + "…"
        items.append(Paragraph(_escape(body_text), styles["p2_body"]))

    # Labels
    if activity.labels:
        label_str = ", ".join(_escape(l) for l in activity.labels)
        items.append(Paragraph(f"Labels: <i>{label_str}</i>", styles["p2_body"]))

    # Related references
    if activity.related_refs:
        refs_str = ", ".join(_escape(r) for r in activity.related_refs)
        items.append(Paragraph(f"Related: {refs_str}", styles["p2_body"]))

    items.append(Spacer(1, 4))
    return items


def _escape(text: str) -> str:
    """Escape XML special characters for reportlab Paragraphs."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
