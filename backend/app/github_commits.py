from datetime import datetime, timezone
import re
from threading import BoundedSemaphore, RLock
from time import monotonic
from typing import Any

import httpx

from .cache import TtlCache
from .config import get_settings


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
COMMIT_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      contributionCalendar {
        totalContributions
      }
    }
  }
}
"""

_settings = get_settings()
_commit_cache = TtlCache(_settings.github_commit_cache_ttl_seconds)
_github_api_semaphore = BoundedSemaphore(4)
_negative_cache_lock = RLock()
_negative_lookup_cache: dict[tuple[str, int], tuple[float, str, str]] = {}
NEGATIVE_LOOKUP_CACHE_TTL_SECONDS = 300


class GithubCommitLookupError(RuntimeError):
    pass


class GithubCommitConfigurationError(GithubCommitLookupError):
    pass


class GithubUserNotFoundError(GithubCommitLookupError):
    pass


def _read_negative_lookup_cache(cache_key: tuple[str, int]) -> None:
    with _negative_cache_lock:
        cached = _negative_lookup_cache.get(cache_key)
        if not cached:
            return
        expires_at, error_type, message = cached
        if monotonic() >= expires_at:
            _negative_lookup_cache.pop(cache_key, None)
            return

    if error_type == "GithubUserNotFoundError":
        raise GithubUserNotFoundError(message)
    raise GithubCommitLookupError(message)


def _store_negative_lookup(cache_key: tuple[str, int], error: Exception) -> None:
    if isinstance(error, GithubCommitConfigurationError):
        return
    if not isinstance(error, (GithubUserNotFoundError, GithubCommitLookupError)):
        return
    if "요청이 많아" in str(error):
        return
    with _negative_cache_lock:
        _negative_lookup_cache[cache_key] = (
            monotonic() + NEGATIVE_LOOKUP_CACHE_TTL_SECONDS,
            type(error).__name__,
            str(error),
        )


def normalize_github_username(username: str) -> str:
    normalized = str(username or "").strip().lstrip("@")
    if not GITHUB_USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError("올바른 GitHub 사용자명이 아닙니다.")
    return normalized


def _read_contribution_counts(payload: dict[str, Any], username: str) -> dict[str, int]:
    if payload.get("errors"):
        raise GithubCommitLookupError(str(payload["errors"]))

    user = (payload.get("data") or {}).get("user")
    if not user:
        raise GithubUserNotFoundError(f"GitHub 사용자를 찾을 수 없습니다: {username}")

    contributions = user.get("contributionsCollection") or {}
    contribution_calendar = contributions.get("contributionCalendar") or {}
    return {
        "totalContributions": int(contribution_calendar.get("totalContributions") or 0),
        "totalCommitContributions": int(contributions.get("totalCommitContributions") or 0),
    }


def get_current_year_commit_range(now: datetime | None = None) -> dict[str, Any]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    year = current.year
    return {
        "year": year,
        "from": f"{year}-01-01T00:00:00Z",
        "to": current.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def get_total_commits(username: str) -> dict[str, Any]:
    normalized_username = normalize_github_username(username)
    commit_range = get_current_year_commit_range()
    cache_key = (normalized_username.lower(), commit_range["year"])
    _read_negative_lookup_cache(cache_key)

    def fetch_commits() -> dict[str, Any]:
        settings = get_settings()
        if not settings.github_token:
            raise GithubCommitConfigurationError("GITHUB_TOKEN 환경변수가 필요합니다.")

        if not _github_api_semaphore.acquire(blocking=False):
            raise GithubCommitLookupError("GitHub 활동 조회 요청이 많아 잠시 후 다시 시도해 주세요.")

        try:
            response = httpx.post(
                GITHUB_GRAPHQL_URL,
                headers={
                    "Authorization": f"Bearer {settings.github_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": COMMIT_QUERY,
                    "variables": {
                        "login": normalized_username,
                        "from": commit_range["from"],
                        "to": commit_range["to"],
                    },
                },
                timeout=httpx.Timeout(connect=2.0, read=8.0, write=4.0, pool=2.0),
            )
        finally:
            _github_api_semaphore.release()
        if response.status_code >= 400:
            raise GithubCommitLookupError(
                f"GitHub API HTTP {response.status_code}: {response.text[:200]}",
            )

        counts = _read_contribution_counts(response.json(), normalized_username)
        return {
            "username": normalized_username,
            "totalCommits": counts["totalContributions"],
            "totalContributions": counts["totalContributions"],
            "totalCommitContributions": counts["totalCommitContributions"],
            "year": commit_range["year"],
            "from": commit_range["from"],
            "to": commit_range["to"],
        }

    try:
        return _commit_cache.get_or_set(cache_key, fetch_commits)
    except (GithubUserNotFoundError, GithubCommitLookupError) as error:
        _store_negative_lookup(cache_key, error)
        raise


def get_total_commits_for_users(usernames: list[str]) -> list[dict[str, Any]]:
    return [get_total_commits(username) for username in iter_unique_github_usernames(usernames)]


def iter_unique_github_usernames(usernames: list[str]) -> list[str]:
    normalized_usernames = []
    seen = set()
    for username in usernames:
        normalized = normalize_github_username(username)
        key = normalized.lower()
        if key not in seen:
            normalized_usernames.append(normalized)
            seen.add(key)

    return normalized_usernames
