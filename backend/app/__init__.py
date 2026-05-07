import asyncio
from collections import deque
from contextlib import asynccontextmanager, suppress
from ipaddress import ip_address, ip_network
from threading import RLock
from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from starlette.staticfiles import StaticFiles
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
_rate_limit_lock = RLock()
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
PRIVATE_API_CACHE_CONTROL = "no-store, private"


async def _run_keepalive_loop(url: str, interval_seconds: int) -> None:
    interval_seconds = max(60, interval_seconds)
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                await client.get(url)
            except Exception as exc:
                log_security_event(
                    "keepalive.health_ping_failed",
                    outcome="error",
                    severity="warning",
                    reason=type(exc).__name__,
                )


def _append_vary_header(response: Response, value: str) -> None:
    existing = {
        entry.strip().lower()
        for entry in response.headers.get("Vary", "").split(",")
        if entry.strip()
    }
    if value.lower() in existing:
        return
    response.headers["Vary"] = (
        f"{response.headers['Vary']}, {value}"
        if response.headers.get("Vary")
        else value
    )


def _is_private_api_response(request: Request) -> bool:
    path = request.url.path
    if not path.startswith("/api/"):
        return False
    if path.startswith(("/api/me/", "/api/admin/", "/api/server-admin/")):
        return True
    return request.headers.get("authorization", "").lower().startswith("bearer ")


def _client_host_from_request(request: Request) -> str:
    direct_host = request.client.host if request.client else ""
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for and _is_trusted_forwarding_source(direct_host):
        forwarded_host = _trusted_forwarded_client_host(forwarded_for)
        if forwarded_host:
            return forwarded_host
    return direct_host


def _trusted_forwarded_client_host(forwarded_for: str) -> str:
    forwarded_hosts = [host.strip() for host in forwarded_for.split(",") if host.strip()]
    for host in reversed(forwarded_hosts):
        try:
            address = ip_address(host)
        except ValueError:
            continue
        if not any(address in network for network in TRUSTED_FORWARDING_NETWORKS):
            return str(address)
    if forwarded_hosts:
        try:
            return str(ip_address(forwarded_hosts[0]))
        except ValueError:
            return ""
    return ""


def _is_trusted_forwarding_source(client_host: str) -> bool:
    if client_host in {"", "testclient", "localhost"}:
        return True
    try:
        address = ip_address(client_host)
    except ValueError:
        return False
    return any(address in network for network in TRUSTED_FORWARDING_NETWORKS)


def _recent_auth_failures(client_host: str, now: float, *, create: bool = True) -> deque[float]:
    events = _auth_failure_events_by_host.get(client_host)
    if events is None:
        if not create:
            return deque()
        events = deque()
        _auth_failure_events_by_host[client_host] = events
    while events and now - events[0] > AUTH_FAILURE_WINDOW_SECONDS:
        events.popleft()
    if not events and not create:
        _auth_failure_events_by_host.pop(client_host, None)
    return events


def _is_auth_failure_limited(client_host: str) -> bool:
    if not client_host:
        return False
    with _rate_limit_lock:
        return len(_recent_auth_failures(client_host, monotonic(), create=False)) >= AUTH_FAILURE_LIMIT


def _record_auth_failure(client_host: str) -> None:
    if client_host:
        with _rate_limit_lock:
            _recent_auth_failures(client_host, monotonic()).append(monotonic())


def _recent_sensitive_mutations(client_host: str, now: float, *, create: bool = True) -> deque[float]:
    events = _sensitive_mutation_events_by_host.get(client_host)
    if events is None:
        if not create:
            return deque()
        events = deque()
        _sensitive_mutation_events_by_host[client_host] = events
    while events and now - events[0] > SENSITIVE_MUTATION_WINDOW_SECONDS:
        events.popleft()
    if not events and not create:
        _sensitive_mutation_events_by_host.pop(client_host, None)
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
        or path == "/api/profiles"
        or path.startswith("/api/profiles/")
        or path == "/api/portfolio-items"
        or path.startswith("/api/portfolio-items/")
        or path.startswith("/api/uploads/")
    )


def _is_sensitive_mutation_limited(client_host: str) -> bool:
    if not client_host:
        return False
    with _rate_limit_lock:
        return len(_recent_sensitive_mutations(client_host, monotonic(), create=False)) >= SENSITIVE_MUTATION_LIMIT


def _record_sensitive_mutation(client_host: str) -> None:
    if client_host:
        with _rate_limit_lock:
            _recent_sensitive_mutations(client_host, monotonic()).append(monotonic())


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    keepalive_task = None
    if settings.keepalive_url:
        keepalive_task = asyncio.create_task(
            _run_keepalive_loop(
                settings.keepalive_url,
                settings.keepalive_interval_seconds,
            ),
        )

    try:
        yield
    finally:
        if keepalive_task:
            keepalive_task.cancel()
            with suppress(asyncio.CancelledError):
                await keepalive_task
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
        if _is_private_api_response(request):
            response.headers["Cache-Control"] = PRIVATE_API_CACHE_CONTROL
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            if request.headers.get("authorization"):
                _append_vary_header(response, "Authorization")
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

        is_sensitive_mutation = _is_sensitive_mutation_request(request)
        if is_sensitive_mutation:
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

        if is_sensitive_mutation and response.status_code not in {401, 403}:
            _record_sensitive_mutation(client_host)

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
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

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
        max_age=600,
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
    app.mount(
        "/uploads",
        StaticFiles(directory=str(settings.upload_dir), check_dir=False),
        name="uploads",
    )

    return app
