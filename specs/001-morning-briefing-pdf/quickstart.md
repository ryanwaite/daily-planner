# Quickstart: Morning Briefing PDF Generator

## Prerequisites

- macOS (required for Things 3 database access and Keychain)
- Python ≥ 3.12
- [UV](https://docs.astral.sh/uv/) package manager
- Things 3 installed with tasks configured
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli) installed and authenticated

## Setup

```bash
# Clone and enter the project
git clone <your-repo-url> daily-planner
cd daily-planner

# Install dependencies with UV
uv sync

# Edit the repos config — one repo per line (github:owner/repo or ado:org/project/repo)
nano config/repos.txt

# (Optional) Customise font sizes and output path
nano config/settings.toml
```

## MCP Server Configuration

Copilot CLI needs to know how to launch the daily-planner MCP server.
Create `~/.copilot/mcp-config.json`:

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

> **Replace** `/absolute/path/to/daily-planner` with the actual path
> to your clone (e.g. `/Users/you/Source/daily-planner`).

### Work IQ (optional — Outlook calendar)

If you have access to the Microsoft Work IQ MCP server, add it to the
same config file so the agent can fetch calendar events:

```json
{
  "mcpServers": {
    "daily-planner": { "..." : "..." },
    "workiq": {
      "type": "stdio",
      "command": "...",
      "args": ["..."]
    }
  }
}
```

Without Work IQ, everything else works — the calendar section
will simply show "Calendar data unavailable".

### VS Code

For use within VS Code's Copilot Chat, the repo includes
`.github/copilot/mcp.json` which is picked up automatically
when you open the project folder.

## First-Run Authentication

GitHub and ADO use OAuth2 device-code flow. On first run (or when
tokens expire), the MCP server will prompt you to authenticate:

```
GitHub: Visit https://github.com/login/device and enter code: ABCD-1234
ADO: Visit https://microsoft.com/devicelogin and enter code: EFGH5678
```

Tokens are stored in the macOS Keychain under the service name
`daily-planner`.

## Usage

### Via Copilot CLI agent (primary)

Run from the repo root directory so Copilot CLI can find the
`.github/agents/` folder:

```bash
cd /path/to/daily-planner
copilot --agent morning-briefing "Generate my morning briefing"
```

The agent will:
1. Fetch calendar events from Work IQ (if configured)
2. Fetch today's and tomorrow's tasks from Things 3
3. Fetch repo activity from GitHub/ADO
4. Summarise repo activity using its LLM
5. Generate a two-page PDF

Output: `~/Desktop/2026-03-13 Friday.pdf` (or configured path)

### Direct MCP server (for testing)

```bash
# Run as stdio MCP server (used by Copilot CLI automatically)
uv run python -m daily_planner

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/
```

## Configuration Files

### `config/repos.txt`

```text
github:octocat/hello-world
github:myorg/backend-api
ado:mycompany/MyProject/web-frontend
```

### `config/settings.toml`

```toml
[page_one]
font_size = 9.0

[page_two]
font_size = 8.0

[output]
path = "~/Desktop"
repos_file = "config/repos.txt"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No such agent: morning-briefing` | Make sure you run `copilot` from the repo root so it can find `.github/agents/` |
| Agent starts but immediately exits | Check that `~/.copilot/mcp-config.json` exists with the correct absolute `--directory` path |
| "Things database not found" | Ensure Things 3 is installed; check `~/Library/Group Containers/` |
| "Token expired" for GitHub | Re-run; device-code flow will trigger automatically |
| "Repos config file not found" | Create `config/repos.txt` per setup instructions |
| PDF sections show "Unavailable" | Check stderr output for the specific integration error |
| Font sizes not changing | Ensure `config/settings.toml` is valid TOML syntax |
