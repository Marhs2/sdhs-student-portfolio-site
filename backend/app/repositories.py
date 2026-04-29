import logging
from time import sleep
from typing import Any

import httpx

from postgrest.exceptions import APIError

from .cache import TtlCache
from .config import get_settings
from .database import supabase
from .normalization import (
    clean_rich_html,
    clean_github_url,
    clean_http_url,
    clean_youtube_url,
    _normalize_tag_list,
    normalize_job,
    normalize_portfolio_item_record,
    normalize_profile_record,
)
from .security_logging import log_security_event


logger = logging.getLogger("portfolio-backend")
PROFILE_COLUMNS = (
    "id,name,des,job,school,department,track,tags,featured_rank,review_status,"
    "is_visible,GITHUB,email,img,created_at,isAdmin"
)
LEGACY_PROFILE_COLUMNS = "id,name,des,job,GITHUB,email,img,created_at,isAdmin"
PORTFOLIO_ITEM_COLUMNS = (
    "id,title,github_link,custom_link_url,des,project_role,skill_tags,"
    "created_at,youtube_link,img,owner,is_featured"
)
LEGACY_PORTFOLIO_ITEM_COLUMNS = "id,title,github_link,des,created_at,youtube_link,img,owner"
_settings = get_settings()
PUBLIC_CACHE_MAX_ENTRIES = 512
_public_cache = TtlCache(
    _settings.public_cache_ttl_seconds,
    stale_seconds=_settings.public_cache_stale_seconds,
    max_entries=PUBLIC_CACHE_MAX_ENTRIES,
)


def clear_public_cache() -> None:
    _public_cache.clear()


def _clone_profile(profile: dict[str, Any] | None) -> dict[str, Any] | None:
    if not profile:
        return None
    cloned = dict(profile)
    cloned["tags"] = list(profile.get("tags") or [])
    return cloned


