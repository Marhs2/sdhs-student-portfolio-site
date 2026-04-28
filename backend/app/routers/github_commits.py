import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

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
                "message": str(error),
            }
        if isinstance(error, GithubUserNotFoundError):
            return {
                "ok": False,
                "configured": True,
                "checkedUsername": username,
                "totalCommits": None,
                "message": str(error),
            }
        if isinstance(error, (GithubCommitLookupError, httpx.HTTPError)):
            return {
                "ok": False,
                "configured": True,
                "checkedUsername": username,
                "totalCommits": None,
                "message": f"GitHub API 조회에 실패했습니다: {error}",
            }
        raise


@router.get("/commits/{username}")
def get_github_commits(username: str) -> dict:
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
def post_github_commits(payload: GithubCommitBatchPayload) -> dict:
    results = []
    errors = []
    try:
        for username in iter_unique_github_usernames(payload.usernames):
            try:
                results.append(get_total_commits(username))
            except GithubCommitConfigurationError:
                raise
            except (GithubUserNotFoundError, GithubCommitLookupError, ValueError, httpx.HTTPError) as item_error:
                errors.append(
                    {
                        "username": username,
                        "reason": type(item_error).__name__,
                        "message": str(item_error),
                    },
                )

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
