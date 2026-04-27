# Data Model: Markdown Briefing Overhaul

**Feature**: 005-markdown-briefing-overhaul  
**Date**: 2026-04-26

## Entity Changes

### Configuration (MODIFIED)

**File**: `src/daily_planner/models/config.py`

```python
@dataclass
class Configuration:
    """User-editable settings loaded from config/settings.toml."""

    output_path: str = "~/Desktop"
    repos_file: str = "config/repos.txt"

    @property
    def resolved_output_path(self) -> Path:
        return Path(self.output_path).expanduser()

    @property
    def resolved_repos_file(self) -> Path:
        return Path(self.repos_file)
```

**Changes**:
- REMOVED: `page_one_font_size: float`
- REMOVED: `page_two_font_size: float`

### ActionSuggestion (NEW)

**File**: `src/daily_planner/models/task.py` (added to existing file)

```python
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
```

### BriefingData (MODIFIED)

**File**: `src/daily_planner/models/__init__.py`

```python
@dataclass
class BriefingData:
    """Top-level data structure passed to render_markdown."""

    date: date
    config: Configuration
    calendar_events: list[CalendarEvent] | None = None
    calendar_error: str | None = None
    today_tasks: list[Task] | None = None
    today_error: str | None = None
    tomorrow_tasks: list[Task] | None = None
    tomorrow_error: str | None = None
    repo_summaries: list[RepoSummary] = field(default_factory=list)
    action_suggestions: list[ActionSuggestion] = field(default_factory=list)
```

**Changes**:
- ADDED: `action_suggestions: list[ActionSuggestion]` (default empty list)
- Updated docstring: "render_markdown" instead of "render_pdf"

### Task (MODIFIED)

**File**: `src/daily_planner/models/task.py`

Already has `area: str | None = None`. Add `area_created: date | None = None` to support sorting Area groups by creation date.

**Changes**:
- ADDED: `area_created: date | None = None` — the creation date of the task's Area in Things 3, used for sorting Area groups (oldest first). `None` when the task has no Area or the creation date is unavailable.
- Add `area_created` to `from_dict` classmethod (parse from ISO string if present).

### Repository, ActivityItem, RepoSummary (UNCHANGED)

**File**: `src/daily_planner/models/repo.py`

No changes needed. Narratives already support blank lines as plain text.

### CalendarEvent (UNCHANGED)

**File**: `src/daily_planner/models/calendar.py`

No changes needed.

## Relationship Diagram

```
Configuration ─────────────┐
                            │
CalendarEvent[] ──────────┐ │
                          │ │
Task[] (today) ──────────┐│ │
                         ││ │
Task[] (tomorrow) ──────┐││ │
                        │││ │
ActionSuggestion[] ────┐│││ │
                       ││││ │
RepoSummary[] ────────┐│││││
                      │││││├──► BriefingData ──► markdown/renderer.py ──► .md file
                      ├┘││││
Task.area (str|None)  │ ││││
  └── groups tasks    │ ││││
      by Area heading │ ││││
                      └─┘│││
                         └┘│
                           └
```

## Validation Rules

| Entity | Field | Rule |
|--------|-------|------|
| ActionSuggestion | task_title | Non-empty string |
| ActionSuggestion | suggestion | Non-empty string |
| Configuration | output_path | Must resolve within `Path.home()` (validated in tool handler, not model) |

## State Transitions

No state machines in this feature. All entities are immutable
dataclasses created once and passed to the renderer.
