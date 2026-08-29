"""HighlightSegment routes: detect (Claude), list, update (timeline drag-adjust), delete."""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.highlight_segment import HighlightSegment
from app.models.project import Project, ProjectStatus
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.highlight import HighlightDetectRequest, HighlightResponse, HighlightUpdateRequest
from app.services.pipeline import run_highlight_detection_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["highlights"])


def _get_owned_project(db: Session, project_id: int, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError("Project")
    if project.user_id != user.id:
        raise ForbiddenError("You do not have access to this project")
    return project


@router.post("/{project_id}/highlights/detect", status_code=202, response_model=dict)
async def detect_highlights(
    project_id: int,
    payload: HighlightDetectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Kick off (async, via BackgroundTasks) Claude-based highlight detection."""
    project = _get_owned_project(db, project_id, current_user)

    transcript = db.query(Transcript).filter(Transcript.project_id == project_id).first()
    if not transcript:
        raise BadRequestError("Project has no transcript yet; wait for transcription to complete")

    project.status = ProjectStatus.detecting_highlights
    project.status_message = "Highlight detection queued"
    db.add(project)
    db.commit()

    background_tasks.add_task(run_highlight_detection_pipeline, project_id, payload.num_shorts)
    return {"detail": "Highlight detection started", "project_id": project_id}


@router.get("/{project_id}/highlights", response_model=list[HighlightResponse])
async def list_highlights(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[HighlightSegment]:
    """List highlight segments for a project, ordered by their `order` field."""
    _get_owned_project(db, project_id, current_user)
    return (
        db.query(HighlightSegment)
        .filter(HighlightSegment.project_id == project_id)
        .order_by(HighlightSegment.order)
        .all()
    )


def _get_owned_highlight(db: Session, project_id: int, hid: int, user: User) -> HighlightSegment:
    _get_owned_project(db, project_id, user)
    highlight = (
        db.query(HighlightSegment)
        .filter(HighlightSegment.id == hid, HighlightSegment.project_id == project_id)
        .first()
    )
    if not highlight:
        raise NotFoundError("HighlightSegment")
    return highlight


@router.put("/{project_id}/highlights/{hid}", response_model=HighlightResponse)
async def update_highlight(
    project_id: int,
    hid: int,
    payload: HighlightUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HighlightSegment:
    """Persist a timeline drag-adjustment (start/end/title/order) for one highlight segment."""
    highlight = _get_owned_highlight(db, project_id, hid, current_user)

    if payload.start_time is not None:
        highlight.start_time = payload.start_time
    if payload.end_time is not None:
        highlight.end_time = payload.end_time
    if payload.title is not None:
        highlight.title = payload.title
    if payload.order is not None:
        highlight.order = payload.order

    if highlight.end_time <= highlight.start_time:
        raise BadRequestError("end_time must be greater than start_time")
    if highlight.end_time - highlight.start_time > 60:
        raise BadRequestError("Highlight segment must be <= 60 seconds")

    db.add(highlight)
    db.commit()
    db.refresh(highlight)
    return highlight


@router.delete("/{project_id}/highlights/{hid}", status_code=204)
async def delete_highlight(
    project_id: int, hid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    """Delete a highlight segment (and cascades to its Short, if any)."""
    highlight = _get_owned_highlight(db, project_id, hid, current_user)
    db.delete(highlight)
    db.commit()
