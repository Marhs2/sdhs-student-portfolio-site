from fastapi import APIRouter, Depends

from ..auth import get_current_profile, get_current_user, is_configured_admin_email
from ..repositories import get_profile_by_email

router = APIRouter(prefix="/api/me", tags=["auth"])


@router.get("/context")
def get_my_context(user: dict = Depends(get_current_user)) -> dict:
    profile = get_profile_by_email(user["email"], include_private=True)
    is_config_admin = is_configured_admin_email(user["email"])
    if not profile:
        return {
            "email": user["email"],
            "isAdmin": is_config_admin,
            "isConfigAdmin": is_config_admin,
            "profileId": None,
            "hasProfile": False,
        }

    return {
        "email": profile.get("email"),
        "isAdmin": bool(profile.get("isAdmin")) or is_config_admin,
        "isConfigAdmin": is_config_admin,
        "profileId": profile.get("id"),
        "hasProfile": True,
    }


@router.get("/profile")
def get_my_profile(profile: dict = Depends(get_current_profile)) -> dict:
    return profile
