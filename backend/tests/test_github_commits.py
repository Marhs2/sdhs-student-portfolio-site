import os
import time
from datetime import datetime, timezone
from threading import Lock

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app.config import get_settings  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from backend.app import create_app  # noqa: E402
from backend.app.auth import require_server_admin  # noqa: E402
from backend.app import github_commits  # noqa: E402
from backend.app.routers import github_commits as github_commit_router  # noqa: E402


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
    github_commits._negative_lookup_cache.clear()
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


def test_github_missing_user_lookup_is_negative_cached(monkeypatch) -> None:
    calls = []

    def fake_post(url, *, headers, json, timeout):
        calls.append(json["variables"]["login"])
        return GithubResponse({"data": {"user": None}})

    monkeypatch.setenv("GITHUB_TOKEN", "unit-token")
    get_settings.cache_clear()
    github_commits._commit_cache.clear()
    github_commits._negative_lookup_cache.clear()
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

    for _ in range(2):
        try:
            github_commits.get_total_commits("missing-user")
        except github_commits.GithubUserNotFoundError:
            pass
        else:
            raise AssertionError("missing GitHub user was accepted")

    assert calls == ["missing-user"]


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
    github_commit_router._github_lookup_events_by_host.clear()

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
    github_commit_router._github_lookup_events_by_host.clear()

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


def test_github_commit_batch_uses_bounded_parallel_lookup(monkeypatch) -> None:
    app = create_app()
    github_commit_router._github_lookup_events_by_host.clear()
    active = 0
    max_active = 0
    lock = Lock()

    def fake_get_total_commits(username: str) -> dict:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        return {"username": username, "totalCommits": 10}

    monkeypatch.setattr(
        "backend.app.routers.github_commits.get_total_commits",
        fake_get_total_commits,
    )

    response = TestClient(app).post(
        "/api/github/commits",
        json={"usernames": [f"user-{index}" for index in range(12)]},
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 12
    assert max_active > 1
    assert max_active <= 4


def test_github_commit_batch_rejects_large_public_fanout() -> None:
    app = create_app()
    github_commit_router._github_lookup_events_by_host.clear()

    response = TestClient(app).post(
        "/api/github/commits",
        json={"usernames": [f"user-{index}" for index in range(21)]},
    )

    assert response.status_code == 422


def test_github_commit_lookup_is_rate_limited_by_host(monkeypatch) -> None:
    app = create_app()
    github_commit_router._github_lookup_events_by_host.clear()
    monkeypatch.setattr(github_commit_router, "GITHUB_PUBLIC_LOOKUP_LIMIT", 1)
    monkeypatch.setattr(
        "backend.app.routers.github_commits.get_total_commits",
        lambda username: {"username": username, "totalCommits": 10},
    )

    client = TestClient(app)
    assert client.get("/api/github/commits/one").status_code == 200
    response = client.get("/api/github/commits/two")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
