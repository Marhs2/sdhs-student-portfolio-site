import json
import logging
import time
from typing import Any
from uuid import uuid4

from starlette.requests import Request


security_logger = logging.getLogger("portfolio-security")
SENSITIVE_FIELD_NAMES = {"authorization", "cookie", "password", "secret", "service_role", "token"}
MAX_LOGGED_TEXT_LENGTH = 240


def new_request_id() -> str:
    return uuid4().hex[:12]


def now_ms() -> int:
    return int(time.time() * 1000)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.replace("-", "_").lower()
    return any(name in normalized for name in SENSITIVE_FIELD_NAMES)


def _to_camel_case(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, str) and len(value) > MAX_LOGGED_TEXT_LENGTH:
            return f"{value[:MAX_LOGGED_TEXT_LENGTH]}..."
        return value
    if isinstance(value, (list, tuple, set)):
        return [_clean_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): "[redacted]" if _is_sensitive_key(str(key)) else _clean_value(entry)
            for key, entry in value.items()
            if entry is not None
        }
    return str(value)


def get_request_security_context(request: Request) -> dict[str, Any]:
    return {
        "method": request.method,
        "path": request.url.path,
        "query": dict(request.query_params),
        "client_host": request.client.host if request.client else "",
        "forwarded_for": request.headers.get("x-forwarded-for", ""),
        "origin": request.headers.get("origin", ""),
        "referer": request.headers.get("referer", ""),
        "user_agent": request.headers.get("user-agent", ""),
        "content_type": request.headers.get("content-type", ""),
        "content_length": request.headers.get("content-length", ""),
    }


def log_security_event(
    event: str,
    *,
    outcome: str,
    severity: str = "info",
    request_id: str | None = None,
    actor_email: str | None = None,
    actor_profile_id: int | str | None = None,
    target_type: str | None = None,
    target_id: int | str | None = None,
    reason: str | None = None,
    **fields: Any,
) -> None:
    payload = {
        "event": event,
        "outcome": outcome,
        "severity": severity,
        "requestId": request_id,
        "actorEmail": actor_email,
        "actorProfileId": actor_profile_id,
        "targetType": target_type,
        "targetId": target_id,
        "reason": reason,
        **fields,
    }
    cleaned = {
        _to_camel_case(key): "[redacted]" if _is_sensitive_key(key) else _clean_value(value)
        for key, value in payload.items()
        if value is not None
    }
    message = json.dumps(cleaned, ensure_ascii=False, sort_keys=True)

    if severity in {"error", "critical"}:
        security_logger.error(message)
    elif severity == "warning":
        security_logger.warning(message)
    else:
        security_logger.info(message)