def _clone_portfolio_item(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    cloned = dict(item)
    cloned["tags"] = list(item.get("tags") or [])
    return cloned


def _strip_portfolio_private_fields(item: dict[str, Any]) -> dict[str, Any]:
    public_item = dict(item)
    public_item.pop("ownerEmail", None)
    return public_item


def _filter_public_portfolio_items(
    items: list[dict[str, Any]],
    public_owner_emails: set[str] | None = None,
) -> list[dict[str, Any]]:
    allowed_owner_emails = public_owner_emails or _get_public_owner_emails()
    return [
        _strip_portfolio_private_fields(item)
        for item in items
        if (item.get("ownerEmail") or "").strip().lower() in allowed_owner_emails
    ]


def is_public_approved_profile(profile: dict[str, Any] | None) -> bool:
    return bool(profile and profile.get("isVisible") and profile.get("reviewStatus") == "approved")


def _get_public_owner_emails() -> set[str]:
    def select() -> set[str]:
        return {
            (profile.get("email") or "").strip().lower()
            for profile in _select_profiles(include_hidden=False, include_private=True)
            if is_public_approved_profile(profile)
        }

    return _public_cache.get_or_set(("public-owner-emails",), select)


def _is_missing_column_error(exc: Exception) -> bool:
    message = str(exc)
    return isinstance(exc, APIError) and (
        getattr(exc, "code", None) == "42703"
        or getattr(exc, "code", None) == "PGRST204"
        or ("column" in message.lower() and "does not exist" in message.lower())
        or ("schema cache" in message.lower() and "column" in message.lower())
    )


def _execute_with_missing_column_fallback(
    primary_query: Any,
    legacy_query: Any,
    *,
    operation: str,
    legacy_operation: str,
) -> Any:
    try:
        return _execute_query(primary_query, operation=operation)
    except APIError as exc:
        if not _is_missing_column_error(exc):
            raise
        return _execute_query(legacy_query, operation=legacy_operation)


def _apply_query_window(query: Any, *, limit: int | None = None, offset: int = 0) -> Any:
    if limit is None:
        return query
    return query.range(offset, offset + limit - 1)


def _build_profile_select_query(
    columns: str,
    *,
    school: str | None = None,
    department: str | None = None,
    track: str | None = None,
    job: str | None = None,
    sort: str = "featured",
    extended_schema: bool = True,
    include_hidden: bool = False,
    limit: int | None = None,
    offset: int = 0,
):
    query = supabase.table("userProfile").select(columns)

    if sort in {"latest", "newest"}:
        query = query.order("created_at", desc=True)
    elif sort == "name":
        query = query.order("name", desc=False)
    elif sort == "department" and extended_schema:
        query = query.order("department", desc=False).order("name", desc=False)
    elif sort == "featured" and extended_schema:
        query = query.order("featured_rank", desc=False).order("created_at", desc=True)
    else:
        query = query.order("created_at", desc=True)

    if school and extended_schema:
        query = query.eq("school", school)
    if department and extended_schema:
        query = query.eq("department", department)
    if track and extended_schema:
        query = query.eq("track", track)
    if job and extended_schema:
        query = query.eq("job", normalize_job(job))
    if not include_hidden and extended_schema:
        query = query.eq("is_visible", True).eq("review_status", "approved")

    return _apply_query_window(query, limit=limit, offset=offset)


def _trim_page(items: list[dict[str, Any]], limit: int) -> tuple[list[dict[str, Any]], bool]:
    return items[:limit], len(items) > limit


def _select_profiles(
    *,
    school: str | None = None,
    department: str | None = None,
    track: str | None = None,
    job: str | None = None,
    sort: str = "featured",
    include_hidden: bool = False,
    include_private: bool = False,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    response = _execute_with_missing_column_fallback(
        _build_profile_select_query(
            PROFILE_COLUMNS,
            school=school,
            department=department,
            track=track,
            job=job,
            sort=sort,
            extended_schema=True,
            include_hidden=include_hidden,
            limit=limit,
            offset=offset,
        ),
        _build_profile_select_query(
            LEGACY_PROFILE_COLUMNS,
            job=job,
            sort=sort,
            extended_schema=False,
            limit=limit,
            offset=offset,
        ),
        operation="profiles.select",
        legacy_operation="profiles.select_legacy",
    )

    return [
        item
        for item in (normalize_profile_record(row, include_private=include_private) for row in response.data)
        if item
    ]


def _profile_insert_payload(payload: dict[str, Any], *, email: str, extended_schema: bool = True) -> dict[str, Any]:
    row = {
        "name": payload["name"],
        "email": email,
        "des": payload.get("description", ""),
        "job": normalize_job(payload.get("job")),
        "GITHUB": clean_github_url(payload.get("github")),
        "img": clean_http_url(payload.get("imageUrl")),
    }

    if extended_schema:
        row.update(
            {
                "school": payload.get("school", ""),
                "department": payload.get("department", ""),
                "track": payload.get("track", ""),
                "tags": _normalize_tag_list(payload.get("tags")),
                "review_status": payload.get("reviewStatus", "approved"),
                "is_visible": payload.get("isVisible", True),
            }
        )

    return row


def _profile_update_payload(payload: dict[str, Any], *, extended_schema: bool = True) -> dict[str, Any]:
    raw_update = {}
    if "name" in payload:
        raw_update["name"] = payload["name"]
    if "description" in payload:
        raw_update["des"] = payload["description"]
    if "job" in payload:
        raw_update["job"] = normalize_job(payload["job"])
    if "github" in payload:
        raw_update["GITHUB"] = clean_github_url(payload["github"])
    if "imageUrl" in payload:
        raw_update["img"] = clean_http_url(payload["imageUrl"])

    if extended_schema:
        if "school" in payload:
            raw_update["school"] = payload["school"]
        if "department" in payload:
            raw_update["department"] = payload["department"]
        if "track" in payload:
            raw_update["track"] = payload["track"]
        if "tags" in payload:
            raw_update["tags"] = _normalize_tag_list(payload["tags"])
        if "featuredRank" in payload:
            raw_update["featured_rank"] = payload["featuredRank"]
        if "reviewStatus" in payload:
            raw_update["review_status"] = payload["reviewStatus"]
        if "isVisible" in payload:
            raw_update["is_visible"] = payload["isVisible"]
        if "isAdmin" in payload:
            raw_update["isAdmin"] = payload["isAdmin"]

    if payload.get("reviewStatus") == "banned":
        raw_update["is_visible"] = False

    return {key: value for key, value in raw_update.items() if value is not None}


def _build_portfolio_item_select_query(
    columns: str,
    *,
    owner_emails: list[str] | None = None,
    limit: int | None = None,
    offset: int = 0,
):
    query = supabase.table("portfoilo").select(columns).order("created_at", desc=True)
    if owner_emails is not None:
        query = query.in_("owner", owner_emails)
    return _apply_query_window(query, limit=limit, offset=offset)


def _portfolio_insert_payload(
    owner_email: str,
    payload: dict[str, Any],
    *,
    extended_schema: bool = True,
) -> dict[str, Any]:
    row = {
        "title": payload["title"],
        "des": payload.get("description", ""),
        "github_link": clean_github_url(payload.get("githubUrl")),
        "youtube_link": clean_youtube_url(payload.get("videoUrl")),
        "img": clean_http_url(payload.get("imageUrl")),
        "owner": owner_email,
    }

    if extended_schema:
        row.update(
            {
                "project_role": payload.get("contribution", ""),
                "skill_tags": _normalize_tag_list(payload.get("tags")),
                "is_featured": payload.get("isFeatured", False),
                "custom_link_url": clean_http_url(payload.get("websiteUrl") or payload.get("customLinkUrl")),
            }
        )

    return row


def _portfolio_update_payload(payload: dict[str, Any], *, extended_schema: bool = True) -> dict[str, Any]:
    raw_update = {}
    if "title" in payload:
        raw_update["title"] = payload["title"]
    if "description" in payload:
        raw_update["des"] = payload["description"]
    if "githubUrl" in payload:
        raw_update["github_link"] = clean_github_url(payload["githubUrl"])
    if "videoUrl" in payload:
        raw_update["youtube_link"] = clean_youtube_url(payload["videoUrl"])
    if "imageUrl" in payload:
        raw_update["img"] = clean_http_url(payload["imageUrl"])

    if extended_schema:
        if "contribution" in payload:
            raw_update["project_role"] = payload["contribution"]
        if "tags" in payload:
            raw_update["skill_tags"] = _normalize_tag_list(payload["tags"])
        if "isFeatured" in payload:
            raw_update["is_featured"] = payload["isFeatured"]
        if "websiteUrl" in payload:
            raw_update["custom_link_url"] = clean_http_url(payload["websiteUrl"])
        elif "customLinkUrl" in payload:
            raw_update["custom_link_url"] = clean_http_url(payload["customLinkUrl"])

    return {key: value for key, value in raw_update.items() if value is not None}


def list_profiles(
    *,
    school: str | None = None,
    department: str | None = None,
    track: str | None = None,
    job: str | None = None,
    sort: str = "featured",
    include_hidden: bool = False,
    include_private: bool = False,
) -> list[dict[str, Any]]:
    normalized_job = normalize_job(job)

    def select() -> list[dict[str, Any]]:
        return _select_profiles(
            school=school,
            department=department,
            track=track,
            job=job,
            sort=sort,
            include_hidden=include_hidden,
            include_private=include_private,
        )

    if not include_hidden and not include_private:
        normalized = _public_cache.get_or_set(
            ("profiles", school, department, track, normalized_job, sort),
            select,
        )
    else:
        normalized = select()

    if normalized_job:
        normalized = [item for item in normalized if item["job"] == normalized_job]
    if include_hidden:
        return normalized
    return [
        item
        for item in normalized
        if is_public_approved_profile(item)
    ]


def list_profiles_page(
    *,
    school: str | None = None,
    department: str | None = None,
    track: str | None = None,
    job: str | None = None,
    sort: str = "featured",
    limit: int,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], bool]:
    normalized_job = normalize_job(job)

    def select() -> list[dict[str, Any]]:
        return _select_profiles(
            school=school,
            department=department,
            track=track,
            job=job,
            sort=sort,
            include_hidden=False,
            include_private=False,
            limit=limit + 1,
            offset=offset,
        )

    normalized = _public_cache.get_or_set(
        ("profiles-page", school, department, track, normalized_job, sort, limit, offset),
        select,
    )
    if normalized_job:
        normalized = [item for item in normalized if item["job"] == normalized_job]
    public_profiles = [
        item
        for item in normalized
        if is_public_approved_profile(item)
    ]
    return _trim_page(public_profiles, limit)


def list_admin_profiles(
    *,
    review_status: str | None = None,
    visibility: str | None = None,
    search: str | None = None,
    sort: str = "featured",
) -> list[dict[str, Any]]:
    profiles = list_profiles(sort=sort, include_hidden=True, include_private=True)
    filtered = profiles

    if review_status and review_status != "all":
        filtered = [profile for profile in filtered if profile["reviewStatus"] == review_status]

    if visibility == "visible":
        filtered = [profile for profile in filtered if profile["isVisible"]]
    elif visibility == "hidden":
        filtered = [profile for profile in filtered if not profile["isVisible"]]

    normalized_search = (search or "").strip().lower()
    if normalized_search:
        filtered = [
            profile
            for profile in filtered
            if normalized_search
            in " ".join(
                [
                    profile.get("name", ""),
                    profile.get("email", ""),
                    profile.get("description", ""),
                    profile.get("job", ""),
                    profile.get("school", ""),
                    profile.get("department", ""),
                    *(profile.get("tags") or []),
                ]
            ).lower()
        ]

    return filtered


def get_profile_by_id(profile_id: int, *, include_private: bool = False) -> dict[str, Any] | None:
    def select() -> dict[str, Any] | None:
        response = _execute_with_missing_column_fallback(
            supabase.table("userProfile")
            .select(PROFILE_COLUMNS)
            .eq("id", profile_id)
            .limit(1),
            supabase.table("userProfile")
            .select(LEGACY_PROFILE_COLUMNS)
            .eq("id", profile_id)
            .limit(1),
            operation="profile.select_by_id",
            legacy_operation="profile.select_by_id_legacy",
        )
        row = response.data[0] if response.data else None
        return normalize_profile_record(row, include_private=include_private)

    return _clone_profile(
        _public_cache.get_or_set(("profile-by-id", profile_id, include_private), select),
    )


def _is_transient_supabase_error(exc: Exception) -> bool:
    if isinstance(exc, (ConnectionError, OSError, httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)):
        return True
    module_name = type(exc).__module__
    return module_name.startswith("httpcore") and "ProtocolError" in type(exc).__name__


def _execute_query(query: Any, *, operation: str, attempts: int = 2) -> Any:
    for attempt in range(1, attempts + 1):
        try:
            return query.execute()
        except Exception as exc:
            if not _is_transient_supabase_error(exc) or attempt >= attempts:
                raise

            logger.warning(
                "Transient Supabase request failed; retrying operation=%s attempt=%s error=%s",
                operation,
                attempt,
                type(exc).__name__,
            )
            log_security_event(
                "supabase.transient_retry",
                outcome="retry",
                severity="warning",
                reason=type(exc).__name__,
                operation=operation,
                attempt=attempt,
            )
            sleep(0.08 * attempt)


def get_profile_by_email(email: str, *, include_private: bool = True) -> dict[str, Any] | None:
    normalized_email = email.strip().lower()

    def select() -> dict[str, Any] | None:
        response = _execute_with_missing_column_fallback(
            supabase.table("userProfile")
            .select(PROFILE_COLUMNS)
            .eq("email", normalized_email)
            .limit(1),
            supabase.table("userProfile")
            .select(LEGACY_PROFILE_COLUMNS)
            .eq("email", normalized_email)
            .limit(1),
            operation="profile.select_by_email",
            legacy_operation="profile.select_by_email_legacy",
        )
        row = response.data[0] if response.data else None
        return normalize_profile_record(row, include_private=include_private)

    return _clone_profile(
        _public_cache.get_or_set(("profile-by-email", normalized_email, include_private), select),
    )


def create_profile(email: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = _execute_with_missing_column_fallback(
        supabase.table("userProfile")
        .insert(_profile_insert_payload(payload, email=email, extended_schema=True)),
        supabase.table("userProfile")
        .insert(_profile_insert_payload(payload, email=email, extended_schema=False)),
        operation="profile.insert",
        legacy_operation="profile.insert_legacy",
    )
    row = response.data[0] if response.data else None
    clear_public_cache()
    return normalize_profile_record(row, include_private=True) or {}


def update_profile(profile_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    clean_update = _profile_update_payload(payload, extended_schema=True)
    try:
        response = _execute_query(
            supabase.table("userProfile")
            .update(clean_update)
            .eq("id", profile_id),
            operation="profile.update",
        )
    except APIError as exc:
        if not _is_missing_column_error(exc):
            raise
        clean_update = _profile_update_payload(payload, extended_schema=False)
        if not clean_update:
            return get_profile_by_id(profile_id, include_private=True) or {}
        response = _execute_query(
            supabase.table("userProfile")
            .update(clean_update)
            .eq("id", profile_id),
            operation="profile.update_legacy",
        )
    row = response.data[0] if response.data else None
    clear_public_cache()
    return normalize_profile_record(row, include_private=True) or {}


def delete_profile(profile_id: int) -> bool:
    profile = get_profile_by_id(profile_id, include_private=True)
    if not profile:
        return False

    owner_email = profile.get("email", "")
    if owner_email:
        supabase.table("portfoilo").delete().eq("owner", owner_email).execute()

    supabase.table("userHtml").delete().eq("owner_id", profile_id).execute()
    response = supabase.table("userProfile").delete().eq("id", profile_id).execute()
    deleted = bool(response.data)
    if deleted:
        clear_public_cache()
    return deleted


def get_profile_html(profile_id: int) -> str:
    def select() -> str:
        response = _execute_query(
            supabase.table("userHtml")
            .select("HTML")
            .eq("owner_id", profile_id)
            .limit(1),
            operation="profile_html.select",
        )
        if not response.data:
            return ""
        return clean_rich_html(response.data[0].get("HTML", ""))

    return _public_cache.get_or_set(("profile-html", profile_id), select)


def save_profile_html(profile_id: int, html: str) -> str:
    clean_html = clean_rich_html(html)
    existing = (
        supabase.table("userHtml")
        .select("id")
        .eq("owner_id", profile_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        response = (
            supabase.table("userHtml")
            .update({"HTML": clean_html})
            .eq("owner_id", profile_id)
            .execute()
        )
    else:
        response = (
            supabase.table("userHtml")
            .insert({"owner_id": profile_id, "HTML": clean_html})
            .execute()
        )

    if not response.data:
        clear_public_cache()
        return clean_html
    clear_public_cache()
    return clean_rich_html(response.data[0].get("HTML", clean_html))


def list_portfolio_items(*, include_private: bool = False) -> list[dict[str, Any]]:
    def select() -> list[dict[str, Any]]:
        response = _execute_with_missing_column_fallback(
            _build_portfolio_item_select_query(PORTFOLIO_ITEM_COLUMNS),
            _build_portfolio_item_select_query(LEGACY_PORTFOLIO_ITEM_COLUMNS),
            operation="portfolio_items.select",
            legacy_operation="portfolio_items.select_legacy",
        )
        return [
            item
            for item in (normalize_portfolio_item_record(row, include_private=True) for row in response.data)
            if item
        ]

    if include_private:
        return select()
    return _public_cache.get_or_set(
        ("portfolio-items-public",),
        lambda: _filter_public_portfolio_items(select(), _get_public_owner_emails()),
    )


def list_portfolio_items_page(
    *,
    limit: int,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], bool]:
    public_owner_emails = sorted(_get_public_owner_emails())
    if not public_owner_emails:
        return [], False

    def select() -> list[dict[str, Any]]:
        response = _execute_with_missing_column_fallback(
            _build_portfolio_item_select_query(
                PORTFOLIO_ITEM_COLUMNS,
                owner_emails=public_owner_emails,
                limit=limit + 1,
                offset=offset,
            ),
            _build_portfolio_item_select_query(
                LEGACY_PORTFOLIO_ITEM_COLUMNS,
                owner_emails=public_owner_emails,
                limit=limit + 1,
                offset=offset,
            ),
            operation="portfolio_items.select_page",
            legacy_operation="portfolio_items.select_page_legacy",
        )
        return [
            item
            for item in (normalize_portfolio_item_record(row, include_private=True) for row in response.data)
            if item
        ]

    items = _public_cache.get_or_set(
        ("portfolio-items-public-page", tuple(public_owner_emails), limit, offset),
        lambda: _filter_public_portfolio_items(select(), set(public_owner_emails)),
    )
    return _trim_page(items, limit)


def list_portfolio_items_by_owner(
    owner_email: str,
    *,
    include_private: bool = False,
    public_owner_verified: bool = False,
) -> list[dict[str, Any]]:
    def select() -> list[dict[str, Any]]:
        response = _execute_with_missing_column_fallback(
            _build_portfolio_item_select_query(PORTFOLIO_ITEM_COLUMNS).eq("owner", owner_email),
            _build_portfolio_item_select_query(LEGACY_PORTFOLIO_ITEM_COLUMNS).eq("owner", owner_email),
            operation="portfolio_items.select_by_owner",
            legacy_operation="portfolio_items.select_by_owner_legacy",
        )
        return [
            item
            for item in (normalize_portfolio_item_record(row, include_private=include_private) for row in response.data)
            if item
        ]

    if include_private:
        return select()
    normalized_owner = owner_email.strip().lower()
    if not public_owner_verified and normalized_owner not in _get_public_owner_emails():
        return []
    return _public_cache.get_or_set(
        ("portfolio-items-by-owner-public", normalized_owner),
        lambda: [_strip_portfolio_private_fields(item) for item in select()],
    )


def get_portfolio_item_by_id(item_id: int, *, include_private: bool = False) -> dict[str, Any] | None:
    def select() -> dict[str, Any] | None:
        response = _execute_with_missing_column_fallback(
            supabase.table("portfoilo")
            .select(PORTFOLIO_ITEM_COLUMNS)
            .eq("id", item_id)
            .limit(1),
            supabase.table("portfoilo")
            .select(LEGACY_PORTFOLIO_ITEM_COLUMNS)
            .eq("id", item_id)
            .limit(1),
            operation="portfolio_item.select_by_id",
            legacy_operation="portfolio_item.select_by_id_legacy",
        )
        row = response.data[0] if response.data else None
        return normalize_portfolio_item_record(row, include_private=include_private)

    return _clone_portfolio_item(
        _public_cache.get_or_set(("portfolio-item-by-id", item_id, include_private), select),
    )


def create_portfolio_item(owner_email: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = _execute_with_missing_column_fallback(
        supabase.table("portfoilo")
        .insert(_portfolio_insert_payload(owner_email, payload, extended_schema=True)),
        supabase.table("portfoilo")
        .insert(_portfolio_insert_payload(owner_email, payload, extended_schema=False)),
        operation="portfolio_item.insert",
        legacy_operation="portfolio_item.insert_legacy",
    )
    row = response.data[0] if response.data else None
    clear_public_cache()
    return normalize_portfolio_item_record(row, include_private=True) or {}


def update_portfolio_item(item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    clean_update = _portfolio_update_payload(payload, extended_schema=True)
    try:
        response = _execute_query(
            supabase.table("portfoilo").update(clean_update).eq("id", item_id),
            operation="portfolio_item.update",
        )
    except APIError as exc:
        if not _is_missing_column_error(exc):
            raise
        clean_update = _portfolio_update_payload(payload, extended_schema=False)
        if not clean_update:
            return get_portfolio_item_by_id(item_id, include_private=True) or {}
        response = _execute_query(
            supabase.table("portfoilo").update(clean_update).eq("id", item_id),
            operation="portfolio_item.update_legacy",
        )
    row = response.data[0] if response.data else None
    clear_public_cache()
    return normalize_portfolio_item_record(row, include_private=True) or {}


def delete_portfolio_item(item_id: int) -> bool:
    response = supabase.table("portfoilo").delete().eq("id", item_id).execute()
    deleted = bool(response.data)
    if deleted:
        clear_public_cache()
    return deleted
