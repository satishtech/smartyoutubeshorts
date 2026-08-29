"""Upload / input validation helpers shared by routers."""
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.exceptions import BadRequestError

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
ALLOWED_VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    "video/x-msvideo",
}


def validate_upload_file(file: UploadFile) -> None:
    """Validate a video upload's filename extension and declared content-type.

    Size is enforced separately while streaming to disk (see save_upload_streamed).
    """
    if not file.filename:
        raise BadRequestError("Uploaded file has no filename")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise BadRequestError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
        )
    if file.content_type and file.content_type not in ALLOWED_VIDEO_CONTENT_TYPES:
        raise BadRequestError(f"Unsupported content type '{file.content_type}'")


async def save_upload_streamed(file: UploadFile, dest_path: Path) -> int:
    """Stream an UploadFile to disk in chunks, enforcing MAX_UPLOAD_SIZE_MB. Returns bytes written."""
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    chunk_size = 1024 * 1024
    with open(dest_path, "wb") as out:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                out.close()
                dest_path.unlink(missing_ok=True)
                raise BadRequestError(f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB")
            out.write(chunk)
    if total == 0:
        dest_path.unlink(missing_ok=True)
        raise BadRequestError("Uploaded file is empty")
    return total


def to_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
