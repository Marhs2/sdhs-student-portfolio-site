from fastapi import APIRouter, Depends

from ..auth import ALLOWED_EMAIL_DOMAIN, require_admin
from ..config import get_settings

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])


@router.get("")
def get_admin_settings(admin: dict = Depends(require_admin)) -> dict:
    settings = get_settings()
    admin_email = (admin.get("email") or "").strip().lower()

    return {
        "allowedEmailDomain": ALLOWED_EMAIL_DOMAIN,
        "currentAdminEmail": admin_email,
        "currentAdminSource": "environment"
        if admin_email in settings.admin_emails
        else "profile",
        "maxUploadBytes": settings.max_upload_bytes,
    }
