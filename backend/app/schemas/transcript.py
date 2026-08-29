"""Transcript schemas."""
from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptResponse(BaseModel):
    id: int
    project_id: int
    full_text: str
    segments: list[TranscriptSegment]
    language: str | None

    model_config = {"from_attributes": True}
