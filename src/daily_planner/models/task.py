"""Task model for Things 3 to-do items."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    """A Things 3 to-do item."""

    title: str
    due_date: date
    sort_position: int = 0
    project: str | None = None
    area: str | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Task title must be non-empty")

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Create a Task from a JSON-compatible dict."""
        due = data["due_date"]
        if isinstance(due, str):
            due = date.fromisoformat(due)
        return cls(
            title=data["title"],
            due_date=due,
            sort_position=data.get("sort_position", 0),
            project=data.get("project"),
            area=data.get("area"),
            tags=data.get("tags", []),
        )
