# Quickstart: Agent Debug Logging

## Enable Debug Logging

Set the environment variable before running the MCP server:

```bash
DAILY_PLANNER_DEBUG=1 uv run python -m daily_planner
```

Or export it for the session:

```bash
export DAILY_PLANNER_DEBUG=1
uv run python -m daily_planner
```

## Find the Log File

After a briefing run, look for a `.jsonl` file in your configured output directory (same location as the markdown briefing):

```bash
ls ~/Desktop/debug_*.jsonl
```

The file name includes the date, time, and process ID:
```
debug_2026-04-26_083012_48291.jsonl
```

## Read the Log

Each line is a standalone JSON object. Common ways to read it:

```bash
# View the full log
cat ~/Desktop/debug_2026-04-26_083012_48291.jsonl

# Pretty-print with jq
cat ~/Desktop/debug_2026-04-26_083012_48291.jsonl | jq .

# Filter for errors only
cat ~/Desktop/debug_2026-04-26_083012_48291.jsonl | jq 'select(.level == "ERROR")'

# Find all entries for a specific tool
grep '"get_repo_activity"' ~/Desktop/debug_2026-04-26_083012_48291.jsonl | jq .

# Find all API responses with their status
cat ~/Desktop/debug_2026-04-26_083012_48291.jsonl | jq 'select(.direction == "response")'
```

## Disable Debug Logging

Unset the environment variable or omit it:

```bash
unset DAILY_PLANNER_DEBUG
uv run python -m daily_planner
```

No log file will be created.
