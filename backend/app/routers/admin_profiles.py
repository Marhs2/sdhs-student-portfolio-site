from fastapi import APIRouter, Depends, Query

from ..auth import require_admin
from ..repositories import list_admin_profiles, update_profile
from ..schemas import AdminProfileUpdatePayload
from ..security_logging import log_security_event


router = APIRouter(prefix="/api/admin/profiles", tags=["admin-profiles"])
REGULAR_ADMIN_HIDDEN_FIELDS = {"isAdmin"}


def _regular_admin_profile_payload(profile: dict) -> dict:
    return {
        key: value
        for key, value in profile.items()
        if key not in REGULAR_ADMIN_HIDDEN_FIELDS
    }


@router.get("")
def get_admin_profiles(
    review_status: str | None = Query(default=None),
    visibility: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="featured"),
    _admin: dict = Depends(require_admin),
) -> list[dict]:
    profiles = list_admin_profiles(
        review_status=review_status,
        visibility=visibility,
        search=search,
        sort=sort,
    )
    return [_regular_admin_profile_payload(profile) for profile in profiles]


@router.put("/{profile_id}")
def put_admin_profile(
    profile_id: int,
    payload: AdminProfileUpdatePayload,
    admin: dict = Depends(require_admin),
) -> dict:
    update_payload = payload.model_dump(exclude_unset=True)
    updated = update_profile(profile_id, update_payload)
    log_security_event(
        "admin.profile_curation_updated",
        outcome="allowed",
        actor_email=admin.get("email"),
        actor_profile_id=admin.get("id"),
        target_type="profile",
        target_id=profile_id,
        changed_fields=sorted(update_payload.keys()),
    )
    return _regular_admin_profile_payload(updated)
