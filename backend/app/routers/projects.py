"""Project routes: create (upload or YouTube URL), list, get, delete, status polling."""
import logging
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.project import Project, ProjectStatus, SourceType
from app.models.user import User
from app.schemas.project import ProjectListResponse, ProjectResponse, ProjectStatusResponse
from app.services.pipeline import run_import_pipeline
from app.services.storage import project_dir, source_video_path
from app.services.validation import save_upload_streamed, to_bool, validate_upload_file
from app.services.youtube_import import validate_youtube_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_owned_project(db: Session, project_id: int, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError("Project")
    if project.user_id != user.id:
        raise ForbiddenError("You do not have access to this project")
    return project


@router.post("", status_code=201, response_model=ProjectResponse)
async def create_project(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    """Create a project either via multipart file upload or a JSON {youtube_url} body."""
    content_type = request.headers.get("content-type", "")

    title: str | None
    youtube_url: str | None
    num_shorts_requested: int
    burn_subtitles: bool
    use_broll: bool
    upload_file = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        title = (form.get("title") or None)
        youtube_url = (form.get("youtube_url") or None)
        num_shorts_requested = int(form.get("num_shorts_requested") or 3)
        burn_subtitles = to_bool(form.get("burn_subtitles"), default=True)
        use_broll = to_bool(form.get("use_broll"), default=False)
        candidate = form.get("file")
        if candidate is not None and getattr(candidate, "filename", None):
            upload_file = candidate
    elif content_type.startswith("application/json"):
        body = await request.json()
        title = body.get("title")
        youtube_url = body.get("youtube_url")
        num_shorts_requested = int(body.get("num_shorts_requested") or 3)
        burn_subtitles = bool(body.get("burn_subtitles", True))
        use_broll = bool(body.get("use_broll", False))
    else:
        raise BadRequestError("Content-Type must be multipart/form-data or application/json")

    if not (1 <= num_shorts_requested <= 10):
        raise BadRequestError("num_shorts_requested must be between 1 and 10")

    if upload_file and youtube_url:
        raise BadRequestError("Provide either a file upload or a youtube_url, not both")
    if not upload_file and not youtube_url:
        raise BadRequestError("Provide either a file upload or a youtube_url")

    if youtube_url:
        validate_youtube_url(youtube_url)
        project = Project(
            user_id=current_user.id,
            title=title or "Untitled YouTube import",
            source_type=SourceType.youtube_url,
            source_url=youtube_url,
            status=ProjectStatus.pending,
            num_shorts_requested=num_shorts_requested,
            burn_subtitles=burn_subtitles,
            use_broll=use_broll,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    else:
        validate_upload_file(upload_file)
        project = Project(
            user_id=current_user.id,
            title=title or upload_file.filename,
            source_type=SourceType.upload,
            status=ProjectStatus.pending,
            num_shorts_requested=num_shorts_requested,
            burn_subtitles=burn_subtitles,
            use_broll=use_broll,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        dest = source_video_path(project.id, upload_file.filename)
        try:
            await save_upload_streamed(upload_file, dest)
        except BadRequestError:
            shutil.rmtree(project_dir(project.id), ignore_errors=True)
            db.delete(project)
            db.commit()
            raise
        project.source_video_path = str(dest)
        db.add(project)
        db.commit()
        db.refresh(project)

    background_tasks.add_task(run_import_pipeline, project.id)
    return project


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    """List the authenticated user's projects."""
    query = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(min(limit, 100)).all()
    return ProjectListResponse(items=items, total=total)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Project:
    """Get a single project owned by the authenticated user."""
    return _get_owned_project(db, project_id, current_user)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    """Delete a project (and its stored media) owned by the authenticated user."""
    project = _get_owned_project(db, project_id, current_user)
    db.delete(project)
    db.commit()
    shutil.rmtree(project_dir(project_id), ignore_errors=True)


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Project:
    """Lightweight endpoint for polling pipeline progress."""
    return _get_owned_project(db, project_id, current_user)
