# MCP Tool Contracts: Markdown Briefing Overhaul

**Feature**: 005-markdown-briefing-overhaul  
**Date**: 2026-04-26

## Tool: `render_markdown` (was `render_pdf`)

### Description

Accept all gathered briefing data and produce a markdown file.
Returns JSON with the output file path.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "repo_summaries": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "repo": {
            "type": "object",
            "properties": {
              "platform": { "type": "string", "enum": ["github", "ado"] },
              "owner": { "type": "string" },
              "name": { "type": "string" },
              "url": { "type": "string" },
              "project": { "type": ["string", "null"] }
            },
            "required": ["platform", "owner", "name", "url"]
          },
          "activities": { "type": "array" },
          "narrative": { "type": ["string", "null"] },
          "error": { "type": ["string", "null"] }
        },
        "required": ["repo"]
      },
      "description": "List of per-repo objects with repo, activities, narrative, and error fields."
    },
    "calendar_events": {
      "type": ["array", "null"],
      "description": "Calendar events for today, or null if unavailable."
    },
    "calendar_error": {
      "type": ["string", "null"],
      "description": "Error message if calendar fetch failed."
    },
    "today_tasks": {
      "type": ["array", "null"],
      "description": "Today's tasks from Things 3, or null if unavailable."
    },
    "today_error": {
      "type": ["string", "null"],
      "description": "Error message if today's tasks fetch failed."
    },
    "tomorrow_tasks": {
      "type": ["array", "null"],
      "description": "Tomorrow's tasks from Things 3, or null if unavailable."
    },
    "tomorrow_error": {
      "type": ["string", "null"],
      "description": "Error message if tomorrow's tasks fetch failed."
    },
    "action_suggestions": {
      "type": ["array", "null"],
      "items": {
        "type": "object",
        "properties": {
          "task_title": { "type": "string" },
          "suggestion": { "type": "string" }
        },
        "required": ["task_title", "suggestion"]
      },
      "description": "Up to 5 AI-generated action suggestions for unassigned tasks. Null or empty to omit section."
    },
    "output_path": {
      "type": ["string", "null"],
      "description": "Override output directory. Must resolve within user's home directory."
    }
  },
  "required": ["repo_summaries"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "markdown_path": {
      "type": "string",
      "description": "Absolute path to the generated markdown file."
    }
  },
  "required": ["markdown_path"]
}
```

### Changes from `render_pdf`

| Aspect | Old (`render_pdf`) | New (`render_markdown`) |
|--------|--------------------|------------------------|
| Tool name | `render_pdf` | `render_markdown` |
| New parameter | — | `action_suggestions: list[dict] \| None` |
| Response field | `pdf_path` | `markdown_path` |
| Response field | `pages: 2` | REMOVED |
| Output format | `.pdf` (ReportLab) | `.md` (plain text) |
| Filename | `YYYY-MM-DD dddd.pdf` | `morning-briefing-YYYY-MM-DD.md` |

---

## Tool: `get_today_tasks` (MODIFIED output)

### Description

Retrieve today's tasks from Things 3 in the application's default sort order.

### Input Schema

No parameters (unchanged).

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "tasks": {
      "type": ["array", "null"],
      "items": {
        "type": "object",
        "properties": {
          "title": { "type": "string" },
          "due_date": { "type": "string", "format": "date" },
          "sort_position": { "type": "integer" },
          "project": { "type": ["string", "null"] },
          "area": { "type": ["string", "null"] },
          "area_created": { "type": ["string", "null"], "format": "date", "description": "ISO date when the Area was created in Things 3, or null" },
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "error": { "type": ["string", "null"] }
  }
}
```

### Changes

| Aspect | Old | New |
|--------|-----|-----|
| Task object fields | title, due_date, sort_position, project, tags | title, due_date, sort_position, project, **area**, **area_created**, tags |

---

## Tool: `get_tomorrow_tasks` (MODIFIED output)

### Description

Retrieve tasks due the next business day from Things 3.

### Input Schema

`since_business_days` optional parameter (unchanged).

### Output Schema

Same as `get_today_tasks` plus `target_date` field (unchanged structure,
but task objects now include `area`).

### Changes

Same as `get_today_tasks` — adds `area` and `area_created` fields to each task object.

---

## Tool: `get_repo_activity` (UNCHANGED)

No changes to input or output schema.
