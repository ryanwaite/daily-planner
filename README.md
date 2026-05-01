# Daily Planner

A Python MCP server that generates a markdown morning briefing, orchestrated by a Copilot CLI agent skill.

The briefing includes: Outlook calendar events (via Work IQ), today's and tomorrow's Things tasks grouped by Area, AI action suggestions for unassigned tasks, and LLM-summarised repository activity from GitHub and Azure DevOps.

## Requirements

- macOS (Things 3 database + Keychain)
- Python ≥ 3.12
- [UV](https://docs.astral.sh/uv/) package manager
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli) installed and authenticated (`gh auth login` + `gh extension install github/gh-copilot`)

## Installation

```bash
git clone <your-repo-url> daily-planner
cd daily-planner
uv sync
```

## MCP Server Setup

Copilot CLI needs to know how to start the daily-planner MCP server. Add it to your Copilot CLI MCP configuration.

### Copilot CLI (`~/.copilot/mcp-config.json`)

Create or edit `~/.copilot/mcp-config.json`:

```json
{
  "mcpServers": {
    "daily-planner": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/daily-planner", "python", "-m", "daily_planner"]
    }
  }
}
```

> **Important**: Replace `/absolute/path/to/daily-planner` with the actual absolute path to your clone of this repo (e.g. `/Users/you/Source/daily-planner`).

### VS Code (`.github/copilot/mcp.json`)

This repo also includes a VS Code MCP config at `.github/copilot/mcp.json` for use within the editor. If you run the agent from within VS Code's Copilot Chat, it will use this config automatically — just make sure you open the project folder in VS Code.

### Work IQ (optional — calendar events)

If you have access to the Microsoft Work IQ MCP server for Outlook calendar events, add it to the same `mcp-config.json`:

```json
{
  "mcpServers": {
    "daily-planner": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/daily-planner", "python", "-m", "daily_planner"]
    },
    "workiq": {
      "type": "stdio",
      "command": "...",
      "args": ["..."]
    }
  }
}
```

Without Work IQ, the briefing will still generate — the calendar section will show "Calendar data unavailable" and all other sections will work normally.

## Configuration

### `config/repos.txt`

One repository per line. Lines starting with `#` are comments.

```
github:owner/repo
ado:org/project/repo
```

For example, to track the Radius project:
```
github:radius-project/radius
```

### `config/settings.toml`

Customise the output path:

```toml
[output]
path = "~/Desktop"
repos_file = "config/repos.txt"
```

### Authentication

**GitHub** — the token is resolved in this order:
1. `GITHUB_TOKEN` environment variable
2. `gh auth token` (if [GitHub CLI](https://cli.github.com/) is installed and authenticated via `gh auth login`)
3. macOS Keychain (service: `daily-planner`, account: `github_access_token`)

**Azure DevOps** — the token is resolved in this order:
1. `ADO_TOKEN` environment variable
2. `az account get-access-token` (if [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/) is installed and authenticated via `az login`)
3. macOS Keychain (service: `daily-planner`, account: `ado_access_token`)

The easiest path: just run `gh auth login` once and you're set for GitHub repos.

## Usage

### Copilot CLI agent (primary)

```bash
copilot --agent morning-briefing --allow-all-tools "Generate my morning briefing"
```

> `--allow-all-tools` pre-approves MCP tool calls so the agent can run without interactive permission prompts.

The agent will:
1. Fetch calendar events from Work IQ (if configured)
2. Fetch today's and tomorrow's tasks from Things 3
3. Fetch repo activity from GitHub/ADO
4. Summarise repo activity using its LLM
5. Generate a two-page PDF on your Desktop

Output: `~/Desktop/2026-03-13 Friday.pdf` (or your configured path)

### Direct MCP server (for testing)

```bash
uv run python -m daily_planner
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No such agent: morning-briefing` | Ensure you're running from the repo root so Copilot CLI can find `.github/agents/` |
| Agent starts but immediately exits | Check that `~/.copilot/mcp-config.json` exists and the `--directory` path is correct |
| "Things database not found" | Ensure Things 3 is installed; check `~/Library/Group Containers/` |
| "Token expired" for GitHub | Run `gh auth login` to refresh your CLI token, or update `GITHUB_TOKEN` env var |
| "Repos config file not found" | Create `config/repos.txt` per the configuration section above |
| PDF sections show "Unavailable" | Check stderr output for the specific integration error |
| Font sizes not changing | Ensure `config/settings.toml` is valid TOML syntax |

## Debug Logging

Set `DAILY_PLANNER_DEBUG=1` to capture a detailed JSONL log of every tool invocation, API call, and error during a briefing run:

```bash
DAILY_PLANNER_DEBUG=1 uv run python -m daily_planner
```

The log file is written to the configured output directory as `debug_YYYY-MM-DD_HHMMSS_<pid>.jsonl`. Each line is a JSON object with fields:

- `timestamp` — ISO 8601
- `level` — DEBUG, INFO, ERROR
- `operation` — e.g. `get_today_tasks`, `github.fetch_commits`
- `message` — human-readable description
- `direction` — `request`, `response`, or `internal`
- `data` — structured payload (truncated at 5,000 chars)
- `duration_ms` — elapsed time for response entries
- `traceback` — full traceback on errors

Debug logging writes only to a file (never stdout) so it cannot interfere with MCP stdio transport.

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Security audit
uv run pip-audit
```

## License

See [LICENSE](LICENSE).
