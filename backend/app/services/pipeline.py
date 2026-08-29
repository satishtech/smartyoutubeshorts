"""Background-task orchestration for the media pipeline.

Every function here is meant to be scheduled via FastAPI `BackgroundTasks` — never
called inline from a request handler. Each function opens its own short-lived DB
session (the request-scoped session from `get_db` is closed before background
tasks run) and advances `Project.status` as it progresses, per CLAUDE.md.
"""
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.exceptions import AppException
from app.models.highlight_segment import HighlightSegment
from app.models.project import Project, ProjectStatus, SourceType
from app.models.short import Short, ShortStatus
from app.models.transcript import Transcript
from app.services import highlight_detection, video_render, youtube_import
from app.services.ffmpeg_utils import probe_duration_seconds
from app.services.storage import project_dir, project_thumbnail_path, shorts_dir
from app.services.transcription import transcribe_video

logger = logging.getLogger(__name__)


def _set_status(db: Session, project: Project, status: ProjectStatus, message: str | None = None) -> None:
    project.status = status
    project.status_message = message
    db.add(project)
    db.commit()
    db.refresh(project)


def run_import_pipeline(project_id: int) -> None:
    """Download (if YouTube) or probe (if uploaded) the source video, then auto-run transcription."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("run_import_pipeline: project %s not found", project_id)
            return

        try:
            if project.source_type == SourceType.youtube_url:
                _set_status(db, project, ProjectStatus.downloading, "Downloading video from YouTube")
                result = youtube_import.download_youtube_video(project.source_url, project_dir(project.id))
                project.source_video_path = result["path"]
                project.duration_seconds = result["duration_seconds"]
                if not project.title:
                    project.title = result["title"]
                db.add(project)
                db.commit()
                db.refresh(project)
            else:
                # Uploaded file was already saved synchronously by the router.
                if project.source_video_path and project.duration_seconds is None:
                    project.duration_seconds = probe_duration_seconds(Path(project.source_video_path))
                    db.add(project)
                    db.commit()
                    db.refresh(project)

            _generate_project_thumbnail(db, project)
            _run_transcription(db, project)
        except AppException as exc:
            logger.error("Import pipeline failed for project %s: %s", project_id, exc.message)
            _set_status(db, project, ProjectStatus.failed, exc.message)
        except Exception as exc:  # noqa: BLE001 - final safety net for background task
            logger.exception("Unexpected error in import pipeline for project %s", project_id)
            _set_status(db, project, ProjectStatus.failed, f"Unexpected error: {exc}")
    finally:
        db.close()


def _generate_project_thumbnail(db: Session, project: Project) -> None:
    """Extract one representative frame (~10% into the video) as the project's thumbnail.

    Best-effort: a thumbnail failure must not fail the whole import pipeline.
    """
    if not project.source_video_path:
        return
    try:
        at_seconds = (project.duration_seconds or 5.0) * 0.1
        thumb_path = project_thumbnail_path(project.id)
        video_render.generate_thumbnail(Path(project.source_video_path), thumb_path, at_seconds=at_seconds)
        project.thumbnail_path = str(thumb_path)
        db.add(project)
        db.commit()
        db.refresh(project)
    except Exception:  # noqa: BLE001 - thumbnail generation is non-critical
        logger.warning("Failed to generate thumbnail for project %s", project.id, exc_info=True)


def _run_transcription(db: Session, project: Project) -> None:
    _set_status(db, project, ProjectStatus.transcribing, "Transcribing audio")
    result = transcribe_video(Path(project.source_video_path))

    transcript = db.query(Transcript).filter(Transcript.project_id == project.id).first()
    if transcript is None:
        transcript = Transcript(project_id=project.id)
    transcript.full_text = result["full_text"]
    transcript.segments = result["segments"]
    transcript.language = result.get("language")
    db.add(transcript)

    _set_status(
        db,
        project,
        ProjectStatus.ready_for_review,
        "Transcript ready. Run highlight detection when you're ready.",
    )


def run_highlight_detection_pipeline(project_id: int, num_shorts_override: int | None = None) -> None:
    """Call Claude to detect highlight segments for a project's transcript."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("run_highlight_detection_pipeline: project %s not found", project_id)
            return

        try:
            _set_status(db, project, ProjectStatus.detecting_highlights, "Detecting highlight moments")
            transcript = db.query(Transcript).filter(Transcript.project_id == project.id).first()
            if not transcript:
                raise AppException("No transcript available for highlight detection", "NO_TRANSCRIPT", 400)

            num_shorts = num_shorts_override or project.num_shorts_requested
            highlights = highlight_detection.detect_highlights(
                transcript.segments, num_shorts, project.duration_seconds
            )

            db.query(HighlightSegment).filter(HighlightSegment.project_id == project.id).delete()
            for idx, h in enumerate(highlights):
                db.add(
                    HighlightSegment(
                        project_id=project.id,
                        order=idx,
                        start_time=h["start_time"],
                        end_time=h["end_time"],
                        title=h["title"],
                        reason=h.get("reason"),
                        score=h.get("score"),
                    )
                )
            db.commit()

            _set_status(
                db,
                project,
                ProjectStatus.ready_for_review,
                f"{len(highlights)} highlight(s) ready. Adjust the timeline and generate shorts.",
            )
        except AppException as exc:
            logger.error("Highlight detection failed for project %s: %s", project_id, exc.message)
            _set_status(db, project, ProjectStatus.failed, exc.message)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error detecting highlights for project %s", project_id)
            _set_status(db, project, ProjectStatus.failed, f"Unexpected error: {exc}")
    finally:
        db.close()


