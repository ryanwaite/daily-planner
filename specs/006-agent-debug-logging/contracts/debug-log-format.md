# Contract: Debug Log File Format (JSONL)

**Feature**: 006-agent-debug-logging  
**Type**: File output contract  
**Consumers**: Developer/user reading log files with `cat`, `grep`, `jq`

## Overview

When `DAILY_PLANNER_DEBUG=1` is set, each briefing run produces a single JSONL file in the configured output directory. This contract defines the file naming convention and the schema of each JSON line.

## File Convention

| Property | Contract |
|----------|----------|
| Location | Same directory as markdown briefing output (`settings.toml` → `[output].path`) |
| Name pattern | `debug_YYYY-MM-DD_HHMMSS_<pid>.jsonl` |
| Encoding | UTF-8, no BOM |
| Line separator | `\n` (LF) |
| Lines | Each line is a complete, valid JSON object |

**Example**: `~/Desktop/debug_2026-04-26_083012_48291.jsonl`

## Line Schema

Each line is a JSON object with the following fields:

```jsonc
{
  // REQUIRED fields (always present)
  "timestamp": "2026-04-26T08:30:12.456789",  // ISO 8601, local time, microsecond precision
  "level": "DEBUG",                             // One of: DEBUG, INFO, WARNING, ERROR
  "operation": "get_today_tasks",               // Tool name, integration name, or module name
  "message": "Tool invocation started",         // Human-readable event description

  // OPTIONAL fields (present when applicable)
  "direction": "request",                       // "request", "response", or "internal"
  "data": { ... },                              // Arbitrary payload; string values truncated at 5,000 chars
  "traceback": "Traceback (most recent...)...", // Formatted Python traceback on errors
  "duration_ms": 142.5                          // Elapsed time for timed operations
}
```

### Field Details

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `timestamp` | string | Yes | ISO 8601 with microseconds, local timezone |
| `level` | string | Yes | `"DEBUG"` \| `"INFO"` \| `"WARNING"` \| `"ERROR"` |
| `operation` | string | Yes | Identifies the source: tool name (e.g. `"get_today_tasks"`), integration (e.g. `"github.fetch_commits"`), or module (e.g. `"render_markdown"`) |
| `message` | string | Yes | Human-readable description |
| `direction` | string | No | `"request"` (outgoing call), `"response"` (incoming data), `"internal"` (processing step) |
| `data` | object | No | Request params, response body, or processing details. String values over 5,000 chars are truncated with `"...[truncated]"` suffix |
| `traceback` | string | No | Python traceback string, present only when logging exceptions |
| `duration_ms` | number | No | Milliseconds elapsed, present on tool call end and API response entries |

## Logged Events

The following events produce log entries when debug mode is active:

| Event | Level | Direction | Operation Example |
|-------|-------|-----------|-------------------|
| Tool invocation start | DEBUG | request | `"get_today_tasks"` |
| Tool invocation end | DEBUG | response | `"get_today_tasks"` |
| External API request | DEBUG | request | `"github.fetch_commits"` |
| External API response | DEBUG | response | `"github.fetch_commits"` |
| Data transformation | DEBUG | internal | `"render_markdown.group_tasks"` |
| Render output | INFO | internal | `"render_markdown"` |
| Warning (non-fatal) | WARNING | internal | `"debug_logging_setup"` |
| Error with traceback | ERROR | (varies) | `"github.fetch_commits"` |

## MCP Tool Schema Impact

**None.** This feature does not modify any MCP tool input or output schemas. The existing tools (`get_today_tasks`, `get_tomorrow_tasks`, `get_repo_activity`, `render_markdown`) retain identical signatures and return values.

## Backward Compatibility

- When `DAILY_PLANNER_DEBUG` is unset or empty, behavior is identical to pre-feature builds: no log files, no debug output, no configuration changes.
- No existing configuration keys are modified or removed.
- No existing file outputs are affected.
