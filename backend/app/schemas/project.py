"""Project schemas."""
from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.models.project import OutputLayout, ProjectStatus, SourceType


class ProjectCreateJSON(BaseModel):
    """Used only for documentation/validation of the JSON (youtube_url) request shape."""

    title: str | None = Field(default=None, max_length=255)
    youtube_url: str = Field(max_length=1000)
    num_shorts_requested: int = Field(default=3, ge=1, le=10)
    burn_subtitles: bool = True
    use_broll: bool = False
    output_layout: OutputLayout = OutputLayout.vertical_9_16


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    title: str
    source_type: SourceType
    source_url: str | None
    duration_seconds: float | None
    status: ProjectStatus
    status_message: str | None
    num_shorts_requested: int
    burn_subtitles: bool
    use_broll: bool
    output_layout: OutputLayout
    thumbnail_path: str | None = Field(exclude=True, default=None)
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def has_thumbnail(self) -> bool:
        return bool(self.thumbnail_path)


class ProjectStatusResponse(BaseModel):
    id: int
    status: ProjectStatus
    status_message: str | None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