def run_shorts_generation_pipeline(project_id: int, highlight_ids: list[int] | None = None) -> None:
    """Render a Short (ffmpeg) for each requested highlight segment."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("run_shorts_generation_pipeline: project %s not found", project_id)
            return

        try:
            _set_status(db, project, ProjectStatus.generating_shorts, "Rendering shorts")

            transcript = db.query(Transcript).filter(Transcript.project_id == project.id).first()
            segments = transcript.segments if transcript else []

            query = db.query(HighlightSegment).filter(HighlightSegment.project_id == project.id)
            if highlight_ids:
                query = query.filter(HighlightSegment.id.in_(highlight_ids))
            highlights = query.order_by(HighlightSegment.order).all()

            any_failed = False
            for highlight in highlights:
                short = db.query(Short).filter(Short.highlight_segment_id == highlight.id).first()
                if short is None:
                    short = Short(project_id=project.id, highlight_segment_id=highlight.id)
                short.status = ShortStatus.rendering
                db.add(short)
                db.commit()
                db.refresh(short)

                try:
                    dest = shorts_dir(project.id) / f"short_{highlight.id}.mp4"
                    thumb = shorts_dir(project.id) / f"short_{highlight.id}.jpg"
                    video_render.render_short(
                        source_video_path=Path(project.source_video_path),
                        start_time=highlight.start_time,
                        end_time=highlight.end_time,
                        dest_path=dest,
                        transcript_segments=segments,
                        burn_subtitles=project.burn_subtitles,
                        output_layout=project.output_layout,
                    )
                    video_render.generate_thumbnail(dest, thumb)

                    short.file_path = str(dest)
                    short.thumbnail_path = str(thumb)
                    short.duration_seconds = min(highlight.end_time - highlight.start_time, 60.0)
                    short.has_subtitles = project.burn_subtitles
                    short.has_broll = False
                    short.status = ShortStatus.ready
                    db.add(short)
                    db.commit()
                except Exception:  # noqa: BLE001
                    logger.exception("Failed to render short for highlight %s", highlight.id)
                    short.status = ShortStatus.failed
                    db.add(short)
                    db.commit()
                    any_failed = True

            if any_failed:
                _set_status(db, project, ProjectStatus.failed, "One or more shorts failed to render")
            else:
                _set_status(db, project, ProjectStatus.completed, "All shorts generated successfully")
        except AppException as exc:
            logger.error("Shorts generation failed for project %s: %s", project_id, exc.message)
            _set_status(db, project, ProjectStatus.failed, exc.message)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error generating shorts for project %s", project_id)
            _set_status(db, project, ProjectStatus.failed, f"Unexpected error: {exc}")
    finally:
        db.close()
