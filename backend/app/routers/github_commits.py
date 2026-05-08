from concurrent.futures import ThreadPoolExecutor
from collections import deque
from threading import BoundedSemaphore, RLock
from time import monotonic

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..auth import require_server_admin
from ..github_commits import (
    GithubCommitConfigurationError,
    GithubCommitLookupError,
    GithubUserNotFoundError,
    get_total_commits,
    iter_unique_github_usernames,
)
from ..schemas import GithubCommitBatchPayload
from ..security_logging import log_security_event


router = APIRouter(prefix="/api/github", tags=["github"])
GITHUB_COMMIT_BATCH_WORKERS = 4
GITHUB_COMMIT_BATCH_MAX_USERNAMES = 20
GITHUB_PUBLIC_LOOKUP_WINDOW_SECONDS = 60
GITHUB_PUBLIC_LOOKUP_LIMIT = 40
_github_batch_semaphore = BoundedSemaphore(2)
_github_lookup_events_by_host: dict[str, deque[float]] = {}
_github_lookup_lock = RLock()


def _client_host(request: Request) -> str:
    return request.client.host if request.client else ""


def _require_public_github_lookup_budget(request: Request, lookup_count: int = 1) -> None:
    client_host = _client_host(request)
    if not client_host:
        return
    now = monotonic()
    with _github_lookup_lock:
        events = _github_lookup_events_by_host.setdefault(client_host, deque())
        while events and now - events[0] > GITHUB_PUBLIC_LOOKUP_WINDOW_SECONDS:
            events.popleft()
        if len(events) + lookup_count > GITHUB_PUBLIC_LOOKUP_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="GitHub 활동 조회 요청이 많아 잠시 후 다시 시도해 주세요.",
                headers={"Retry-After": str(GITHUB_PUBLIC_LOOKUP_WINDOW_SECONDS)},
            )
        events.extend(now for _ in range(lookup_count))


def _handle_github_error(error: Exception) -> None:
    if isinstance(error, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    if isinstance(error, GithubCommitConfigurationError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub 활동 조회 토큰이 설정되지 않았습니다.",
        )
    if isinstance(error, GithubUserNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, (GithubCommitLookupError, httpx.HTTPError)):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub 활동 수를 조회하지 못했습니다.",
        )
    raise error


def _public_github_lookup_message(error: Exception) -> str:
    if isinstance(error, ValueError):
        return str(error)
    if isinstance(error, GithubUserNotFoundError):
        return str(error)
    return "GitHub 활동 수를 조회하지 못했습니다."


def _lookup_github_commit_batch(usernames: list[str]) -> tuple[list[dict], list[dict]]:
    results = []
    errors = []
    if not usernames:
        return results, errors

    if not _github_batch_semaphore.acquire(blocking=False):
        raise GithubCommitLookupError("GitHub 활동 조회 요청이 많아 잠시 후 다시 시도해 주세요.")

    try:
        max_workers = min(GITHUB_COMMIT_BATCH_WORKERS, len(usernames))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_by_username = {
                username: executor.submit(get_total_commits, username)
                for username in usernames
            }
            for username in usernames:
                try:
                    results.append(future_by_username[username].result())
                except GithubCommitConfigurationError:
                    raise
                except (GithubUserNotFoundError, GithubCommitLookupError, ValueError, httpx.HTTPError) as item_error:
                    errors.append(
                        {
                            "username": username,
                            "reason": type(item_error).__name__,
                            "message": _public_github_lookup_message(item_error),
                        },
                    )
    finally:
        _github_batch_semaphore.release()

    return results, errors


@router.get("/commit-status")
def get_github_commit_status(
    username: str = Query(default="torvalds"),
    admin: dict = Depends(require_server_admin),
) -> dict:
    try:
        result = get_total_commits(username)
        return {
            "ok": True,
            "configured": True,
            "checkedUsername": result["username"],
            "totalCommits": result["totalCommits"],
            "totalContributions": result.get("totalContributions"),
            "totalCommitContributions": result.get("totalCommitContributions"),
            "year": result.get("year"),
            "from": result.get("from"),
            "to": result.get("to"),
        }
    except Exception as error:
        log_security_event(
            "github.commits_status_check_failed",
            outcome="error",
            severity="warning",
            actor_email=admin.get("email"),
            target_type="github_user",
            target_id=username,
            reason=type(error).__name__,
            error_message=str(error),
        )
        if isinstance(error, GithubCommitConfigurationError):
            return {
                "ok": False,
                "configured": False,
                "checkedUsername": username,
                "totalCommits": None,
                "message": "GITHUB_TOKEN 환경변수가 설정되지 않았습니다.",
            }
        if isinstance(error, ValueError):
            return {
                "ok": False,
                "configured": True,
                "checkedUsername": username,
                "totalCommits": None,
                "message": "올바른 GitHub 사용자명이 아닙니다.",
            }
        if isinstance(error, GithubUserNotFoundError):
            return {
                "ok": False,
                "configured": True,
                "checkedUsername": username,
                "totalCommits": None,
                "message": "GitHub 사용자를 찾을 수 없습니다.",
            }
        if isinstance(error, (GithubCommitLookupError, httpx.HTTPError)):
            return {
                "ok": False,
                "configured": True,
                "checkedUsername": username,
                "totalCommits": None,
                "message": "GitHub API 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.",
            }
        raise


@router.get("/commits/{username}")
def get_github_commits(username: str, request: Request) -> dict:
    _require_public_github_lookup_budget(request)
    try:
        return get_total_commits(username)
    except Exception as error:
        log_security_event(
            "github.commits_lookup_failed",
            outcome="error",
            severity="warning",
            target_type="github_user",
            target_id=username,
            reason=type(error).__name__,
            error_message=str(error),
        )
        _handle_github_error(error)
        raise


@router.post("/commits")
def post_github_commits(payload: GithubCommitBatchPayload, request: Request) -> dict:
    try:
        usernames = iter_unique_github_usernames(payload.usernames)
        if len(usernames) > GITHUB_COMMIT_BATCH_MAX_USERNAMES:
            raise ValueError(f"GitHub 사용자명은 한 번에 최대 {GITHUB_COMMIT_BATCH_MAX_USERNAMES}개까지 조회할 수 있습니다.")
        _require_public_github_lookup_budget(request, len(usernames))
        results, errors = _lookup_github_commit_batch(usernames)
        return {"results": results, "errors": errors}
    except Exception as error:
        log_security_event(
            "github.commits_batch_lookup_failed",
            outcome="error",
            severity="warning",
            target_type="github_user_batch",
            target_id=str(len(payload.usernames)),
            reason=type(error).__name__,
            error_message=str(error),
        )
        _handle_github_error(error)
        raise
