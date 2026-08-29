"""Background pipeline orchestration tests. All external services are mocked;
`SessionLocal` is patched to the same in-memory SQLite engine the `db` fixture uses
so pipeline functions (which open their own sessions) see the same test data.
"""
from pathlib import Path

import pytest

from app.models.highlight_segment import HighlightSegment
from app.models.project import Project, ProjectStatus, SourceType
from app.models.short import Short, ShortStatus
from app.models.transcript import Transcript
from app.services import pipeline
from tests.conftest import TestSessionLocal


@pytest.fixture(autouse=True)
def _patch_session_local(monkeypatch, db):
    """Point pipeline.SessionLocal at the same in-memory engine as the `db` fixture."""
    monkeypatch.setattr(pipeline, "SessionLocal", TestSessionLocal)


def test_run_import_pipeline_youtube_success(db, test_user, monkeypatch, tmp_path):
    project = Project(
        user_id=test_user.id,
        title="",
        source_type=SourceType.youtube_url,
        source_url="https://youtu.be/dQw4w9WgXcQ",
        status=ProjectStatus.pending,
        num_shorts_requested=3,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    video_path = tmp_path / "source.mp4"
    video_path.write_bytes(b"fake")

    monkeypatch.setattr(
        pipeline.youtube_import,
        "download_youtube_video",
        lambda url, dest_dir: {"path": str(video_path), "duration_seconds": 55.0, "title": "Downloaded Title"},
    )
    monkeypatch.setattr(
        pipeline,
        "transcribe_video",
        lambda path: {"full_text": "hi there", "segments": [{"start": 0, "end": 1, "text": "hi there"}], "language": "en"},
    )

    pipeline.run_import_pipeline(project.id)

    db.refresh(project)
    assert project.status == ProjectStatus.ready_for_review
    assert project.duration_seconds == 55.0
    assert project.title == "Downloaded Title"
    transcript = db.query(Transcript).filter(Transcript.project_id == project.id).first()
    assert transcript is not None
    assert transcript.full_text == "hi there"


def test_run_import_pipeline_youtube_download_failure_marks_failed(db, test_user, monkeypatch):
    project = Project(
        user_id=test_user.id,
        title="X",
        source_type=SourceType.youtube_url,
        source_url="https://youtu.be/dQw4w9WgXcQ",
        status=ProjectStatus.pending,
        num_shorts_requested=3,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    from app.exceptions import ExternalServiceError

    def _boom(url, dest_dir):
        raise ExternalServiceError("yt-dlp exploded")

    monkeypatch.setattr(pipeline.youtube_import, "download_youtube_video", _boom)

    pipeline.run_import_pipeline(project.id)

    db.refresh(project)
    assert project.status == ProjectStatus.failed
    assert "yt-dlp exploded" in project.status_message


def test_run_import_pipeline_upload_probes_duration(db, test_user, monkeypatch, tmp_path):
    video_path = tmp_path / "source.mp4"
    video_path.write_bytes(b"fake")

    project = Project(
        user_id=test_user.id,
        title="Uploaded",
        source_type=SourceType.upload,
        source_video_path=str(video_path),
        status=ProjectStatus.pending,
        num_shorts_requested=3,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    monkeypatch.setattr(pipeline, "probe_duration_seconds", lambda path: 30.0)
    monkeypatch.setattr(
        pipeline,
        "transcribe_video",
        lambda path: {"full_text": "hello", "segments": [], "language": "en"},
    )

    pipeline.run_import_pipeline(project.id)

    db.refresh(project)
    assert project.duration_seconds == 30.0
    assert project.status == ProjectStatus.ready_for_review


def test_run_highlight_detection_pipeline_success(db, project, transcript, monkeypatch):
    monkeypatch.setattr(
        pipeline.highlight_detection,
        "detect_highlights",
        lambda segments, num_shorts, duration: [
            {"start_time": 0.0, "end_time": 10.0, "title": "A", "reason": "r", "score": 0.9}
        ],
    )

    pipeline.run_highlight_detection_pipeline(project.id, num_shorts_override=1)

    db.refresh(project)
    assert project.status == ProjectStatus.ready_for_review
    highlights = db.query(HighlightSegment).filter(HighlightSegment.project_id == project.id).all()
    assert len(highlights) == 1
    assert highlights[0].title == "A"


def test_run_highlight_detection_pipeline_no_transcript_fails(db, project):
    pipeline.run_highlight_detection_pipeline(project.id)
    db.refresh(project)
    assert project.status == ProjectStatus.failed


def test_run_shorts_generation_pipeline_success(db, project, highlight, transcript, monkeypatch, tmp_path):
    def _fake_render_short(source_video_path, start_time, end_time, dest_path, **kwargs):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"fake rendered video")
        return dest_path

    def _fake_thumbnail(video_path, dest_path, **kwargs):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"fake jpg")
        return dest_path

    monkeypatch.setattr(pipeline.video_render, "render_short", _fake_render_short)
    monkeypatch.setattr(pipeline.video_render, "generate_thumbnail", _fake_thumbnail)

    pipeline.run_shorts_generation_pipeline(project.id)

    db.refresh(project)
    assert project.status == ProjectStatus.completed
    short = db.query(Short).filter(Short.highlight_segment_id == highlight.id).first()
    assert short is not None
    assert short.status == ShortStatus.ready
    assert short.file_path and Path(short.file_path).exists()


def test_run_shorts_generation_pipeline_render_failure_marks_failed(db, project, highlight, transcript, monkeypatch):
    from app.exceptions import ExternalServiceError

    def _boom(*args, **kwargs):
        raise ExternalServiceError("ffmpeg exploded")

    monkeypatch.setattr(pipeline.video_render, "render_short", _boom)

    pipeline.run_shorts_generation_pipeline(project.id)

    db.refresh(project)
    assert project.status == ProjectStatus.failed
    short = db.query(Short).filter(Short.highlight_segment_id == highlight.id).first()
    assert short.status == ShortStatus.failed


def test_run_import_pipeline_missing_project_is_noop(db):
    # Should not raise even though project 999999 doesn't exist.
    pipeline.run_import_pipeline(999999)
