# Daily Planner

A Python MCP server that generates a printable two-page PDF morning briefing, orchestrated by a Copilot CLI agent skill.

**Page 1** — three-column layout: Outlook calendar (via Work IQ), today's Things tasks, tomorrow's tasks + note space.
**Page 2** — two-column layout: LLM-summarised repository activity from GitHub and Azure DevOps.

## Requirements

- macOS (Things 3 database + Keychain)
- Python ≥ 3.12
- [UV](https://docs.astral.sh/uv/) package manager

## Installation

```bash
cd daily-planner
uv sync
```

## Configuration

### `config/settings.toml`

Customise font sizes and output path:

```toml
[page_one]
font_size = 9.0

[page_two]
font_size = 8.0

[output]
path = "~/Desktop"
repos_file = "config/repos.txt"
```

### `config/repos.txt`

One repository per line. Lines starting with `#` are comments.

```
github:owner/repo
ado:org/project/repo
```

### Keychain

GitHub and Azure DevOps tokens are stored in the macOS Keychain under the service name `daily-planner`. On first run the MCP server initiates an OAuth2 device-code flow — follow the on-screen instructions to authenticate.

## Usage

### Copilot CLI agent (primary)

```bash
copilot --agent morning-briefing "Generate my morning briefing"
```

### Direct MCP server

```bash
uv run python -m daily_planner
```

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
