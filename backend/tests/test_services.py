"""Service-layer unit tests. All external calls (yt-dlp, ffmpeg, OpenAI, Anthropic, Pixabay/Pexels) are mocked."""
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import BadRequestError, ExternalServiceError
from app.services import broll, highlight_detection, video_render, youtube_import
from app.services.ffmpeg_utils import run_ffmpeg

# --- youtube_import -----------------------------------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True),
        ("https://youtu.be/dQw4w9WgXcQ", True),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", True),
        ("https://example.com/watch?v=dQw4w9WgXcQ", False),
        ("not a url at all", False),
        ("", False),
    ],
)
def test_is_valid_youtube_url(url, expected):
    assert youtube_import.is_valid_youtube_url(url) is expected


def test_validate_youtube_url_raises_on_bad_url():
    with pytest.raises(BadRequestError):
        youtube_import.validate_youtube_url("https://example.com/video")


def test_download_youtube_video_uses_yt_dlp(tmp_path):
    fake_ydl_instance = MagicMock()
    fake_ydl_instance.extract_info.return_value = {"duration": 42.5, "title": "Fake Title"}
    fake_ydl_instance.prepare_filename.return_value = str(tmp_path / "source.mp4")
    (tmp_path / "source.mp4").write_bytes(b"fake")

    fake_yt_dlp_module = SimpleNamespace(
        YoutubeDL=MagicMock(return_value=MagicMock(__enter__=lambda s: fake_ydl_instance, __exit__=lambda *a: None))
    )

    with patch.dict("sys.modules", {"yt_dlp": fake_yt_dlp_module}):
        result = youtube_import.download_youtube_video("https://youtu.be/dQw4w9WgXcQ", tmp_path)

    assert result["duration_seconds"] == 42.5
    assert result["title"] == "Fake Title"


def test_download_youtube_video_wraps_failures(tmp_path):
    fake_ydl_instance = MagicMock()
    fake_ydl_instance.extract_info.side_effect = RuntimeError("network boom")
    fake_yt_dlp_module = SimpleNamespace(
        YoutubeDL=MagicMock(return_value=MagicMock(__enter__=lambda s: fake_ydl_instance, __exit__=lambda *a: None))
    )

    with patch.dict("sys.modules", {"yt_dlp": fake_yt_dlp_module}):
        with pytest.raises(ExternalServiceError):
            youtube_import.download_youtube_video("https://youtu.be/dQw4w9WgXcQ", tmp_path)


# --- highlight_detection --------------------------------------------------------------


def _fake_anthropic_response(text: str):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def test_detect_highlights_parses_and_caps_results(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "fake-key")

    raw_json = (
        '[{"start_time": 0, "end_time": 30, "title": "A", "reason": "r1", "score": 0.9},'
        '{"start_time": 40, "end_time": 200, "title": "B", "reason": "r2", "score": 0.8},'
        '{"start_time": 250, "end_time": 260, "title": "C", "reason": "r3", "score": 0.5}]'
    )
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_anthropic_response(raw_json)
    fake_anthropic_module = SimpleNamespace(Anthropic=MagicMock(return_value=fake_client))

    segments = [{"start": 0, "end": 5, "text": "hi"}]
    with patch.dict("sys.modules", {"anthropic": fake_anthropic_module}):
        highlights = highlight_detection.detect_highlights(segments, num_shorts_requested=2, video_duration=300)

    assert len(highlights) == 2  # capped at num_shorts_requested
    assert all(h["end_time"] - h["start_time"] <= 60 for h in highlights)  # clamped to <=60s
    # highest score first
    assert highlights[0]["title"] == "A"


def test_detect_highlights_strips_markdown_fences(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "fake-key")

    raw_json = '```json\n[{"start_time": 0, "end_time": 10, "title": "A", "score": 0.5}]\n```'
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_anthropic_response(raw_json)
    fake_anthropic_module = SimpleNamespace(Anthropic=MagicMock(return_value=fake_client))

    with patch.dict("sys.modules", {"anthropic": fake_anthropic_module}):
        highlights = highlight_detection.detect_highlights([], num_shorts_requested=5, video_duration=100)

    assert len(highlights) == 1


