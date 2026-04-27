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
    area_created: date | None = None
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
        area_created_raw = data.get("area_created")
        area_created = (
            date.fromisoformat(area_created_raw)
            if isinstance(area_created_raw, str)
            else area_created_raw
        )
        return cls(
            title=data["title"],
            due_date=due,
            sort_position=data.get("sort_position", 0),
            project=data.get("project"),
            area=data.get("area"),
            area_created=area_created,
            tags=data.get("tags", []),
        )


@dataclass
class ActionSuggestion:
    """An AI-generated next-step suggestion for an unassigned task."""

    task_title: str
    suggestion: str

    def __post_init__(self) -> None:
        if not self.task_title.strip():
            raise ValueError("ActionSuggestion task_title must be non-empty")
        if not self.suggestion.strip():
            raise ValueError("ActionSuggestion suggestion must be non-empty")

    @classmethod
    def from_dict(cls, data: dict) -> ActionSuggestion:
        return cls(
            task_title=data["task_title"],
            suggestion=data["suggestion"],
        )
