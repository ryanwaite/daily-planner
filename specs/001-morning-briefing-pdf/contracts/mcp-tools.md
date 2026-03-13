# MCP Tool Contracts: Daily Planner Server

**Date**: 2026-03-12
**Transport**: stdio (JSON-RPC 2.0 over stdin/stdout)
**Server name**: `daily-planner`

---

## Tool: `get_today_tasks`

**Description**: Retrieve today's tasks from Things 3 in the
application's default sort order.

### Input Schema

```json
{
  "type": "object",
  "properties": {},
  "additionalProperties": false
}
```

No parameters required — the tool reads today's date from the
system clock and queries the Things database.

### Output (success)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"tasks\": [{\"title\": \"Review PR #42\", \"due_date\": \"2026-03-12\", \"sort_position\": 1, \"project\": \"daily-planner\", \"tags\": [\"work\"]}, ...]}"
    }
  ]
}
```

### Output (error — Things unreachable)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"tasks\": null, \"error\": \"Things database not found or inaccessible\"}"
    }
  ],
  "isError": true
}
```

---

## Tool: `get_tomorrow_tasks`

**Description**: Retrieve tasks due the next business day from
Things 3. Friday → Monday; otherwise next calendar day.

### Input Schema

```json
{
  "type": "object",
  "properties": {},
  "additionalProperties": false
}
```

### Output (success)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"tasks\": [{\"title\": \"Prepare sprint demo\", \"due_date\": \"2026-03-13\", \"sort_position\": 1, \"project\": null, \"tags\": []}], \"target_date\": \"2026-03-13\"}"
    }
  ]
}
```

### Output (error)

Same error shape as `get_today_tasks`.

---

## Tool: `get_repo_activity`

**Description**: Fetch recent activity (commits, PRs, issues/work
items) since the last business day for all configured repositories.
Returns raw structured data for the agent to summarize.

### Input Schema

```json
{
  "type": "object",
  "properties": {},
  "additionalProperties": false
}
```

Reads config from `config/repos.txt` and `config/settings.toml`.
Uses tokens from macOS Keychain.

### Output (success)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"repos\": [{\"repo\": {\"platform\": \"github\", \"owner\": \"octocat\", \"name\": \"hello-world\", \"url\": \"https://github.com/octocat/hello-world\"}, \"activities\": [{\"activity_type\": \"pr\", \"title\": \"Add README\", \"author\": \"octocat\", \"timestamp\": \"2026-03-11T14:30:00Z\", \"url\": \"https://github.com/octocat/hello-world/pull/1\", \"pr_state\": \"merged\"}], \"readme_excerpt\": \"Hello World is a sample repo...\", \"error\": null}, ...], \"since_date\": \"2026-03-11\"}"
    }
  ]
}
```

### Output (partial failure)

Repos that are unreachable still appear in the list with
`activities: []` and a populated `error` field. The tool itself
does NOT return `isError: true` for partial failures — only for
total failure (e.g., config file missing).

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"repos\": [{\"repo\": {\"platform\": \"ado\", \"owner\": \"myorg\", \"project\": \"myproject\", \"name\": \"backend\", \"url\": \"...\"}, \"activities\": [], \"readme_excerpt\": null, \"error\": \"HTTP 401: Token expired\"}], \"since_date\": \"2026-03-11\"}"
    }
  ]
}
```

### Output (total failure — config missing)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"repos\": [], \"error\": \"Repos config file not found at config/repos.txt\"}"
    }
  ],
  "isError": true
}
```

---

## Tool: `render_pdf`

**Description**: Accept all gathered briefing data (calendar events,
tasks, repo activity with optional LLM summaries) and produce a
two-page US Letter PDF.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "calendar_events": {
      "type": ["array", "null"],
      "description": "Today's calendar events from Work IQ, or null if unavailable",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "start_time": {"type": "string", "format": "date-time"},
          "end_time": {"type": "string", "format": "date-time"},
          "location": {"type": ["string", "null"]},
          "is_all_day": {"type": "boolean"}
        },
        "required": ["title", "start_time", "end_time", "is_all_day"]
      }
    },
    "calendar_error": {
      "type": ["string", "null"],
      "description": "Error message if calendar data is unavailable"
    },
    "today_tasks": {
      "type": ["array", "null"],
      "description": "Today's tasks (from get_today_tasks), or null if unavailable"
    },
    "today_error": {
      "type": ["string", "null"]
    },
    "tomorrow_tasks": {
      "type": ["array", "null"],
      "description": "Tomorrow's tasks (from get_tomorrow_tasks), or null if unavailable"
    },
    "tomorrow_error": {
      "type": ["string", "null"]
    },
    "repo_summaries": {
      "type": "array",
      "description": "Per-repo activity with optional LLM narrative",
      "items": {
        "type": "object",
        "properties": {
          "repo": {
            "type": "object",
            "properties": {
              "platform": {"type": "string"},
              "owner": {"type": "string"},
              "name": {"type": "string"},
              "url": {"type": "string"}
            }
          },
          "activities": {"type": "array"},
          "narrative": {"type": ["string", "null"]},
          "error": {"type": ["string", "null"]}
        }
      }
    },
    "output_path": {
      "type": ["string", "null"],
      "description": "Override output directory (default: from config or ~/Desktop)"
    }
  },
  "required": ["repo_summaries"]
}
```

### Output (success)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"pdf_path\": \"/Users/user/Desktop/2026-03-12 Thursday.pdf\", \"pages\": 2}"
    }
  ]
}
```

### Output (error)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"Failed to write PDF: Permission denied\"}"
    }
  ],
  "isError": true
}
```

---

## Agent Skill Contract

**File**: `.github/agents/morning-briefing.agent.md`

**Orchestration flow** (defined in the agent skill instructions):

1. Call Work IQ MCP server → get calendar events for today
2. Call `daily-planner` → `get_today_tasks`
3. Call `daily-planner` → `get_tomorrow_tasks`
4. Call `daily-planner` → `get_repo_activity`
5. For each repo with activities: use LLM to generate narrative
   summary from raw activities + readme excerpt
6. Call `daily-planner` → `render_pdf` with all assembled data
7. Report the output PDF path to the user
