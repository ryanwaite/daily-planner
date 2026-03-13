"""GitHub API client — fetch commits, PRs, and issues since a given date."""

from __future__ import annotations

import base64
import sys
from datetime import date, datetime

import httpx

from daily_planner.models.repo import ActivityItem, Repository

API_BASE = "https://api.github.com"
TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=10)
MAX_RETRIES = 1


async def fetch_github_activity(
    repo: Repository,
    since: date,
    token: str,
) -> tuple[list[ActivityItem], str | None]:
    """Fetch commits, PRs, and issues from a GitHub repo since a given date.

    Returns (activities, readme_excerpt). On error, returns ([], None).
    """
    since_iso = f"{since.isoformat()}T00:00:00Z"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    activities: list[ActivityItem] = []
    readme_excerpt: str | None = None

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as client:
        # Commits
        url = f"{API_BASE}/repos/{repo.owner}/{repo.name}/commits"
        commits = await _get_with_retry(
            client, url, params={"since": since_iso}
        )
        if commits is not None:
            for c in commits:
                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="commit",
                    title=c["commit"]["message"].split("\n")[0],
                    author=(
                        c.get("author", {}).get("login", "unknown")
                        if c.get("author")
                        else c["commit"]["author"].get("name", "unknown")
                    ),
                    timestamp=datetime.fromisoformat(
                        c["commit"]["author"]["date"].replace("Z", "+00:00")
                    ),
                    url=c.get("html_url"),
                ))

        # Pull Requests
        prs = await _get_with_retry(
            client,
            f"{API_BASE}/repos/{repo.owner}/{repo.name}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 50},
        )
        if prs is not None:
            for pr in prs:
                updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
                if updated.date() < since:
                    continue
                state = "merged" if pr.get("merged_at") else pr["state"]
                if state == "open":
                    state = "opened"
                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="pr",
                    title=pr["title"],
                    author=pr["user"]["login"],
                    timestamp=updated,
                    url=pr.get("html_url"),
                    pr_state=state,
                ))

        # Issues (exclude PRs — GitHub includes PRs in issues endpoint)
        issues = await _get_with_retry(
            client,
            f"{API_BASE}/repos/{repo.owner}/{repo.name}/issues",
            params={"state": "all", "since": since_iso, "per_page": 50},
        )
        if issues is not None:
            for issue in issues:
                if "pull_request" in issue:
                    continue  # Skip PRs
                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="issue",
                    title=issue["title"],
                    author=issue["user"]["login"],
                    timestamp=datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00")),
                    url=issue.get("html_url"),
                ))

        # README excerpt
        readme_resp = await _get_with_retry(
            client, f"{API_BASE}/repos/{repo.owner}/{repo.name}/readme"
        )
        if readme_resp is not None and isinstance(readme_resp, dict):
            try:
                raw = readme_resp.get("content", "")
                content = base64.b64decode(raw).decode(
                    "utf-8", errors="replace"
                )
                readme_excerpt = content[:500]
            except Exception:
                pass

    return activities, readme_excerpt


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
    retries: int = MAX_RETRIES,
) -> list | dict | None:
    """GET with single retry and exponential backoff."""
    import asyncio

    for attempt in range(retries + 1):
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (401, 403, 404):
                return None  # Don't retry auth or not-found errors
        except httpx.TimeoutException:
            pass
        except httpx.HTTPError as exc:
            print(f"GitHub API error for {url}: {exc}", file=sys.stderr)

        if attempt < retries:
            await asyncio.sleep(2 ** attempt)

    return None
