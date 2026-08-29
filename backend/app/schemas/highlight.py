"""HighlightSegment schemas."""
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class HighlightDetectRequest(BaseModel):
    num_shorts: int | None = Field(default=None, ge=1, le=10)


class HighlightResponse(BaseModel):
    id: int
    project_id: int
    order: int
    start_time: float
    end_time: float
    title: str
    reason: str | None
    score: float | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class HighlightUpdateRequest(BaseModel):
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, ge=0)
    title: str | None = Field(default=None, max_length=255)
    order: int | None = None

    @model_validator(mode="after")
    def check_range(self) -> "HighlightUpdateRequest":
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be greater than start_time")
            if self.end_time - self.start_time > 60:
                raise ValueError("Highlight segment must be <= 60 seconds")
        return self
