from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from ..auth import (
    can_view_profile,
    get_current_user,
    get_optional_profile,
    require_profile_write_access,
)
from ..config import get_settings
from ..repositories import (
    create_profile,
    delete_profile,
    get_profile_by_email,
    get_profile_by_id,
    get_profile_html,
    is_public_approved_profile,
    list_profiles_page,
    list_portfolio_items_by_owner,
    list_profiles,
    save_profile_html,
    update_profile,
)
from ..schemas import HtmlContentPayload, ProfilePayload, ProfileUpdatePayload
from ..security_logging import log_security_event


router = APIRouter(prefix="/api/profiles", tags=["profiles"])
PUBLIC_PROFILE_HIDDEN_FIELDS = {"email", "isAdmin", "isVisible", "reviewStatus"}


def _is_owner_or_admin(profile: dict | None, viewer: dict | None) -> bool:
    return bool(
        profile
        and viewer
        and (viewer.get("isAdmin") or viewer.get("email") == profile.get("email"))
    )


def _public_profile_payload(profile: dict) -> dict:
    return {
        key: value
        for key, value in profile.items()
        if key not in PUBLIC_PROFILE_HIDDEN_FIELDS
    }


def _profile_response_payload(profile: dict, viewer: dict | None = None) -> dict:
    if _is_owner_or_admin(profile, viewer):
        return dict(profile)
    return _public_profile_payload(profile)


@router.get("")
def get_profiles(
    response: Response,
    school: str | None = Query(default=None),
    department: str | None = Query(default=None),
    track: str | None = Query(default=None),
    job: str | None = Query(default=None),
    sort: str = Query(default="featured"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    response.headers["Cache-Control"] = get_settings().public_cache_control_header
    if limit is None:
        profiles = list_profiles(
            school=school,
            department=department,
            track=track,
            job=job,
            sort=sort,
            include_private=False,
        )
        response.headers["X-Result-Count"] = str(len(profiles))
        return [_public_profile_payload(profile) for profile in profiles]

    page, has_more = list_profiles_page(
        school=school,
        department=department,
        track=track,
        job=job,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Result-Count"] = str(len(page))
    if has_more:
        response.headers["X-Next-Offset"] = str(offset + limit)
    return [_public_profile_payload(profile) for profile in page]


@router.post("", status_code=status.HTTP_201_CREATED)
def post_profile(
    payload: ProfilePayload,
    user: dict = Depends(get_current_user),
) -> dict:
    existing = get_profile_by_email(user["email"])
    if existing:
        log_security_event(
            "profile.create_conflict",
            outcome="blocked",
            severity="warning",
            actor_email=user["email"],
            target_type="profile",
            target_id=existing.get("id"),
            reason="profile_already_exists",
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 프로필이 존재합니다.",
        )
    created = create_profile(user["email"], payload.model_dump(exclude={"createProfileConsent"}))
    log_security_event(
        "profile.created",
        outcome="allowed",
        actor_email=user["email"],
        target_type="profile",
        target_id=created.get("id"),
    )
    return created


@router.get("/{profile_id}/bundle")
def get_profile_bundle(
    profile_id: int,
    viewer: dict | None = Depends(get_optional_profile),
) -> dict:
    profile = get_profile_by_id(profile_id, include_private=True)
    if not can_view_profile(profile, viewer):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )

    owner_email = profile["email"]
    return {
        "profile": _profile_response_payload(profile, viewer),
        "html": get_profile_html(profile_id),
        "portfolioItems": list_portfolio_items_by_owner(
            owner_email,
            include_private=False,
            public_owner_verified=is_public_approved_profile(profile),
        ),
    }


@router.get("/{profile_id}")
def get_profile(
    profile_id: int,
    viewer: dict | None = Depends(get_optional_profile),
) -> dict:
    profile = get_profile_by_id(profile_id, include_private=True)
    if not can_view_profile(profile, viewer):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )
    return _profile_response_payload(profile, viewer)


@router.put("/{profile_id}")
def put_profile(
    profile_id: int,
    payload: ProfileUpdatePayload,
    profile: dict = Depends(require_profile_write_access),
) -> dict:
    update_payload = payload.model_dump(exclude_unset=True)
    updated = update_profile(profile_id, update_payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )
    log_security_event(
        "profile.updated",
        outcome="allowed",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="profile",
        target_id=profile_id,
        changed_fields=sorted(update_payload.keys()),
        admin_override=bool(profile.get("isAdmin") and profile.get("id") != profile_id),
    )
    return updated


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile_route(
    profile_id: int,
    profile: dict = Depends(require_profile_write_access),
) -> None:
    deleted = delete_profile(profile_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )
    log_security_event(
        "profile.deleted",
        outcome="allowed",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="profile",
        target_id=profile_id,
        admin_override=bool(profile.get("isAdmin") and profile.get("id") != profile_id),
    )


@router.get("/{profile_id}/html")
def get_profile_html_content(
    profile_id: int,
    viewer: dict | None = Depends(get_optional_profile),
) -> dict:
    profile = get_profile_by_id(profile_id, include_private=True)
    if not can_view_profile(profile, viewer):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )
    return {"html": get_profile_html(profile_id)}


@router.get("/{profile_id}/portfolio-items")
def get_profile_portfolio_items(
    profile_id: int,
    viewer: dict | None = Depends(get_optional_profile),
) -> list[dict]:
    profile = get_profile_by_id(profile_id, include_private=True)
    if not can_view_profile(profile, viewer):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )
    return list_portfolio_items_by_owner(
        profile["email"],
        include_private=False,
        public_owner_verified=is_public_approved_profile(profile),
    )


@router.put("/{profile_id}/html")
def put_profile_html_content(
    profile_id: int,
    payload: HtmlContentPayload,
    profile: dict = Depends(require_profile_write_access),
) -> dict:
    html = save_profile_html(profile_id, payload.html)
    log_security_event(
        "profile.html_updated",
        outcome="allowed",
        actor_email=profile.get("email"),
        actor_profile_id=profile.get("id"),
        target_type="profile",
        target_id=profile_id,
        input_bytes=len(payload.html.encode("utf-8")),
        stored_bytes=len(html.encode("utf-8")),
        sanitized=payload.html != html,
        admin_override=bool(profile.get("isAdmin") and profile.get("id") != profile_id),
    )
    return {"html": html}
