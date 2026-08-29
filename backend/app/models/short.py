"""Short model — a rendered 9:16 vertical clip."""
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.highlight_segment import HighlightSegment
    from app.models.project import Project


class ShortStatus(str, enum.Enum):
    pending = "pending"
    rendering = "rendering"
    ready = "ready"
    failed = "failed"


class Short(Base, TimestampMixin):
    __tablename__ = "shorts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    highlight_segment_id: Mapped[int] = mapped_column(
        ForeignKey("highlight_segments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_broll: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ShortStatus] = mapped_column(Enum(ShortStatus), default=ShortStatus.pending, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="shorts")
    highlight_segment: Mapped["HighlightSegment"] = relationship("HighlightSegment", back_populates="short")
