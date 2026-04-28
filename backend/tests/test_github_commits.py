import os
from datetime import datetime, timezone

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app.config import get_settings  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from backend.app import create_app  # noqa: E402
from backend.app.auth import require_server_admin  # noqa: E402
from backend.app import github_commits  # noqa: E402


class GithubResponse:
    def __init__(self, payload: dict, status_code: int = 200, text: str = "") -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_github_commit_lookup_uses_graphql_variables(monkeypatch) -> None:
    calls = []

    def fake_post(url, *, headers, json, timeout):
        calls.append((url, headers, json, timeout))
        return GithubResponse(
            {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "totalCommitContributions": 321,
                            "contributionCalendar": {
                                "totalContributions": 479,
                            },
                        },
                    },
                },
            },
        )

    monkeypatch.setenv("GITHUB_TOKEN", "unit-token")
    get_settings.cache_clear()
    github_commits._commit_cache.clear()
    monkeypatch.setattr(github_commits.httpx, "post", fake_post)
    monkeypatch.setattr(
        github_commits,
        "get_current_year_commit_range",
        lambda: {
            "year": 2026,
            "from": "2026-01-01T00:00:00Z",
            "to": "2026-04-28T00:00:00Z",
        },
    )

    result = github_commits.get_total_commits("Marhs2")
    cached = github_commits.get_total_commits("marhs2")

    assert result == {
        "username": "Marhs2",
        "totalCommits": 479,
        "totalContributions": 479,
        "totalCommitContributions": 321,
        "year": 2026,
        "from": "2026-01-01T00:00:00Z",
        "to": "2026-04-28T00:00:00Z",
    }
    assert cached == result
    assert len(calls) == 1
    assert calls[0][2]["variables"] == {
        "login": "Marhs2",
        "from": "2026-01-01T00:00:00Z",
        "to": "2026-04-28T00:00:00Z",
    }
    assert "Marhs2" not in calls[0][2]["query"]
    assert "contributionCalendar" in calls[0][2]["query"]


def test_github_commit_range_uses_current_calendar_year() -> None:
    assert github_commits.get_current_year_commit_range(
        datetime(2026, 4, 28, tzinfo=timezone.utc),
    ) == {
        "year": 2026,
        "from": "2026-01-01T00:00:00Z",
        "to": "2026-04-28T00:00:00Z",
    }


def test_github_username_validation_rejects_invalid_values() -> None:
    try:
        github_commits.normalize_github_username("bad/user")
    except ValueError as error:
        assert "GitHub" in str(error)
    else:
        raise AssertionError("invalid username was accepted")


def test_github_commit_status_endpoint_reports_success(monkeypatch) -> None:
    app = create_app()
    app.dependency_overrides[require_server_admin] = lambda: {
        "email": "owner@sdh.hs.kr",
        "isAdmin": True,
        "isConfigAdmin": True,
    }
    monkeypatch.setattr(
        "backend.app.routers.github_commits.get_total_commits",
        lambda username: {
            "username": username,
            "totalCommits": 123,
            "totalContributions": 123,
            "totalCommitContributions": 45,
            "year": 2026,
            "from": "2026-01-01T00:00:00Z",
            "to": "2027-01-01T00:00:00Z",
        },
    )

    response = TestClient(app).get("/api/github/commit-status?username=Marhs2")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "configured": True,
        "checkedUsername": "Marhs2",
        "totalCommits": 123,
        "totalContributions": 123,
        "totalCommitContributions": 45,
        "year": 2026,
        "from": "2026-01-01T00:00:00Z",
        "to": "2027-01-01T00:00:00Z",
    }


def test_github_commit_batch_returns_partial_results(monkeypatch) -> None:
    app = create_app()

    def fake_get_total_commits(username: str) -> dict:
        if username == "missing-user":
            raise github_commits.GithubUserNotFoundError("missing")
        return {"username": username, "totalCommits": 10}

    monkeypatch.setattr(
        "backend.app.routers.github_commits.get_total_commits",
        fake_get_total_commits,
    )

    response = TestClient(app).post(
        "/api/github/commits",
        json={"usernames": ["good-user", "missing-user"]},
    )

    assert response.status_code == 200
    assert response.json()["results"] == [{"username": "good-user", "totalCommits": 10}]
    assert response.json()["errors"][0]["username"] == "missing-user"


def test_github_commit_batch_keeps_lookup_failures_partial(monkeypatch) -> None:
    app = create_app()

    def fake_get_total_commits(username: str) -> dict:
        if username == "github-down":
            raise github_commits.GithubCommitLookupError("upstream failed")
        return {"username": username, "totalCommits": 10}

    monkeypatch.setattr(
        "backend.app.routers.github_commits.get_total_commits",
        fake_get_total_commits,
    )

    response = TestClient(app).post(
        "/api/github/commits",
        json={"usernames": ["good-user", "github-down"]},
    )

    assert response.status_code == 200
    assert response.json()["results"] == [{"username": "good-user", "totalCommits": 10}]
    assert response.json()["errors"][0] == {
        "username": "github-down",
        "reason": "GithubCommitLookupError",
        "message": "upstream failed",
    }
