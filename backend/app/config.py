import base64
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
LOCAL_ONLY_SUPABASE_PROJECT_REFS = {"lbayyiylxjvqhcqejvkr"}


def _get_supabase_project_ref(url: str) -> str:
    hostname = url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    return hostname.split(".", 1)[0]


def _is_local_origin(origin: str) -> bool:
    normalized = origin.strip().lower()
    return (
        normalized.startswith("http://localhost:")
        or normalized == "http://localhost"
        or normalized.startswith("http://127.0.0.1:")
        or normalized == "http://127.0.0.1"
        or normalized.startswith("http://[::1]:")
        or normalized == "http://[::1]"
    )


def _assert_local_only_supabase_project(supabase_url: str, allowed_origins: list[str]) -> None:
    project_ref = _get_supabase_project_ref(supabase_url)
    if project_ref not in LOCAL_ONLY_SUPABASE_PROJECT_REFS:
        return

    non_local_origins = [origin for origin in allowed_origins if not _is_local_origin(origin)]
    if non_local_origins:
        raise RuntimeError(
            "Local-only Supabase project cannot be used with non-local allowed origins.",
        )


def _validate_allowed_origin_regex(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.lower()
    if "vercel\\.app" in normalized and ("[a-z" in normalized or ".*" in normalized):
        raise RuntimeError(
            "PORTFOLIO_ALLOWED_ORIGIN_REGEX must not wildcard the shared vercel.app namespace.",
        )
    return value


@dataclass(frozen=True)
class Settings:
    supabase_auth_url: str
    supabase_auth_service_role_key: str
    supabase_db_url: str
    supabase_db_service_role_key: str
    allowed_origins: list[str]
    allowed_origin_regex: str | None
    admin_emails: set[str]
    max_upload_bytes: int
    public_cache_ttl_seconds: int
    public_cache_stale_seconds: int
    github_token: str
    github_commit_cache_ttl_seconds: int
    keepalive_url: str
    keepalive_interval_seconds: int
    image_bucket: str = "user-img"

    @property
    def supabase_url(self) -> str:
        return self.supabase_db_url

    @property
    def supabase_service_role_key(self) -> str:
        return self.supabase_db_service_role_key

    @property
    def service_role_hint(self) -> str:
        jwt_parts = self.supabase_db_service_role_key.split(".")
        if len(jwt_parts) < 2:
            return "unknown"

        try:
            payload = jwt_parts[1]
            padding = "=" * (-len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload + padding).decode("utf-8")
            return json.loads(decoded).get("role", "unknown")
        except Exception:
            return "unknown"

    @property
    def public_cache_control_header(self) -> str:
        return "public, max-age=15, stale-while-revalidate=30"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(ENV_PATH, override=False)

    legacy_supabase_url = os.getenv("SUPABASE_URL", "").strip()
    legacy_supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    supabase_auth_url = os.getenv("SUPABASE_AUTH_URL", legacy_supabase_url).strip()
    supabase_auth_service_role_key = os.getenv(
        "SUPABASE_AUTH_SERVICE_ROLE_KEY",
        legacy_supabase_service_role_key,
    ).strip()
    supabase_db_url = os.getenv("SUPABASE_DB_URL", legacy_supabase_url).strip()
    supabase_db_service_role_key = os.getenv(
        "SUPABASE_DB_SERVICE_ROLE_KEY",
        legacy_supabase_service_role_key,
    ).strip()

    if (
        not supabase_auth_url
        or not supabase_auth_service_role_key
        or not supabase_db_url
        or not supabase_db_service_role_key
    ):
        raise RuntimeError(
            "Missing Supabase environment variables. Configure SUPABASE_AUTH_URL, "
            "SUPABASE_AUTH_SERVICE_ROLE_KEY, SUPABASE_DB_URL, and "
            "SUPABASE_DB_SERVICE_ROLE_KEY, or use legacy SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY.",
        )

    allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "PORTFOLIO_ALLOWED_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173",
        ).split(",")
        if origin.strip()
    ]
    _assert_local_only_supabase_project(supabase_auth_url, allowed_origins)

    max_upload_bytes = int(os.getenv("PORTFOLIO_MAX_UPLOAD_BYTES", str(1024 * 1024)))
    public_cache_ttl_seconds = int(os.getenv("PORTFOLIO_PUBLIC_CACHE_TTL_SECONDS", "30"))
    public_cache_stale_seconds = int(os.getenv("PORTFOLIO_PUBLIC_CACHE_STALE_SECONDS", "300"))
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    github_commit_cache_ttl_seconds = int(os.getenv("PORTFOLIO_GITHUB_COMMIT_CACHE_TTL_SECONDS", "900"))
    keepalive_url = os.getenv("PORTFOLIO_KEEPALIVE_URL", "").strip()
    keepalive_interval_seconds = int(os.getenv("PORTFOLIO_KEEPALIVE_INTERVAL_SECONDS", "600"))
    allowed_origin_regex = _validate_allowed_origin_regex(
        os.getenv("PORTFOLIO_ALLOWED_ORIGIN_REGEX", "").strip() or None,
    )
    admin_emails = {
        email.strip().lower()
        for email in os.getenv("PORTFOLIO_ADMIN_EMAILS", "").split(",")
        if email.strip()
    }

    return Settings(
        supabase_auth_url=supabase_auth_url,
        supabase_auth_service_role_key=supabase_auth_service_role_key,
        supabase_db_url=supabase_db_url,
        supabase_db_service_role_key=supabase_db_service_role_key,
        allowed_origins=allowed_origins,
        allowed_origin_regex=allowed_origin_regex,
        admin_emails=admin_emails,
        max_upload_bytes=max_upload_bytes,
        public_cache_ttl_seconds=public_cache_ttl_seconds,
        public_cache_stale_seconds=public_cache_stale_seconds,
        github_token=github_token,
        github_commit_cache_ttl_seconds=github_commit_cache_ttl_seconds,
        keepalive_url=keepalive_url,
        keepalive_interval_seconds=keepalive_interval_seconds,
    )
