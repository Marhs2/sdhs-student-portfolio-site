from fastapi import APIRouter, Depends

from ..auth import ALLOWED_EMAIL_DOMAIN, require_server_admin
from ..config import get_settings
from ..department_settings import add_department, delete_department, list_departments
from ..schemas import DepartmentPayload
from ..security_logging import log_security_event


router = APIRouter(prefix="/api/server-admin/settings", tags=["server-admin-settings"])


@router.get("")
def get_server_admin_settings(admin: dict = Depends(require_server_admin)) -> dict:
    settings = get_settings()
    return {
        "allowedEmailDomain": ALLOWED_EMAIL_DOMAIN,
        "currentAdminSource": "environment",
        "departments": list_departments(),
        "maxUploadBytes": settings.max_upload_bytes,
        "controlsAdminGrants": True,
    }


@router.post("/departments")
def post_server_admin_department(
    payload: DepartmentPayload,
    admin: dict = Depends(require_server_admin),
) -> dict:
    departments = add_department(payload.name)
    log_security_event(
        "settings.department_added",
        outcome="allowed",
        actor_email=admin.get("email"),
        target_type="department",
        target_id=payload.name.strip(),
    )
    return {"departments": departments}


@router.delete("/departments/{department_name}")
def delete_server_admin_department(
    department_name: str,
    admin: dict = Depends(require_server_admin),
) -> dict:
    departments = delete_department(department_name)
    log_security_event(
        "settings.department_deleted",
        outcome="allowed",
        actor_email=admin.get("email"),
        target_type="department",
        target_id=department_name.strip(),
    )
    return {"departments": departments}
