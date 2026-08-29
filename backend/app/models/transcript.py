"""Transcript model — full text + timestamped segments produced by Whisper."""
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # List[{"start": float, "end": float, "text": str}]
    segments: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="transcript")
