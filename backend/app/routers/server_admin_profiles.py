from fastapi import APIRouter, Depends, Query

from ..auth import require_server_admin
from ..repositories import list_admin_profiles, update_profile
from ..schemas import ServerAdminProfileUpdatePayload
from ..security_logging import log_security_event


router = APIRouter(prefix="/api/server-admin/profiles", tags=["server-admin-profiles"])


@router.get("")
def get_server_admin_profiles(
    review_status: str | None = Query(default=None),
    visibility: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="featured"),
    _admin: dict = Depends(require_server_admin),
) -> list[dict]:
    return list_admin_profiles(
        review_status=review_status,
        visibility=visibility,
        search=search,
        sort=sort,
    )


@router.put("/{profile_id}")
def put_server_admin_profile(
    profile_id: int,
    payload: ServerAdminProfileUpdatePayload,
    admin: dict = Depends(require_server_admin),
) -> dict:
    update_payload = payload.model_dump(exclude_unset=True)
    updated = update_profile(profile_id, update_payload)
    log_security_event(
        "server_admin.profile_updated",
        outcome="allowed",
        actor_email=admin.get("email"),
        actor_profile_id=admin.get("id"),
        target_type="profile",
        target_id=profile_id,
        changed_fields=sorted(update_payload.keys()),
        privileged_fields=sorted(
            field
            for field in update_payload
            if field in {"isAdmin", "school", "department", "track"}
        ),
    )
    return updated
