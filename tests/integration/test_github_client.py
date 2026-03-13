"""Integration tests for GitHub API client — mock HTTP responses with respx."""

from datetime import date

import httpx
import pytest
import respx

from daily_planner.integrations.github import fetch_github_activity
from daily_planner.models.repo import Repository


@pytest.fixture
def github_repo():
    return Repository(
        platform="github",
        owner="octocat",
        name="hello-world",
        url="https://github.com/octocat/hello-world",
    )


class TestGitHubClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_fetches_commits(self, github_repo):
        respx.get("https://api.github.com/repos/octocat/hello-world/commits").mock(
            return_value=httpx.Response(200, json=[
                {
                    "sha": "abc123",
                    "commit": {"message": "Fix bug", "author": {"date": "2026-03-12T10:00:00Z"}},
                    "author": {"login": "alice"},
                    "html_url": "https://github.com/octocat/hello-world/commit/abc123",
                }
            ])
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/pulls").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/issues").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/readme").mock(
            return_value=httpx.Response(200, json={"content": "SGVsbG8=", "encoding": "base64"})
        )

        activities, readme = await fetch_github_activity(
            github_repo, date(2026, 3, 12), token="test-token"
        )
        assert len(activities) == 1
        assert activities[0].activity_type == "commit"
        assert activities[0].author == "alice"

    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_api_error(self, github_repo):
        respx.get("https://api.github.com/repos/octocat/hello-world/commits").mock(
            return_value=httpx.Response(401, json={"message": "Bad credentials"})
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/pulls").mock(
            return_value=httpx.Response(401)
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/issues").mock(
            return_value=httpx.Response(401)
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/readme").mock(
            return_value=httpx.Response(404)
        )

        activities, readme = await fetch_github_activity(
            github_repo, date(2026, 3, 12), token="bad-token"
        )
        assert activities == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_parses_prs(self, github_repo):
        respx.get("https://api.github.com/repos/octocat/hello-world/commits").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/pulls").mock(
            return_value=httpx.Response(200, json=[
                {
                    "title": "Add feature",
                    "user": {"login": "bob"},
                    "updated_at": "2026-03-12T15:00:00Z",
                    "html_url": "https://github.com/octocat/hello-world/pull/1",
                    "state": "open",
                    "merged_at": None,
                }
            ])
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/issues").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get("https://api.github.com/repos/octocat/hello-world/readme").mock(
            return_value=httpx.Response(200, json={"content": "SGVsbG8=", "encoding": "base64"})
        )

        activities, _ = await fetch_github_activity(
            github_repo, date(2026, 3, 12), token="test-token"
        )
        assert len(activities) == 1
        assert activities[0].activity_type == "pr"
        assert activities[0].pr_state == "opened"
