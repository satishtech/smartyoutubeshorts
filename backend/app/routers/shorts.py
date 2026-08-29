"""Short routes: generate (ffmpeg), list, stream, download, thumbnail, and project-wide ZIP export."""
import io
import logging
import zipfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.highlight_segment import HighlightSegment
from app.models.project import Project, ProjectStatus
from app.models.short import Short
from app.models.user import User
from app.schemas.short import ShortGenerateRequest, ShortResponse
from app.services.pipeline import run_shorts_generation_pipeline

logger = logging.getLogger(__name__)

projects_router = APIRouter(prefix="/api/projects", tags=["shorts"])
shorts_router = APIRouter(prefix="/api/shorts", tags=["shorts"])

CHUNK_SIZE = 1024 * 1024


def _get_owned_project(db: Session, project_id: int, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError("Project")
    if project.user_id != user.id:
        raise ForbiddenError("You do not have access to this project")
    return project


def _get_owned_short(db: Session, short_id: int, user: User) -> Short:
    short = db.query(Short).filter(Short.id == short_id).first()
    if not short:
        raise NotFoundError("Short")
    if short.project.user_id != user.id:
        raise ForbiddenError("You do not have access to this short")
    return short


def _build_short_response(short: Short) -> ShortResponse:
    """Build a ShortResponse, joining in the linked HighlightSegment's title/timing."""
    highlight = short.highlight_segment
    return ShortResponse(
        id=short.id,
        project_id=short.project_id,
        highlight_segment_id=short.highlight_segment_id,
        duration_seconds=short.duration_seconds,
        has_subtitles=short.has_subtitles,
        has_broll=short.has_broll,
        has_thumbnail=bool(short.thumbnail_path),
        status=short.status,
        highlight_title=highlight.title if highlight else None,
        highlight_start_time=highlight.start_time if highlight else None,
        highlight_end_time=highlight.end_time if highlight else None,
        created_at=short.created_at,
        updated_at=short.updated_at,
    )


@projects_router.post("/{project_id}/shorts/generate", status_code=202, response_model=dict)
async def generate_shorts(
    project_id: int,
    payload: ShortGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Kick off (async, via BackgroundTasks) ffmpeg rendering of one or more Shorts."""
    project = _get_owned_project(db, project_id, current_user)

    highlight_count = db.query(HighlightSegment).filter(HighlightSegment.project_id == project_id).count()
    if highlight_count == 0:
        raise BadRequestError("Project has no highlight segments; run highlight detection first")

    if payload.highlight_segment_ids:
        owned_count = (
            db.query(HighlightSegment)
            .filter(
                HighlightSegment.project_id == project_id,
                HighlightSegment.id.in_(payload.highlight_segment_ids),
            )
            .count()
        )
        if owned_count != len(set(payload.highlight_segment_ids)):
            raise BadRequestError("One or more highlight_segment_ids do not belong to this project")

    project.status = ProjectStatus.generating_shorts
    project.status_message = "Shorts generation queued"
    db.add(project)
    db.commit()

    background_tasks.add_task(run_shorts_generation_pipeline, project_id, payload.highlight_segment_ids)
    return {"detail": "Shorts generation started", "project_id": project_id}


@projects_router.get("/{project_id}/shorts", response_model=list[ShortResponse])
async def list_shorts(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ShortResponse]:
    """List all Shorts generated for a project."""
    _get_owned_project(db, project_id, current_user)
    shorts = db.query(Short).filter(Short.project_id == project_id).all()
    return [_build_short_response(s) for s in shorts]


def _iter_file_range(path: Path, start: int, end: int):
    with open(path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = f.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@shorts_router.get("/{short_id}/stream")
async def stream_short(
    short_id: int,
    range: str | None = Header(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a Short's video with HTTP Range support (for scrubbing in the browser preview)."""
    short = _get_owned_short(db, short_id, current_user)
    if not short.file_path:
        raise NotFoundError("Short file")
    path = Path(short.file_path)
    if not path.exists():
        raise NotFoundError("Short file")

    file_size = path.stat().st_size
    start, end = 0, file_size - 1
    status_code = 200
    headers = {"Accept-Ranges": "bytes", "Content-Type": "video/mp4"}

    if range:
        try:
            range_value = range.replace("bytes=", "")
            start_str, end_str = (range_value.split("-") + [""])[:2]
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except ValueError as exc:
            raise BadRequestError("Invalid Range header") from exc
        status_code = 206
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    headers["Content-Length"] = str(end - start + 1)
    return StreamingResponse(
        _iter_file_range(path, start, end), status_code=status_code, headers=headers, media_type="video/mp4"
    )


@shorts_router.get("/{short_id}/download")
async def download_short(
    short_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> FileResponse:
    """Download a single Short as an attachment."""
    short = _get_owned_short(db, short_id, current_user)
    if not short.file_path or not Path(short.file_path).exists():
        raise NotFoundError("Short file")
    filename = f"short_{short.id}.mp4"
    return FileResponse(short.file_path, media_type="video/mp4", filename=filename)


@projects_router.get("/{project_id}/thumbnail")
async def get_project_thumbnail(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> FileResponse:
    """Stream a project's thumbnail JPEG."""
    project = _get_owned_project(db, project_id, current_user)
    if not project.thumbnail_path or not Path(project.thumbnail_path).exists():
        raise NotFoundError("Project thumbnail")
    return FileResponse(project.thumbnail_path, media_type="image/jpeg")


@shorts_router.get("/{short_id}/thumbnail")
async def get_short_thumbnail(
    short_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> FileResponse:
    """Stream a Short's thumbnail JPEG."""
    short = _get_owned_short(db, short_id, current_user)
    if not short.thumbnail_path or not Path(short.thumbnail_path).exists():
        raise NotFoundError("Short thumbnail")
    return FileResponse(short.thumbnail_path, media_type="image/jpeg")


@projects_router.get("/{project_id}/download-zip")
async def download_zip(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """Stream all ready Shorts for a project as a single ZIP archive."""
    project = _get_owned_project(db, project_id, current_user)
    shorts = (
        db.query(Short)
        .filter(Short.project_id == project_id, Short.file_path.isnot(None))
        .all()
    )
    existing = [s for s in shorts if s.file_path and Path(s.file_path).exists()]
    if not existing:
        raise NotFoundError("No ready shorts to export for this project")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as zf:
        for short in existing:
            zf.write(short.file_path, arcname=f"short_{short.id}.mp4")
    buffer.seek(0)

    safe_title = "".join(c for c in project.title if c.isalnum() or c in (" ", "-", "_")).strip() or "project"
    filename = f"{safe_title}_shorts.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
