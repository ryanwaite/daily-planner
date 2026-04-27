# Quickstart: Markdown Briefing Overhaul

**Feature**: 005-markdown-briefing-overhaul  
**Date**: 2026-04-26

## What Changed

The morning briefing now produces a **markdown file** instead of a PDF.
Tasks are grouped by their Things Area, unassigned tasks get AI action
suggestions, and repository narratives have better visual separation.

## Running the Briefing

```bash
# Start MCP server locally (stdio transport)
uv run python -m daily_planner

# Or invoke via the Copilot agent
# The morning-briefing agent calls the MCP tools automatically
```

## Configuration

Edit `config/settings.toml`:

```toml
# Daily Planner – Settings

[output]
path = "~/Desktop"              # Directory where the markdown file is saved
repos_file = "config/repos.txt"
```

The `[page_one]` and `[page_two]` sections from the old PDF config
are no longer used and can be removed.

## Output File

The briefing is saved as `morning-briefing-YYYY-MM-DD.md` in the
configured output directory. Running multiple times on the same day
overwrites the file silently.

## Markdown Structure

```markdown
# Morning Briefing — Saturday, April 26, 2026

## Calendar Events
- 9:00 AM – 10:00 AM: Team Standup
- ...

## Today Tasks

### No Area
- [ ] Unassigned task 1
- [ ] Unassigned task 2

### Personal
- [ ] Buy groceries

### Work
- [ ] Review PR #142

## Tomorrow Tasks
(same grouped structure)

## Action Suggestions

> **Unassigned task 1**: Search for a local plumber and request a quote.

> **Unassigned task 2**: Break this into three sub-tasks and schedule
> the first one for tomorrow.

## Repository Activity

### radius-project/radius

**Authentication overhaul** — ...

**CI pipeline reliability** — ...

### drasi-project/drasi-server
...
```

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Lint with auto-fix
uv run ruff check --fix src/ tests/
```

## Key Files

| File | Purpose |
|------|---------|
| `src/daily_planner/server.py` | MCP tool registration (`render_markdown`) |
| `src/daily_planner/tools/render_markdown.py` | Tool handler — assembles data, calls renderer |
| `src/daily_planner/markdown/renderer.py` | Markdown string builder |
| `src/daily_planner/tools/tasks.py` | Task tools (now include `area` field) |
| `src/daily_planner/models/config.py` | Configuration (simplified, no font sizes) |
| `src/daily_planner/models/task.py` | Task + ActionSuggestion dataclasses |
| `.github/agents/morning-briefing.agent.md` | Agent instructions (updated workflow) |
| `config/settings.toml` | Output path configuration |
