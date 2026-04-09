"""get_repo_activity MCP tool handler — fetch activity from all configured repos."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from daily_planner.business_day import last_business_day, n_business_days_back
from daily_planner.config.loader import load_configuration, load_repositories
from daily_planner.integrations.ado import fetch_ado_activity
from daily_planner.integrations.auth import get_ado_token, get_github_token
from daily_planner.integrations.github import fetch_github_activity

_ACTIVITY_DIR = Path.cwd() / ".tmp" / "repo_activity"


async def get_repo_activity(since_business_days: int | None = None) -> str:
    """Fetch recent activity for all configured repositories.

    Per-repo JSON files are written to .tmp/repo_activity/. The tool
    response is a lightweight summary (~1-2 KB) with counts and file paths.

    Args:
        since_business_days: Number of business days to look back.
            Defaults to 1 (the last business day).

    Returns JSON summary with per-repo counts, file paths, and any errors.
    """
    config = load_configuration()

    try:
        repos = load_repositories(config.repos_file)
    except FileNotFoundError as exc:
        return json.dumps({"repos": [], "error": str(exc)})

    if not repos:
        return json.dumps({"repos": [], "since_date": None, "error": "No repositories configured"})

    if since_business_days is not None and since_business_days > 1:
        since = n_business_days_back(date.today(), since_business_days)
    else:
        since = last_business_day(date.today())

    activity_dir = _ACTIVITY_DIR
    activity_dir.mkdir(parents=True, exist_ok=True)

    summary_entries: list[dict] = []

    github_token = get_github_token()
    ado_token = get_ado_token()

    for repo in repos:
        try:
            if repo.platform == "github":
                if not github_token:
                    summary_entries.append(_error_summary(repo, "GitHub authentication required"))
                    continue
                activities, readme = await fetch_github_activity(
                    repo, since, github_token,
                )
            elif repo.platform == "ado":
                if not ado_token:
                    summary_entries.append(_error_summary(repo, "ADO authentication required"))
                    continue
                activities, readme = await fetch_ado_activity(
                    repo, since, ado_token,
                )
            else:
                summary_entries.append(_error_summary(repo, f"Unknown platform: {repo.platform}"))
                continue

            file_name = _repo_file_name(repo)
            file_path = activity_dir / file_name
            repo_data = {
                "repo": _repo_dict(repo),
                "activities": [
                    {
                        "activity_type": a.activity_type,
                        "title": a.title,
                        "author": a.author,
                        "timestamp": a.timestamp.isoformat(),
                        "url": a.url,
                        "pr_state": a.pr_state,
                        "body": a.body,
                        "labels": a.labels,
                        "related_refs": a.related_refs,
                    }
                    for a in activities
                ],
                "readme_excerpt": readme,
                "error": None,
            }
            file_path.write_text(json.dumps(repo_data, indent=2), encoding="utf-8")

            relative_path = str(Path(".tmp") / "repo_activity" / file_name)
            summary_entries.append({
                "name": f"{repo.owner}/{repo.name}",
                "platform": repo.platform,
                "commits": sum(1 for a in activities if a.activity_type == "commit"),
                "prs": sum(1 for a in activities if a.activity_type == "pr"),
                "issues": sum(1 for a in activities if a.activity_type == "issue"),
                "file": relative_path,
                "error": None,
            })
        except Exception:
            print(f"Error fetching activity for {repo.owner}/{repo.name}", file=sys.stderr)
            summary_entries.append(_error_summary(repo, "Failed to fetch activity"))

    return json.dumps({
        "since_date": since.isoformat(),
        "activity_dir": str(Path(".tmp") / "repo_activity"),
        "repos": summary_entries,
    })


def _repo_dict(repo) -> dict:
    d = {
        "platform": repo.platform,
        "owner": repo.owner,
        "name": repo.name,
        "url": repo.url,
    }
    if repo.project:
        d["project"] = repo.project
    return d


def _repo_file_name(repo) -> str:
    """Build the per-repo JSON file name from platform/owner/name."""
    parts = [repo.platform, repo.owner, repo.name]
    raw = "_".join(parts)
    return raw.replace("/", "_") + ".json"


def _error_summary(repo, error: str) -> dict:
    return {
        "name": f"{repo.owner}/{repo.name}",
        "platform": repo.platform,
        "commits": 0,
        "prs": 0,
        "issues": 0,
        "file": None,
        "error": error,
    }
