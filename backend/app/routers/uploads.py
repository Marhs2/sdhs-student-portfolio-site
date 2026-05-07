import importlib.util
import re
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..auth import get_current_user
from ..config import get_settings
from ..security_logging import log_security_event


router = APIRouter(prefix="/api/uploads", tags=["uploads"])
settings = get_settings()
has_multipart = importlib.util.find_spec("multipart") is not None
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _safe_upload_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9-]+", "_", value or "").strip("_-")
    return normalized or "user"


def _profile_image_file_path(upload_dir: Path, user_id: str, extension: str) -> Path:
    return upload_dir / "profiles" / f"{_safe_upload_id(user_id)}{extension}"


def _profile_image_public_url(user_id: str, extension: str, *, version_ms: int) -> str:
    return f"/uploads/profiles/{_safe_upload_id(user_id)}{extension}?v={version_ms}"


def _detect_supported_image_content_type(contents: bytes) -> str:
    if contents.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(contents) >= 12 and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return "image/webp"
    return ""


if has_multipart:

    @router.post("/profile-image")
    async def upload_profile_image(
        file: UploadFile = File(...),
        user: dict = Depends(get_current_user),
    ) -> dict:
        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            log_security_event(
                "upload.profile_image_rejected",
                outcome="blocked",
                severity="warning",
                actor_email=user.get("email"),
                reason="unsupported_declared_content_type",
                declared_content_type=file.content_type,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JPEG, PNG, WEBP 이미지만 업로드할 수 있습니다.",
            )

        contents = await file.read(settings.max_upload_bytes + 1)
        if len(contents) > settings.max_upload_bytes:
            log_security_event(
                "upload.profile_image_rejected",
                outcome="blocked",
                severity="warning",
                actor_email=user.get("email"),
                reason="file_too_large",
                bytes_read=len(contents),
                max_upload_bytes=settings.max_upload_bytes,
                declared_content_type=file.content_type,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이미지는 최대 {settings.max_upload_bytes // (1024 * 1024)}MB까지 업로드할 수 있습니다.",
            )
        if not contents:
            log_security_event(
                "upload.profile_image_rejected",
                outcome="blocked",
                severity="warning",
                actor_email=user.get("email"),
                reason="empty_file",
                declared_content_type=file.content_type,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="빈 파일은 업로드할 수 없습니다.",
            )

        detected_type = _detect_supported_image_content_type(contents)

        if detected_type != file.content_type:
            log_security_event(
                "upload.profile_image_rejected",
                outcome="blocked",
                severity="warning",
                actor_email=user.get("email"),
                reason="content_type_mismatch",
                declared_content_type=file.content_type,
                detected_content_type=detected_type,
                bytes_read=len(contents),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="업로드된 파일 형식이 올바르지 않습니다.",
            )

        extension = IMAGE_EXTENSIONS.get(detected_type, "")
        file_path = _profile_image_file_path(settings.upload_dir, user["id"], extension)
        public_url = _profile_image_public_url(
            user["id"],
            extension,
            version_ms=int(time.time() * 1000),
        )

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(contents)
            log_security_event(
                "upload.profile_image_stored",
                outcome="allowed",
                actor_email=user.get("email"),
                actor_profile_id=user.get("id"),
                target_type="local_upload",
                target_id=str(file_path),
                detected_content_type=detected_type,
                bytes_read=len(contents),
            )
            return {
                "imageUrl": public_url,
                "message": "이미지가 업로드되었습니다.",
            }
        except Exception as exc:
            log_security_event(
                "upload.profile_image_failed",
                outcome="error",
                severity="error",
                actor_email=user.get("email"),
                target_type="local_upload",
                target_id=str(file_path),
                reason=type(exc).__name__,
                detected_content_type=detected_type,
                bytes_read=len(contents),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이미지를 업로드하지 못했습니다.",
            ) from exc

else:

    @router.post("/profile-image")
    async def upload_profile_image_unavailable() -> dict:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="python-multipart가 설치되지 않아 이미지 업로드를 사용할 수 없습니다.",
        )
