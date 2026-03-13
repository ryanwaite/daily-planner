"""get_repo_activity MCP tool handler — fetch activity from all configured repos."""

from __future__ import annotations

import json
import sys
from datetime import date

from daily_planner.business_day import last_business_day
from daily_planner.config.loader import load_configuration, load_repositories
from daily_planner.integrations.ado import fetch_ado_activity
from daily_planner.integrations.auth import get_ado_token, get_github_token
from daily_planner.integrations.github import fetch_github_activity


async def get_repo_activity() -> str:
    """Fetch recent activity for all configured repositories.

    Returns JSON with per-repo activity data or errors.
    """
    config = load_configuration()

    try:
        repos = load_repositories(config.repos_file)
    except FileNotFoundError as exc:
        return json.dumps({"repos": [], "error": str(exc)})

    if not repos:
        return json.dumps({"repos": [], "since_date": None, "error": "No repositories configured"})

    since = last_business_day(date.today())
    results: list[dict] = []

    for repo in repos:
        try:
            if repo.platform == "github":
                token = get_github_token(client_id="")  # Client ID from env in production
                if not token:
                    results.append(_error_result(repo, "GitHub authentication required"))
                    continue
                activities, readme = await fetch_github_activity(repo, since, token)
            elif repo.platform == "ado":
                token = get_ado_token(client_id="")  # Client ID from env in production
                if not token:
                    results.append(_error_result(repo, "ADO authentication required"))
                    continue
                activities, readme = await fetch_ado_activity(repo, since, token)
            else:
                results.append(_error_result(repo, f"Unknown platform: {repo.platform}"))
                continue

            results.append({
                "repo": _repo_dict(repo),
                "activities": [
                    {
                        "activity_type": a.activity_type,
                        "title": a.title,
                        "author": a.author,
                        "timestamp": a.timestamp.isoformat(),
                        "url": a.url,
                        "pr_state": a.pr_state,
                    }
                    for a in activities
                ],
                "readme_excerpt": readme,
                "error": None,
            })
        except Exception as exc:
            print(f"Error fetching activity for {repo.owner}/{repo.name}: {exc}", file=sys.stderr)
            results.append(_error_result(repo, str(exc)))

    return json.dumps({"repos": results, "since_date": since.isoformat()})


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


def _error_result(repo, error: str) -> dict:
    return {
        "repo": _repo_dict(repo),
        "activities": [],
        "readme_excerpt": None,
        "error": error,
    }
