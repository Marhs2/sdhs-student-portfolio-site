from contextlib import asynccontextmanager
from collections import deque
from ipaddress import ip_address, ip_network
from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response

from .config import get_settings
from .database import close_supabase_clients
from .security_logging import get_request_security_context, log_security_event, new_request_id, now_ms
from .routers.admin_profiles import router as admin_profiles_router
from .routers.admin_settings import router as admin_settings_router
from .routers.auth import router as auth_router
from .routers.github_commits import router as github_commits_router
from .routers.portfolio_items import router as portfolio_items_router
from .routers.profiles import router as profiles_router
from .routers.server_admin_profiles import router as server_admin_profiles_router
from .routers.server_admin_settings import router as server_admin_settings_router
from .routers.uploads import router as uploads_router


DANGEROUS_SERVER_CONTROL_PATH_PARTS = {
    "shutdown",
    "restart",
    "terminate",
    "kill",
    "stop-server",
    "server-stop",
}
AUTH_FAILURE_WINDOW_SECONDS = 60
AUTH_FAILURE_LIMIT = 25
SENSITIVE_MUTATION_WINDOW_SECONDS = 60
SENSITIVE_MUTATION_LIMIT = 30
_auth_failure_events_by_host: dict[str, deque[float]] = {}
_sensitive_mutation_events_by_host: dict[str, deque[float]] = {}
TRUSTED_FORWARDING_NETWORKS = tuple(
    ip_network(network)
    for network in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "::1/128",
        "fc00::/7",
    )
)


def _client_host_from_request(request: Request) -> str:
    direct_host = request.client.host if request.client else ""
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for and _is_trusted_forwarding_source(direct_host):
        return forwarded_for.split(",", 1)[0].strip()
    return direct_host


def _is_trusted_forwarding_source(client_host: str) -> bool:
    if client_host in {"", "testclient", "localhost"}:
        return True
    try:
        address = ip_address(client_host)
    except ValueError:
        return False
    return any(address in network for network in TRUSTED_FORWARDING_NETWORKS)


def _recent_auth_failures(client_host: str, now: float) -> deque[float]:
    events = _auth_failure_events_by_host.setdefault(client_host, deque())
    while events and now - events[0] > AUTH_FAILURE_WINDOW_SECONDS:
        events.popleft()
    return events


def _is_auth_failure_limited(client_host: str) -> bool:
    if not client_host:
        return False
    return len(_recent_auth_failures(client_host, monotonic())) >= AUTH_FAILURE_LIMIT


def _record_auth_failure(client_host: str) -> None:
    if client_host:
        _recent_auth_failures(client_host, monotonic()).append(monotonic())


def _recent_sensitive_mutations(client_host: str, now: float) -> deque[float]:
    events = _sensitive_mutation_events_by_host.setdefault(client_host, deque())
    while events and now - events[0] > SENSITIVE_MUTATION_WINDOW_SECONDS:
        events.popleft()
    return events


def _is_sensitive_mutation_request(request: Request) -> bool:
    if request.method not in {"POST", "PUT", "DELETE"}:
        return False
    path = request.url.path.lower()
    if not path.startswith("/api/"):
        return False
    return (
        request.method == "DELETE"
        or path.startswith("/api/admin/")
        or path.startswith("/api/server-admin/")
        or path.startswith("/api/uploads/")
    )


def _is_sensitive_mutation_limited(client_host: str) -> bool:
    if not client_host:
        return False
    return len(_recent_sensitive_mutations(client_host, monotonic())) >= SENSITIVE_MUTATION_LIMIT


def _record_sensitive_mutation(client_host: str) -> None:
    if client_host:
        _recent_sensitive_mutations(client_host, monotonic()).append(monotonic())


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        close_supabase_clients()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = new_request_id()
        request.state.request_id = request_id
        started_at = now_ms()
        context = get_request_security_context(request)
        client_host = _client_host_from_request(request)

        normalized_path = request.url.path.lower().strip("/")
        path_parts = {part for part in normalized_path.replace("_", "-").split("/") if part}
        if path_parts & DANGEROUS_SERVER_CONTROL_PATH_PARTS:
            log_security_event(
                "http.dangerous_server_control_path_blocked",
                outcome="blocked",
                severity="warning",
                request_id=request_id,
                status_code=404,
                duration_ms=now_ms() - started_at,
                reason="server_control_path_is_not_allowed",
                **context,
            )
            response = JSONResponse(
                status_code=404,
                content={"detail": "Not found"},
            )
            response.headers.setdefault("X-Request-ID", request_id)
            return response

        if (
            request.url.path.startswith("/api/")
            and request.headers.get("authorization", "").lower().startswith("bearer ")
            and _is_auth_failure_limited(client_host)
        ):
            log_security_event(
                "auth.failure_rate_limited",
                outcome="blocked",
                severity="warning",
                request_id=request_id,
                status_code=429,
                duration_ms=now_ms() - started_at,
                reason="too_many_recent_auth_failures",
                **context,
            )
            response = JSONResponse(
                status_code=429,
                content={"detail": "인증 실패가 반복되어 잠시 후 다시 시도해 주세요."},
            )
            response.headers.setdefault("X-Request-ID", request_id)
            response.headers.setdefault("Retry-After", str(AUTH_FAILURE_WINDOW_SECONDS))
            return response

        if _is_sensitive_mutation_request(request):
            if _is_sensitive_mutation_limited(client_host):
                log_security_event(
                    "http.sensitive_mutation_rate_limited",
                    outcome="blocked",
                    severity="warning",
                    request_id=request_id,
                    status_code=429,
                    duration_ms=now_ms() - started_at,
                    reason="too_many_recent_sensitive_mutations",
                    **context,
                )
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "민감한 작업 요청이 많아 잠시 후 다시 시도해 주세요."},
                )
                response.headers.setdefault("X-Request-ID", request_id)
                response.headers.setdefault("Retry-After", str(SENSITIVE_MUTATION_WINDOW_SECONDS))
                return response
            _record_sensitive_mutation(client_host)

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = now_ms() - started_at
            log_security_event(
                "http.request_exception",
                outcome="error",
                severity="error",
                request_id=request_id,
                duration_ms=duration_ms,
                exception_type=type(exc).__name__,
                **context,
            )
            raise

        duration_ms = now_ms() - started_at
        response.headers.setdefault("X-Request-ID", request_id)
        log_security_event(
            "http.request_completed",
            outcome="allowed" if response.status_code < 400 else "error",
            severity="warning" if response.status_code >= 500 or duration_ms >= 1500 else "info",
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=duration_ms,
            response_content_type=response.headers.get("content-type", ""),
            **context,
        )

        if request.url.path.startswith("/api/") and response.status_code in {401, 403}:
            if request.headers.get("authorization", "").lower().startswith("bearer "):
                _record_auth_failure(client_host)
            log_security_event(
                "http.access_denied",
                outcome="blocked",
                severity="warning",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
                **context,
            )

        if request.url.path.startswith("/api/") and duration_ms >= 1500:
            log_security_event(
                "http.slow_request",
                outcome="observed",
                severity="warning",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
                **context,
            )

        return response


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Portfolio Directory API", lifespan=lifespan)
    app.add_middleware(SecurityAuditMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=settings.allowed_origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(admin_profiles_router)
    app.include_router(admin_settings_router)
    app.include_router(github_commits_router)
    app.include_router(server_admin_profiles_router)
    app.include_router(server_admin_settings_router)
    app.include_router(profiles_router)
    app.include_router(portfolio_items_router)
    app.include_router(uploads_router)

    return app
