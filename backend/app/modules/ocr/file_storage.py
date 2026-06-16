import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import BusinessException
from app.modules.ocr.ocr_constants import SUPPORTED_IMAGE_EXTENSIONS, SUPPORTED_IMAGE_MIME_TYPES


async def save_upload_image(*, user_id: int, upload: UploadFile) -> tuple[str, str, str, int]:
    settings = get_settings()
    original_name = upload.filename or "upload.png"
    suffix = Path(original_name).suffix.lower()

    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        raise BusinessException(code=4006, message="unsupported image type, only png/jpg/jpeg")

    content_type = (upload.content_type or "").lower()
    if content_type and content_type not in SUPPORTED_IMAGE_MIME_TYPES:
        raise BusinessException(code=4006, message="unsupported image mime type")

    data = await upload.read()
    max_bytes = settings.ocr_max_file_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise BusinessException(code=4007, message="file too large")

    base_dir = Path(settings.upload_dir)
    user_dir = base_dir / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    file_path = user_dir / stored_name
    file_path.write_bytes(data)

    return str(file_path), original_name, content_type or suffix, len(data)