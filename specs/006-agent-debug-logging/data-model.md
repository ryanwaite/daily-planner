# Data Model: Agent Debug Logging

**Feature**: 006-agent-debug-logging  
**Date**: 2026-04-26

## Overview

This feature does not introduce new domain entities into the `models/` package. Debug logging is an infrastructure concern, not a domain concern. The data structures live in the new `src/daily_planner/logging.py` module.

## Entities

### LogEntry (conceptual — serialized directly, not a dataclass)

Each log entry is a JSON object written as a single line in the JSONL file. It is not a Python dataclass — it is constructed as a dict inside the `JsonlFormatter.format()` method and serialized via `json.dumps()`.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | When the event occurred, local time, e.g. `"2026-04-26T08:30:12.456789"` |
| `level` | string | Yes | Log level: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |
| `operation` | string | Yes | What operation produced this entry, e.g. `"get_today_tasks"`, `"github.fetch_commits"`, `"render_markdown"` |
| `direction` | string | No | `"request"`, `"response"`, or `"internal"`. Omitted when not applicable. |
| `message` | string | Yes | Human-readable description of the event |
| `data` | object | No | Arbitrary payload (request params, response body, etc.). Truncated at 5,000 chars per string field. |
| `traceback` | string | No | Formatted exception traceback when logging an error with `exc_info` |
| `duration_ms` | number | No | Elapsed time in milliseconds for timed operations (tool calls, API requests) |

**Example entry** (single line in the file, formatted here for readability):
```json
{
  "timestamp": "2026-04-26T08:30:12.456789",
  "level": "DEBUG",
  "operation": "github.fetch_commits",
  "direction": "request",
  "message": "Fetching commits for ryanwaite/daily-planner since 2026-04-25",
  "data": {"repo": "ryanwaite/daily-planner", "since": "2026-04-25"}
}
```

### Debug Log File (filesystem artifact)

A timestamped JSONL file containing all log entries from a single briefing run.

**Properties**:

| Property | Value |
|----------|-------|
| Location | Configured output directory (`settings.toml` → `[output].path`) |
| Name pattern | `debug_YYYY-MM-DD_HHMMSS_<pid>.jsonl` |
| Encoding | UTF-8 |
| Format | JSONL (one JSON object per line) |
| Lifecycle | Created when debug flag is active; never automatically deleted |

**Example filename**: `debug_2026-04-26_083012_48291.jsonl`

## Relationships

```text
Briefing Run (1) ──creates──> (1) Debug Log File ──contains──> (N) LogEntry
```

No relationship to existing domain models (`BriefingData`, `Task`, `RepoSummary`, etc.) — debug logging observes these structures but does not modify or depend on them.

## Validation Rules

- `timestamp`: Always present, always ISO 8601 format
- `level`: Must be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `operation`: Non-empty string; should match a known tool or integration name
- `data` string fields: Truncated to 5,000 characters with `"...[truncated]"` suffix when exceeded
- No validation at write time (logging must not throw); malformed entries are best-effort

## State Transitions

Debug logging has two states, determined at server startup:

```text
DAILY_PLANNER_DEBUG unset/empty ──> DISABLED (no logger, no file, no-ops)
DAILY_PLANNER_DEBUG=1            ──> ENABLED  (logger + FileHandler active)
```

State is immutable after startup — it cannot be toggled during a run.
