import httpx
from contextlib import suppress
from inspect import signature
from typing import Any

from supabase import ClientOptions, create_client

from .config import get_settings


settings = get_settings()
supabase_http_client = httpx.Client(
    http2=False,
    timeout=httpx.Timeout(connect=5.0, read=20.0, write=20.0, pool=5.0),
)
auth_http_client = httpx.Client(
    http2=False,
    timeout=httpx.Timeout(connect=1.0, read=2.0, write=2.0, pool=1.0),
)
client_options_kwargs = {
    "postgrest_client_timeout": httpx.Timeout(connect=5.0, read=20.0, write=20.0, pool=5.0),
    "storage_client_timeout": 20,
}
if "httpx_client" in signature(ClientOptions).parameters:
    client_options_kwargs["httpx_client"] = supabase_http_client

supabase = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
    options=ClientOptions(**client_options_kwargs),
)


def get_auth_user(access_token: str) -> dict:
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {access_token}",
    }

    response = auth_http_client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def _close_once(resources: list[Any]) -> None:
    seen_ids: set[int] = set()
    for resource in resources:
        if resource is None or id(resource) in seen_ids:
            continue
        seen_ids.add(id(resource))
        close = getattr(resource, "close", None)
        if callable(close):
            with suppress(Exception):
                close()


def close_supabase_clients() -> None:
    auth_close = getattr(getattr(supabase, "auth", None), "close", None)
    if callable(auth_close):
        with suppress(Exception):
            auth_close()

    _close_once(
        [
            auth_http_client,
            supabase_http_client,
            getattr(getattr(supabase, "postgrest", None), "session", None),
            getattr(getattr(supabase, "storage", None), "session", None),
            getattr(getattr(supabase, "storage", None), "_client", None),
            getattr(getattr(supabase, "auth", None), "_http_client", None),
        ],
    )


def ensure_public_image_bucket() -> None:
    try:
        supabase.storage.update_bucket(settings.image_bucket, {"public": True})
    except Exception:
        pass
