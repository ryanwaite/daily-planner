"""Azure DevOps API client — fetch commits, PRs, and work items since a given date."""

from __future__ import annotations

import logging
import sys
import time
from datetime import date, datetime

import httpx

from daily_planner.models.repo import ActivityItem, Repository

API_VERSION = "7.1"
TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=10)
MAX_RETRIES = 1

_logger = logging.getLogger("daily_planner.debug")


async def fetch_ado_activity(
    repo: Repository,
    since: date,
    token: str,
) -> tuple[list[ActivityItem], str | None]:
    """Fetch commits, PRs, and work items from an ADO repo since a given date.

    Returns (activities, repo_description). On error, returns ([], None).
    """
    if not isinstance(since, date):
        raise TypeError(f"since must be a date object, got {type(since).__name__}")

    base = f"https://dev.azure.com/{repo.owner}/{repo.project}/_apis"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    activities: list[ActivityItem] = []
    description: str | None = None

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as client:
        # Commits
        _logger.debug(
            "Fetching ADO commits",
            extra={
                "operation": "ado.fetch_commits",
                "direction": "request",
                "data": {"repo": f"{repo.owner}/{repo.name}", "since": since.isoformat()},
            },
        )
        t0 = time.perf_counter()
        commits = await _get_with_retry(
            client,
            f"{base}/git/repositories/{repo.name}/commits",
            params={"searchCriteria.fromDate": since.isoformat(), "api-version": API_VERSION},
        )
        elapsed = (time.perf_counter() - t0) * 1000
        _logger.debug(
            "ADO commits response",
            extra={
                "operation": "ado.fetch_commits",
                "direction": "response",
                "data": {"count": len(commits.get("value", [])) if commits else 0},
                "duration_ms": round(elapsed, 2),
            },
        )
        if commits is not None:
            for c in commits.get("value", []):
                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="commit",
                    title=c.get("comment", "No message").split("\n")[0],
                    author=c.get("author", {}).get("name", "unknown"),
                    timestamp=datetime.fromisoformat(
                        c["author"]["date"].replace("Z", "+00:00")
                    ),
                    url=c.get("remoteUrl"),
                ))

        # Pull Requests
        _logger.debug(
            "Fetching ADO pull requests",
            extra={
                "operation": "ado.fetch_prs",
                "direction": "request",
                "data": {"repo": f"{repo.owner}/{repo.name}"},
            },
        )
        t0 = time.perf_counter()
        prs = await _get_with_retry(
            client,
            f"{base}/git/repositories/{repo.name}/pullrequests",
            params={"searchCriteria.status": "all", "api-version": API_VERSION},
        )
        elapsed = (time.perf_counter() - t0) * 1000
        _logger.debug(
            "ADO pull requests response",
            extra={
                "operation": "ado.fetch_prs",
                "direction": "response",
                "data": {"count": len(prs.get("value", [])) if prs else 0},
                "duration_ms": round(elapsed, 2),
            },
        )
        if prs is not None:
            for pr in prs.get("value", []):
                # Determine PR date — use closedDate if available, fallback to creationDate
                date_str = pr.get("closedDate") or pr.get("creationDate", "")
                if not date_str:
                    continue
                pr_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if pr_time.date() < since:
                    continue

                status = pr.get("status", "active")
                state_map = {"completed": "merged", "abandoned": "closed", "active": "opened"}
                pr_state = state_map.get(status, "opened")

                activities.append(ActivityItem(
                    repo=repo,
                    activity_type="pr",
                    title=pr.get("title", "Untitled PR"),
                    author=pr.get("createdBy", {}).get("displayName", "unknown"),
                    timestamp=pr_time,
                    url=pr.get("url"),
                    pr_state=pr_state,
                ))

        # Work Items (via WIQL)
        # Safety: since is type-checked as date above; isoformat() produces YYYY-MM-DD only
        since_str = since.isoformat()
        wiql_query = (
            f"SELECT [System.Id], [System.Title], [System.ChangedBy], "
            f"[System.ChangedDate], [System.WorkItemType] "
            f"FROM WorkItems "
            f"WHERE [System.ChangedDate] >= '{since_str}' "
            f"ORDER BY [System.ChangedDate] DESC"
        )
        _logger.debug(
            "Fetching ADO work items via WIQL",
            extra={
                "operation": "ado.fetch_work_items",
                "direction": "request",
                "data": {"repo": f"{repo.owner}/{repo.name}", "since": since_str},
            },
        )
        t0 = time.perf_counter()
        wiql_result = await _post_with_retry(
            client,
            f"{base}/wit/wiql",
            params={"api-version": API_VERSION},
            json_body={"query": wiql_query},
        )
        elapsed = (time.perf_counter() - t0) * 1000
        _logger.debug(
            "ADO work items response",
            extra={
                "operation": "ado.fetch_work_items",
                "direction": "response",
                "data": {
                    "count": len(wiql_result.get("workItems", [])) if wiql_result else 0,
                },
                "duration_ms": round(elapsed, 2),
            },
        )
        if wiql_result is not None:
            work_items = wiql_result.get("workItems", [])
            # Fetch details for first 50 work items
            for wi in work_items[:50]:
                wi_detail = await _get_with_retry(
                    client,
                    f"https://dev.azure.com/{repo.owner}/{repo.project}/_apis/wit/workitems/{wi['id']}",
                    params={"api-version": API_VERSION},
                )
                if wi_detail and "fields" in wi_detail:
                    fields = wi_detail["fields"]
                    changed_date_str = fields.get("System.ChangedDate", "")
                    try:
                        ts = datetime.fromisoformat(changed_date_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        ts = datetime.now()
                    activities.append(ActivityItem(
                        repo=repo,
                        activity_type="issue",
                        title=fields.get("System.Title", "Untitled"),
                        author=fields.get("System.ChangedBy", "unknown"),
                        timestamp=ts,
                        url=wi_detail.get("_links", {}).get("html", {}).get("href"),
                    ))

    return activities, description


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
    retries: int = MAX_RETRIES,
) -> dict | None:
    """GET with single retry and exponential backoff."""
    import asyncio

    for attempt in range(retries + 1):
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (401, 403, 404):
                _logger.error(
                    f"ADO API returned {resp.status_code}",
                    extra={
                        "operation": "ado.get",
                        "data": {"url": url, "status_code": resp.status_code},
                    },
                )
                return None
        except httpx.TimeoutException:
            _logger.error(
                "ADO API request timed out",
                exc_info=True,
                extra={
                    "operation": "ado.get",
                    "data": {"url": url, "attempt": attempt},
                },
            )
        except httpx.HTTPError:
            _logger.error(
                "ADO API request failed",
                exc_info=True,
                extra={
                    "operation": "ado.get",
                    "data": {"url": url, "attempt": attempt},
                },
            )
            print("ADO API request failed", file=sys.stderr)

        if attempt < retries:
            await asyncio.sleep(2 ** attempt)

    return None


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
    json_body: dict | None = None,
    retries: int = MAX_RETRIES,
) -> dict | None:
    """POST with single retry and exponential backoff."""
    import asyncio

    for attempt in range(retries + 1):
        try:
            resp = await client.post(url, params=params, json=json_body)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (401, 403, 404):
                _logger.error(
                    f"ADO API POST returned {resp.status_code}",
                    extra={
                        "operation": "ado.post",
                        "data": {"url": url, "status_code": resp.status_code},
                    },
                )
                return None
        except httpx.TimeoutException:
            _logger.error(
                "ADO API POST timed out",
                exc_info=True,
                extra={
                    "operation": "ado.post",
                    "data": {"url": url, "attempt": attempt},
                },
            )
        except httpx.HTTPError:
            _logger.error(
                "ADO API POST failed",
                exc_info=True,
                extra={
                    "operation": "ado.post",
                    "data": {"url": url, "attempt": attempt},
                },
            )
            print("ADO API request failed", file=sys.stderr)

        if attempt < retries:
            await asyncio.sleep(2 ** attempt)

    return None
