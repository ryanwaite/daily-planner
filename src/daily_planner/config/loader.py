"""Config file reader — settings.toml and repos.txt parser."""

from __future__ import annotations

import sys
from pathlib import Path

import tomli

from daily_planner.models.config import Configuration
from daily_planner.models.repo import Repository


def load_configuration(settings_path: str = "config/settings.toml") -> Configuration:
    """Load Configuration from a TOML file. Returns defaults if file is missing."""
    p = Path(settings_path)
    if not p.exists():
        return Configuration()

    with p.open("rb") as f:
        data = tomli.load(f)

    output = data.get("output", {})

    return Configuration(
        output_path=output.get("path", "~/Desktop"),
        repos_file=output.get("repos_file", "config/repos.txt"),
    )


def load_repositories(repos_path: str | Path) -> list[Repository]:
    """Parse repos.txt into a list of Repository objects.

    Expected line format:
        github:owner/repo
        ado:org/project/repo

    Invalid lines are skipped with a warning to stderr.
    Raises FileNotFoundError if the repos file does not exist.
    """
    p = Path(repos_path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Repos config file not found at {repos_path}")

    repos: list[Repository] = []
    for line_num, raw_line in enumerate(p.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            repo = _parse_repo_line(line)
            repos.append(repo)
        except ValueError as exc:
            print(f"Warning: {repos_path}:{line_num}: {exc} — skipping", file=sys.stderr)
    return repos


def _parse_repo_line(line: str) -> Repository:
    """Parse a single repo config line into a Repository."""
    if ":" not in line:
        raise ValueError(f"Invalid repo format (missing platform prefix): '{line}'")

    platform, _, path = line.partition(":")
    platform = platform.strip().lower()

    if platform == "github":
        parts = path.strip().split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError(f"Invalid GitHub repo format: '{line}' (expected github:owner/repo)")
        owner, name = parts
        return Repository(
            platform="github",
            owner=owner,
            name=name,
            url=f"https://github.com/{owner}/{name}",
        )
    elif platform == "ado":
        parts = path.strip().split("/")
        if len(parts) != 3 or not all(parts):
            raise ValueError(
                f"Invalid ADO repo format: '{line}' (expected ado:org/project/repo)"
            )
        org, project, name = parts
        return Repository(
            platform="ado",
            owner=org,
            project=project,
            name=name,
            url=f"https://dev.azure.com/{org}/{project}/_git/{name}",
        )
    else:
        raise ValueError(f"Unknown platform '{platform}' in '{line}'")
