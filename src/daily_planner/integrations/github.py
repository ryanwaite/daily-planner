"""GitHub API client — fetch commits, PRs, and issues since a given date."""

from __future__ import annotations

import asyncio
import base64
import logging
import re
import sys
import time
from datetime import date, datetime

import httpx

from daily_planner.models.repo import ActivityItem, Repository

API_BASE = "https://api.github.com"
TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=10)
MAX_RETRIES = 1
MAX_BODY_LEN = 300

_logger = logging.getLogger("daily_planner.debug")

# Matches GitHub cross-references like #123, owner/repo#456
_REF_PATTERN = re.compile(r"(?:[\w.-]+/[\w.-]+)?#\d+")


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
        _logger.debug(
            "Fetching commits",
            extra={
                "operation": "github.fetch_commits",
                "direction": "request",
                "data": {"repo": f"{repo.owner}/{repo.name}", "since": since_iso},
            },
        )
        t0 = time.perf_counter()
        commits = await _get_with_retry(
            client, url, params={"since": since_iso}
        )
        elapsed = (time.perf_counter() - t0) * 1000
        _logger.debug(
            "Commits response",
            extra={
                "operation": "github.fetch_commits",
                "direction": "response",
                "data": {"count": len(commits) if commits else 0},
                "duration_ms": round(elapsed, 2),
            },
        )
        if commits is not None:
            for c in commits:
                msg = c["commit"]["message"]
                title = msg.split("\n")[0]
                body = "\n".join(msg.split("\n")[1:]).strip()
                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="commit",
                    title=title,
                    author=(
                        c.get("author", {}).get("login", "unknown")
                        if c.get("author")
                        else c["commit"]["author"].get("name", "unknown")
                    ),
                    timestamp=datetime.fromisoformat(
                        c["commit"]["author"]["date"].replace("Z", "+00:00")
                    ),
                    url=c.get("html_url"),
                    body=body[:MAX_BODY_LEN] if body else None,
                    related_refs=_extract_refs(msg),
                ))

        # Pull Requests
        _logger.debug(
            "Fetching pull requests",
            extra={
                "operation": "github.fetch_prs",
                "direction": "request",
                "data": {"repo": f"{repo.owner}/{repo.name}"},
            },
        )
        t0 = time.perf_counter()
        prs = await _get_with_retry(
            client,
            f"{API_BASE}/repos/{repo.owner}/{repo.name}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 50},
        )
        elapsed = (time.perf_counter() - t0) * 1000
        _logger.debug(
            "Pull requests response",
            extra={
                "operation": "github.fetch_prs",
                "direction": "response",
                "data": {"count": len(prs) if prs else 0},
                "duration_ms": round(elapsed, 2),
            },
        )
        if prs is not None:
            for pr in prs:
                updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
                if updated.date() < since:
                    continue
                state = "merged" if pr.get("merged_at") else pr["state"]
                if state == "open":
                    state = "opened"
                pr_body = (pr.get("body") or "")[:MAX_BODY_LEN] or None
                pr_labels = [l["name"] for l in pr.get("labels", []) if isinstance(l, dict)]
                refs = _extract_refs(f"{pr.get('title', '')} {pr.get('body', '')}")
                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="pr",
                    title=pr["title"],
                    author=pr["user"]["login"],
                    timestamp=updated,
                    url=pr.get("html_url"),
                    pr_state=state,
                    body=pr_body,
                    labels=pr_labels,
                    related_refs=refs,
                ))

        # Issues (exclude PRs — GitHub includes PRs in issues endpoint)
        _logger.debug(
            "Fetching issues",
            extra={
                "operation": "github.fetch_issues",
                "direction": "request",
                "data": {"repo": f"{repo.owner}/{repo.name}", "since": since_iso},
            },
        )
        t0 = time.perf_counter()
        issues = await _get_with_retry(
            client,
            f"{API_BASE}/repos/{repo.owner}/{repo.name}/issues",
            params={"state": "all", "since": since_iso, "per_page": 50},
        )
        elapsed = (time.perf_counter() - t0) * 1000
        _logger.debug(
            "Issues response",
            extra={
                "operation": "github.fetch_issues",
                "direction": "response",
                "data": {"count": len(issues) if issues else 0},
                "duration_ms": round(elapsed, 2),
            },
        )
        if issues is not None:
            for issue in issues:
                if "pull_request" in issue:
                    continue  # Skip PRs
                issue_body = (issue.get("body") or "")[:MAX_BODY_LEN] or None
                issue_labels = [l["name"] for l in issue.get("labels", []) if isinstance(l, dict)]
                refs = _extract_refs(f"{issue.get('title', '')} {issue.get('body', '')}")
                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="issue",
                    title=issue["title"],
                    author=issue["user"]["login"],
                    timestamp=datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00")),
                    url=issue.get("html_url"),
                    body=issue_body,
                    labels=issue_labels,
                    related_refs=refs,
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
    for attempt in range(retries + 1):
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (401, 403, 404):
                _logger.error(
                    f"GitHub API returned {resp.status_code}",
                    extra={
                        "operation": "github.get",
                        "data": {"url": url, "status_code": resp.status_code},
                    },
                )
                return None  # Don't retry auth or not-found errors
        except httpx.TimeoutException:
            _logger.error(
                "GitHub API request timed out",
                exc_info=True,
                extra={"operation": "github.get", "data": {"url": url, "attempt": attempt}},
            )
        except httpx.HTTPError:
            _logger.error(
                "GitHub API request failed",
                exc_info=True,
                extra={"operation": "github.get", "data": {"url": url, "attempt": attempt}},
            )
            print("GitHub API request failed", file=sys.stderr)

        if attempt < retries:
            await asyncio.sleep(2 ** attempt)

    return None


def _extract_refs(text: str) -> list[str]:
    """Extract GitHub cross-references (#123, owner/repo#456) from text."""
    if not text:
        return []
    return list(dict.fromkeys(_REF_PATTERN.findall(text)))
