"""Transcript routes."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.transcript import TranscriptResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["transcripts"])


@router.get("/{project_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Transcript:
    """Get the transcript for a project (auto-generated after import)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError("Project")
    if project.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this project")

    transcript = db.query(Transcript).filter(Transcript.project_id == project_id).first()
    if not transcript:
        raise NotFoundError("Transcript")
    return transcript
