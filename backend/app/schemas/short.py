"""Short schemas."""
from datetime import datetime

from pydantic import BaseModel

from app.models.short import ShortStatus


class ShortGenerateRequest(BaseModel):
    highlight_segment_ids: list[int] | None = None  # None = generate all highlights for the project


class ShortResponse(BaseModel):
    id: int
    project_id: int
    highlight_segment_id: int
    duration_seconds: float | None
    has_subtitles: bool
    has_broll: bool
    status: ShortStatus
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
