# daily-planner Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-12

## Active Technologies
- Python ≥ 3.12 (managed by UV); `from __future__ import annotations` in every module (001-morning-briefing-pdf)
- Things 3 local SQLite DB (read-only); macOS Keychain for tokens; plain-text config files (TOML + line-oriented) (001-morning-briefing-pdf)
- Python ≥ 3.12 (with `from __future__ import annotations`) + FastMCP (MCP server), httpx (HTTP client), Python `logging` stdlib module (new for this feature) (006-agent-debug-logging)
- JSONL log files written to the output directory (`settings.toml` → `[output].path`) (006-agent-debug-logging)

- Python ≥ 3.9 (targeting 3.12, managed by UV) (001-morning-briefing-pdf)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python ≥ 3.9 (targeting 3.12, managed by UV): Follow standard conventions

## Recent Changes
- 006-agent-debug-logging: Added Python ≥ 3.12 (with `from __future__ import annotations`) + FastMCP (MCP server), httpx (HTTP client), Python `logging` stdlib module (new for this feature)
- 005-markdown-briefing-overhaul: Added Python ≥ 3.12 (managed by UV); `from __future__ import annotations` in every module
- 001-morning-briefing-pdf: Added Python ≥ 3.12 (managed by UV); `from __future__ import annotations` in every module


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
