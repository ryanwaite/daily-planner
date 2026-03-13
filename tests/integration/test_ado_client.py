"""Integration tests for ADO API client — mock HTTP responses with respx."""

from datetime import date

import httpx
import pytest
import respx

from daily_planner.integrations.ado import fetch_ado_activity
from daily_planner.models.repo import Repository


@pytest.fixture
def ado_repo():
    return Repository(
        platform="ado",
        owner="myorg",
        project="myproject",
        name="backend",
        url="https://dev.azure.com/myorg/myproject/_git/backend",
    )


class TestADOClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_fetches_commits(self, ado_repo):
        base = "https://dev.azure.com/myorg/myproject/_apis"
        respx.get(f"{base}/git/repositories/backend/commits").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {
                        "commitId": "def456",
                        "comment": "Update config",
                        "author": {"name": "carol", "date": "2026-03-12T11:00:00Z"},
                        "remoteUrl": "https://dev.azure.com/myorg/myproject/_git/backend/commit/def456",
                    }
                ]
            })
        )
        respx.get(f"{base}/git/repositories/backend/pullrequests").mock(
            return_value=httpx.Response(200, json={"value": []})
        )
        respx.post(f"{base}/wit/wiql").mock(
            return_value=httpx.Response(200, json={"workItems": []})
        )

        activities, description = await fetch_ado_activity(
            ado_repo, date(2026, 3, 12), token="test-token"
        )
        assert len(activities) == 1
        assert activities[0].activity_type == "commit"
        assert activities[0].author == "carol"

    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_api_error(self, ado_repo):
        base = "https://dev.azure.com/myorg/myproject/_apis"
        respx.get(f"{base}/git/repositories/backend/commits").mock(
            return_value=httpx.Response(401)
        )
        respx.get(f"{base}/git/repositories/backend/pullrequests").mock(
            return_value=httpx.Response(401)
        )
        respx.post(f"{base}/wit/wiql").mock(
            return_value=httpx.Response(401)
        )

        activities, description = await fetch_ado_activity(
            ado_repo, date(2026, 3, 12), token="bad-token"
        )
        assert activities == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetches_prs(self, ado_repo):
        base = "https://dev.azure.com/myorg/myproject/_apis"
        respx.get(f"{base}/git/repositories/backend/commits").mock(
            return_value=httpx.Response(200, json={"value": []})
        )
        respx.get(f"{base}/git/repositories/backend/pullrequests").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {
                        "title": "Refactor auth",
                        "createdBy": {"displayName": "dave"},
                        "closedDate": "2026-03-12T16:00:00Z",
                        "url": "https://dev.azure.com/myorg/myproject/_git/backend/pullrequest/5",
                        "status": "completed",
                    }
                ]
            })
        )
        respx.post(f"{base}/wit/wiql").mock(
            return_value=httpx.Response(200, json={"workItems": []})
        )

        activities, _ = await fetch_ado_activity(ado_repo, date(2026, 3, 12), token="test-token")
        assert len(activities) == 1
        assert activities[0].activity_type == "pr"
