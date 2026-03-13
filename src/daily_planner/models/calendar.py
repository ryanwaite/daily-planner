"""CalendarEvent model for Outlook calendar entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CalendarEvent:
    """A single Outlook calendar entry for today.

    Supplied by the agent from the Work IQ MCP server.
    """

    title: str
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    location: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("CalendarEvent title must be non-empty")
        if not self.is_all_day and self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time for non-all-day events")

    @classmethod
    def from_dict(cls, data: dict) -> CalendarEvent:
        """Create a CalendarEvent from a JSON-compatible dict."""
        return cls(
            title=data["title"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            is_all_day=data.get("is_all_day", False),
            location=data.get("location"),
        )
