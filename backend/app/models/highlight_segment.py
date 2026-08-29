"""HighlightSegment model — AI-detected candidate moments for a Short."""
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.short import Short


class HighlightSegment(Base, TimestampMixin):
    __tablename__ = "highlight_segments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="highlight_segments")
    short: Mapped["Short | None"] = relationship(
        "Short", back_populates="highlight_segment", uselist=False
    )
