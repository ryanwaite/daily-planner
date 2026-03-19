"""Repository and activity models for GitHub/ADO integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Repository:
    """A configured GitHub or ADO repo to track."""

    platform: str  # "github" or "ado"
    owner: str
    name: str
    url: str
    project: str | None = None  # Required for ADO only

    def __post_init__(self) -> None:
        if self.platform not in ("github", "ado"):
            raise ValueError(f"platform must be 'github' or 'ado', got '{self.platform}'")
        if not self.owner.strip():
            raise ValueError("Repository owner must be non-empty")
        if not self.name.strip():
            raise ValueError("Repository name must be non-empty")
        if self.platform == "ado" and not self.project:
            raise ValueError("ADO repositories require a project name")


@dataclass
class ActivityItem:
    """A single event in a repository since the last business day."""

    repo: Repository
    activity_type: str  # "commit", "pr", or "issue"
    title: str
    author: str
    timestamp: datetime
    url: str | None = None
    pr_state: str | None = None  # "opened", "merged", "closed" (PRs only)
    body: str | None = None  # Description/message body (truncated)
    labels: list[str] = field(default_factory=list)
    related_refs: list[str] = field(default_factory=list)  # Related issue/PR references

    def __post_init__(self) -> None:
        if self.activity_type not in ("commit", "pr", "issue"):
            raise ValueError(
                f"activity_type must be 'commit', 'pr', or 'issue', got '{self.activity_type}'"
            )
        if not self.title.strip():
            raise ValueError("ActivityItem title must be non-empty")
        if not self.author.strip():
            raise ValueError("ActivityItem author must be non-empty")


@dataclass
class RepoSummary:
    """Combines raw activity with an optional LLM-generated narrative for one repository."""

    repo: Repository
    activities: list[ActivityItem] = field(default_factory=list)
    narrative: str | None = None
    error: str | None = None
