"""Project model — represents one video import + shorts generation job."""
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.highlight_segment import HighlightSegment
    from app.models.short import Short
    from app.models.transcript import Transcript
    from app.models.user import User


class SourceType(str, enum.Enum):
    upload = "upload"
    youtube_url = "youtube_url"


class ProjectStatus(str, enum.Enum):
    pending = "pending"
    downloading = "downloading"
    transcribing = "transcribing"
    detecting_highlights = "detecting_highlights"
    ready_for_review = "ready_for_review"
    generating_shorts = "generating_shorts"
    completed = "completed"
    failed = "failed"


class OutputLayout(str, enum.Enum):
    vertical_9_16 = "vertical_9_16"
    square_1_1 = "square_1_1"
    portrait_4_5 = "portrait_4_5"
    landscape_16_9 = "landscape_16_9"
    classic_4_3 = "classic_4_3"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_video_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.pending, nullable=False, index=True
    )
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    num_shorts_requested: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    burn_subtitles: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_broll: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    output_layout: Mapped[OutputLayout] = mapped_column(
        Enum(OutputLayout), default=OutputLayout.vertical_9_16, server_default="vertical_9_16", nullable=False
    )
    thumbnail_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="projects")
    transcript: Mapped["Transcript | None"] = relationship(
        "Transcript", back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    highlight_segments: Mapped[list["HighlightSegment"]] = relationship(
        "HighlightSegment", back_populates="project", cascade="all, delete-orphan", order_by="HighlightSegment.order"
    )
    shorts: Mapped[list["Short"]] = relationship(
        "Short", back_populates="project", cascade="all, delete-orphan"
    )
