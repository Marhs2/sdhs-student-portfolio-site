import base64
import json
import logging
import re
from time import time
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import get_auth_user
from .config import get_settings
from .repositories import (
    get_portfolio_item_by_id,
    get_profile_by_email,
    get_profile_by_id,
    is_public_approved_profile,
)
from .security_logging import log_security_event


logger = logging.getLogger("portfolio-backend")
bearer_scheme = HTTPBearer(auto_error=False)
ALLOWED_EMAIL_DOMAIN = "sdh.hs.kr"
MAX_BEARER_TOKEN_LENGTH = 8192
JWT_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def is_allowed_school_email(email: str) -> bool:
    normalized = email.strip().lower()
    return normalized.endswith(f"@{ALLOWED_EMAIL_DOMAIN}")


def is_configured_admin_email(email: str) -> bool:
    normalized = email.strip().lower()
    return normalized in get_settings().admin_emails


def _unwrap_user(response: Any) -> Any:
    if hasattr(response, "user"):
        return response.user
    if isinstance(response, dict):
        return response.get("user") or response
    return None


def _get_user_email(user: Any) -> str:
    if hasattr(user, "email"):
        return user.email or ""
    if isinstance(user, dict):
        return user.get("email", "")
    return ""


def _get_user_id(user: Any) -> str:
    if hasattr(user, "id"):
        return str(user.id or "")
    if isinstance(user, dict):
        return str(user.get("id", ""))
    return ""


def _decode_jwt_segment(segment: str) -> dict[str, Any]:
    padded = segment + "=" * (-len(segment) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    payload = json.loads(decoded.decode("utf-8"))
    return payload if isinstance(payload, dict) else {}


def _preflight_bearer_token(token: str) -> tuple[bool, str]:
    if not token or len(token) > MAX_BEARER_TOKEN_LENGTH:
        return False, "invalid_token_length"

    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        return False, "token_is_not_jwt"
    if not all(JWT_SEGMENT_PATTERN.match(part) for part in parts):
        return False, "token_has_invalid_characters"

    try:
        header = _decode_jwt_segment(parts[0])
        payload = _decode_jwt_segment(parts[1])
    except Exception:
        return False, "token_payload_is_not_valid_json"

    if header.get("typ") not in {None, "JWT"}:
        return False, "token_type_is_not_jwt"
    if not payload.get("sub"):
        return False, "token_missing_subject"

    expires_at = payload.get("exp")
    if not isinstance(expires_at, (int, float)):
        return False, "token_missing_expiration"
    if expires_at <= time():
        return False, "token_expired"

    return True, ""


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str]:
    if not credentials or credentials.scheme.lower() != "bearer":
        log_security_event(
            "auth.missing_bearer",
            outcome="blocked",
            severity="warning",
            reason="missing_or_invalid_authorization_scheme",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
        )

    is_token_shape_valid, token_rejection_reason = _preflight_bearer_token(credentials.credentials)
    if not is_token_shape_valid:
        log_security_event(
            "auth.malformed_token",
            outcome="blocked",
            severity="warning",
            reason=token_rejection_reason,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료되었거나 유효하지 않은 로그인입니다.",
        )

    try:
        response = get_auth_user(credentials.credentials)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        logger.warning("Rejected access token with auth status: %s", status_code)
        log_security_event(
            "auth.invalid_token",
            outcome="blocked",
            severity="warning",
            reason="supabase_auth_rejected_token",
            auth_status_code=status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료되었거나 유효하지 않은 로그인입니다.",
        ) from exc
    except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError, OSError) as exc:
        logger.warning("Supabase auth validation unavailable: %s", type(exc).__name__)
        log_security_event(
            "auth.validation_unavailable",
            outcome="error",
            severity="warning",
            reason=type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="로그인 확인이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    except Exception as exc:
        logger.warning("Failed to validate access token: %s", type(exc).__name__)
        log_security_event(
            "auth.invalid_token",
            outcome="blocked",
            severity="warning",
            reason=type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료되었거나 유효하지 않은 로그인입니다.",
        ) from exc

    user = _unwrap_user(response)
    email = _get_user_email(user)
    user_id = _get_user_id(user)
    if not user or not email or not user_id:
        log_security_event(
            "auth.invalid_user_payload",
            outcome="blocked",
            severity="warning",
            reason="missing_user_email_or_id",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료되었거나 유효하지 않은 로그인입니다.",
        )

    if not is_allowed_school_email(email):
        log_security_event(
            "auth.disallowed_domain",
            outcome="blocked",
            severity="warning",
            actor_email=email.strip().lower(),
            reason="email_domain_not_allowed",
            allowed_domain=ALLOWED_EMAIL_DOMAIN,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="서울디지텍고등학교 sdh.hs.kr 계정만 사용할 수 있습니다.",
        )

    return {"id": user_id, "email": email.strip().lower()}


def get_current_profile(user: dict[str, str] = Depends(get_current_user)) -> dict[str, Any]:
    profile = get_profile_by_email(user["email"], include_private=True)
    if not profile:
        if is_configured_admin_email(user["email"]):
            log_security_event(
                "auth.config_admin_without_profile",
                outcome="allowed",
                actor_email=user["email"],
                reason="configured_admin_email",
            )
            return {
                "id": None,
                "email": user["email"],
                "name": "관리자",
                "isAdmin": True,
                "isConfigAdmin": True,
            }
        log_security_event(
            "auth.profile_missing",
            outcome="blocked",
            severity="warning",
            actor_email=user["email"],
            reason="authenticated_user_has_no_profile",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )
    if is_configured_admin_email(user["email"]):
        profile["isAdmin"] = True
        profile["isConfigAdmin"] = True
    return profile


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str] | None:
    if not credentials:
        return None
    return get_current_user(credentials)


