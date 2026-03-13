# Quickstart: Morning Briefing PDF Generator

## Prerequisites

- macOS (required for Things 3 database access and Keychain)
- Python ≥ 3.9
- [UV](https://docs.astral.sh/uv/) package manager
- Things 3 installed with tasks configured
- Copilot CLI installed and authenticated
- GitHub OAuth App client ID (for device-code flow)
- Azure DevOps App registration client ID (for device-code flow)
- Microsoft Work IQ MCP server configured in Copilot CLI

## Setup

```bash
# Clone and enter the project
cd daily-planner

# Install dependencies with UV
uv sync

# Create your repos config file
cp config/repos.txt.example config/repos.txt
# Edit config/repos.txt — one repo per line:
#   github:owner/repo
#   ado:org/project/repo

# (Optional) Customise font sizes and output path
cp config/settings.toml.example config/settings.toml
# Edit config/settings.toml
```

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

```bash
copilot --agent morning-briefing "Generate my morning briefing"
```

The agent will:
1. Fetch calendar events from Work IQ
2. Fetch today's and tomorrow's tasks from Things
3. Fetch repo activity from GitHub/ADO
4. Summarize repo activity using its LLM
5. Generate a two-page PDF

Output: `~/Desktop/2026-03-12 Thursday.pdf` (or configured path)

### Direct MCP server (for testing)

```bash
# Run as stdio MCP server (used by Copilot CLI automatically)
uv run python -m daily_planner.server

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
| "Things database not found" | Ensure Things 3 is installed; check `~/Library/Group Containers/` |
| "Token expired" for GitHub | Re-run; device-code flow will trigger automatically |
| "Repos config file not found" | Create `config/repos.txt` per setup instructions |
| PDF sections show "Unavailable" | Check stderr output for the specific integration error |
| Font sizes not changing | Ensure `config/settings.toml` is valid TOML syntax |