def test_detect_highlights_requires_api_key(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    with pytest.raises(ExternalServiceError):
        highlight_detection.detect_highlights([], num_shorts_requested=3, video_duration=100)


def test_detect_highlights_invalid_json_raises(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "fake-key")
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_anthropic_response("not json at all")
    fake_anthropic_module = SimpleNamespace(Anthropic=MagicMock(return_value=fake_client))

    with patch.dict("sys.modules", {"anthropic": fake_anthropic_module}):
        with pytest.raises(ExternalServiceError):
            highlight_detection.detect_highlights([], num_shorts_requested=3, video_duration=100)


# --- video_render (SRT building — pure logic, no ffmpeg invocation) ------------------


def test_build_srt_rebases_timestamps_to_clip_start():
    segments = [
        {"start": 0.0, "end": 2.0, "text": "before clip"},
        {"start": 10.0, "end": 12.0, "text": "inside clip"},
        {"start": 30.0, "end": 32.0, "text": "after clip"},
    ]
    srt = video_render.build_srt(segments, clip_start=9.0, clip_end=15.0)
    assert "inside clip" in srt
    assert "before clip" not in srt
    assert "after clip" not in srt
    assert "00:00:01,000" in srt  # 10.0 - 9.0 = 1.0s relative start


def test_build_srt_skips_empty_text():
    segments = [{"start": 0.0, "end": 1.0, "text": "   "}]
    srt = video_render.build_srt(segments, clip_start=0.0, clip_end=5.0)
    assert srt == ""


def test_render_short_invokes_ffmpeg(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.services.video_render.run_ffmpeg", lambda args, timeout=900: calls.append(args)
    )
    source = tmp_path / "source.mp4"
    source.write_bytes(b"fake")
    dest = tmp_path / "out" / "short.mp4"

    video_render.render_short(source, start_time=5.0, end_time=15.0, dest_path=dest, burn_subtitles=False)

    assert len(calls) == 1
    assert str(source) in calls[0]
    assert str(dest) in calls[0]


# --- ffmpeg_utils ---------------------------------------------------------------------


def test_run_ffmpeg_wraps_called_process_error(monkeypatch):
    def _raise(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "ffmpeg", stderr="boom")

    monkeypatch.setattr("app.services.ffmpeg_utils.subprocess.run", _raise)
    with pytest.raises(ExternalServiceError):
        run_ffmpeg(["-i", "in.mp4", "out.mp4"])


# --- broll ------------------------------------------------------------------------------


def test_search_broll_pixabay_returns_empty_without_api_key(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "PIXABAY_API_KEY", "")
    assert broll.search_broll_pixabay("nature") == []


def test_search_broll_pixabay_parses_results(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "PIXABAY_API_KEY", "fake-key")

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "hits": [{"videos": {"medium": {"url": "https://pixabay.example/video.mp4"}}}]
    }
    with patch("app.services.broll.httpx.get", return_value=fake_response):
        results = broll.search_broll_pixabay("nature")

    assert results == [{"url": "https://pixabay.example/video.mp4", "source": "pixabay"}]


def test_search_broll_falls_back_to_pexels(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "PIXABAY_API_KEY", "")
    monkeypatch.setattr(settings, "PEXELS_API_KEY", "fake-key")

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "videos": [{"video_files": [{"width": 480, "link": "https://pexels.example/video.mp4"}]}]
    }
    with patch("app.services.broll.httpx.get", return_value=fake_response):
        results = broll.search_broll("nature")

    assert results == [{"url": "https://pexels.example/video.mp4", "source": "pexels"}]


# --- transcription ---------------------------------------------------------------------


def test_transcribe_video_requires_api_key(monkeypatch, tmp_path):
    from app.config import settings
    from app.services import transcription

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    with pytest.raises(ExternalServiceError):
        transcription.transcribe_video(video)


def test_transcribe_video_parses_segments(monkeypatch, tmp_path):
    from app.config import settings
    from app.services import transcription

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "fake-key")

    def _fake_extract_audio(video_path, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"fake audio bytes")
        return dest_path

    monkeypatch.setattr(transcription, "extract_audio", _fake_extract_audio)

    fake_transcript = SimpleNamespace(
        text="hello world",
        language="en",
        segments=[{"start": 0.0, "end": 1.5, "text": "hello world"}],
    )
    fake_client = MagicMock()
    fake_client.audio.transcriptions.create.return_value = fake_transcript
    fake_openai_module = SimpleNamespace(OpenAI=MagicMock(return_value=fake_client))

    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")

    with patch.dict("sys.modules", {"openai": fake_openai_module}):
        result = transcription.transcribe_video(video)

    assert result["full_text"] == "hello world"
    assert result["language"] == "en"
    assert result["segments"][0]["text"] == "hello world"
