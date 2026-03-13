# Data Model: Morning Briefing PDF Generator

**Date**: 2026-03-12
**Feature**: [spec.md](spec.md) | [plan.md](plan.md)

## Entities

### CalendarEvent

Represents a single Outlook calendar entry for today, supplied by
the agent from the Work IQ MCP server.

| Field       | Type          | Required | Notes                                  |
|-------------|---------------|----------|----------------------------------------|
| title       | str           | yes      | Event title                            |
| start_time  | datetime      | yes      | Event start (ISO 8601)                 |
| end_time    | datetime      | yes      | Event end (ISO 8601)                   |
| location    | str \| None   | no       | Physical or virtual location           |
| is_all_day  | bool          | yes      | True for all-day events                |

**Validation**:
- `start_time` < `end_time` (unless `is_all_day`)
- `title` must be non-empty

**Sort**: Chronological by `start_time`; all-day events first.

---

### Task

Represents a Things 3 to-do item.

| Field          | Type          | Required | Notes                               |
|----------------|---------------|----------|-------------------------------------|
| title          | str           | yes      | Task title                          |
| due_date       | date          | yes      | Date the task is due                |
| sort_position  | int           | yes      | Things' default sort order value    |
| project        | str \| None   | no       | Project name from Things            |
| tags           | list[str]     | no       | Tags from Things (may be empty)     |

**Validation**:
- `title` must be non-empty

**Sort**: By `sort_position` (ascending) — preserves Things' default
order.

---

### Repository

A configured GitHub or ADO repo to track.

| Field         | Type   | Required | Notes                                    |
|---------------|--------|----------|------------------------------------------|
| platform      | str    | yes      | `"github"` or `"ado"`                    |
| owner         | str    | yes      | GitHub owner or ADO organisation         |
| project       | str \| None | no  | ADO project name (required for ADO only) |
| name          | str    | yes      | Repository name                          |
| url           | str    | yes      | Full URL for display purposes            |

**Validation**:
- `platform` must be one of `"github"`, `"ado"`
- `owner` and `name` must be non-empty
- If `platform == "ado"`, `project` is required

**Parsed from**: Plain-text repos config file (`config/repos.txt`).
Expected line format:
```
github:owner/repo
ado:org/project/repo
```

---

### ActivityItem

A single event in a repository since the last business day.

| Field            | Type          | Required | Notes                            |
|------------------|---------------|----------|----------------------------------|
| repo             | Repository    | yes      | Parent repository reference      |
| activity_type    | str           | yes      | `"commit"`, `"pr"`, or `"issue"` |
| title            | str           | yes      | Commit message, PR title, etc.   |
| author           | str           | yes      | Username or display name         |
| timestamp        | datetime      | yes      | When the activity occurred       |
| url              | str \| None   | no       | Link to the activity             |
| pr_state         | str \| None   | no       | `"opened"`, `"merged"`, `"closed"` (PRs only) |

**Validation**:
- `activity_type` must be one of the three allowed values
- `title` and `author` must be non-empty

---

### RepoSummary

Combines raw activity with an optional LLM-generated narrative for
one repository.

| Field            | Type               | Required | Notes                         |
|------------------|--------------------|----------|-------------------------------|
| repo             | Repository         | yes      | The repository                |
| activities       | list[ActivityItem] | yes      | Raw activity items (may be []) |
| narrative        | str \| None        | no       | LLM-generated summary text    |
| error            | str \| None        | no       | Error message if fetch failed  |

**State transitions**:
- `activities=[], narrative=None, error=None` → "No recent activity"
- `activities=[...], narrative="..."` → Full LLM summary
- `activities=[...], narrative=None` → Raw activity fallback
- `activities=[], error="..."` → Error notice in PDF

---

### BriefingData

Top-level data structure passed to `render_pdf`. Assembles all
sections for one briefing run.

| Field            | Type                      | Required | Notes                      |
|------------------|---------------------------|----------|----------------------------|
| date             | date                      | yes      | Today's date               |
| calendar_events  | list[CalendarEvent] \| None | no     | None = unavailable         |
| calendar_error   | str \| None               | no       | Error if calendar failed   |
| today_tasks      | list[Task] \| None        | no       | None = unavailable         |
| today_error      | str \| None               | no       | Error if today tasks failed|
| tomorrow_tasks   | list[Task] \| None        | no       | None = unavailable         |
| tomorrow_error   | str \| None               | no       | Error if tomorrow failed   |
| repo_summaries   | list[RepoSummary]         | yes      | One per configured repo    |
| config           | Configuration             | yes      | Font sizes, output path    |

---

### Configuration

User-editable settings loaded from `config/settings.toml`.

| Field              | Type   | Required | Default             | Notes                    |
|--------------------|--------|----------|---------------------|--------------------------|
| page_one_font_size | float  | no       | 9.0                 | Points                   |
| page_two_font_size | float  | no       | 8.0                 | Points                   |
| output_path        | str    | no       | `~/Desktop`         | Directory for PDF output |
| repos_file         | str    | yes      | `config/repos.txt`  | Path to repo list        |

**File format** (`config/settings.toml`):
```toml
[page_one]
font_size = 9.0

[page_two]
font_size = 8.0

[output]
path = "~/Desktop"
repos_file = "config/repos.txt"
```

## Relationships

```
BriefingData
├── date
├── calendar_events: [CalendarEvent, ...]
├── today_tasks: [Task, ...]
├── tomorrow_tasks: [Task, ...]
├── repo_summaries: [RepoSummary, ...]
│   ├── repo: Repository
│   └── activities: [ActivityItem, ...]
└── config: Configuration
```

## Business Day Logic

- "Next business day" for a Friday is Monday.
- "Last business day" for a Monday is Friday.
- Tue–Fri: previous weekday = day - 1.
- Public holidays are NOT accounted for (per spec assumptions).