def get_optional_profile(
    user: dict[str, str] | None = Depends(get_optional_user),
) -> dict[str, Any] | None:
    if not user:
        return None
    return get_profile_by_email(user["email"], include_private=True)


def can_view_profile(
    target: dict[str, Any] | None,
    viewer: dict[str, Any] | None = None,
) -> bool:
    if not target:
        return False
    if not viewer:
        return is_public_approved_profile(target)
    if viewer.get("isAdmin") or viewer.get("email") == target.get("email"):
        return True
    return is_public_approved_profile(target)


def require_admin(profile: dict[str, Any] = Depends(get_current_profile)) -> dict[str, Any]:
    if not profile.get("isAdmin"):
        log_security_event(
            "authorization.admin_required",
            outcome="blocked",
            severity="warning",
            actor_email=profile.get("email"),
            actor_profile_id=profile.get("id"),
            reason="profile_is_not_admin",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return profile


def require_server_admin(profile: dict[str, Any] = Depends(get_current_profile)) -> dict[str, Any]:
    if not profile.get("isConfigAdmin"):
        log_security_event(
            "authorization.server_admin_required",
            outcome="blocked",
            severity="warning",
            actor_email=profile.get("email"),
            actor_profile_id=profile.get("id"),
            reason="profile_is_not_config_admin",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="서버 관리자 권한이 필요합니다.",
        )
    return profile


def require_profile_write_access(
    profile_id: int,
    profile: dict[str, Any] = Depends(get_current_profile),
) -> dict[str, Any]:
    target = get_profile_by_id(profile_id, include_private=True)
    if not target:
        log_security_event(
            "authorization.profile_write_missing_target",
            outcome="blocked",
            severity="warning",
            actor_email=profile.get("email"),
            actor_profile_id=profile.get("id"),
            target_type="profile",
            target_id=profile_id,
            reason="target_profile_not_found",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )

    if profile.get("isAdmin") or target.get("email") == profile.get("email"):
        return profile

    log_security_event(
        "authorization.profile_write_denied",
        outcome="blocked",
        severity="warning",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="profile",
        target_id=profile_id,
        reason="actor_is_not_owner_or_admin",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="이 프로필을 수정할 권한이 없습니다.",
    )


def require_portfolio_item_write_access(
    item_id: int,
    profile: dict[str, Any] = Depends(get_current_profile),
) -> dict[str, Any]:
    target = get_portfolio_item_by_id(item_id, include_private=True)
    if not target:
        log_security_event(
            "authorization.portfolio_item_write_missing_target",
            outcome="blocked",
            severity="warning",
            actor_email=profile.get("email"),
            actor_profile_id=profile.get("id"),
            target_type="portfolio_item",
            target_id=item_id,
            reason="target_item_not_found",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포트폴리오 항목을 찾을 수 없습니다.",
        )

    if profile.get("isAdmin") or target.get("ownerEmail") == profile.get("email"):
        return profile

    log_security_event(
        "authorization.portfolio_item_write_denied",
        outcome="blocked",
        severity="warning",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="portfolio_item",
        target_id=item_id,
        reason="actor_is_not_owner_or_admin",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="이 포트폴리오 항목을 수정할 권한이 없습니다.",
    )
