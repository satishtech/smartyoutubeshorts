"""Transcription service — extracts audio then calls OpenAI Whisper API."""
import logging
import tempfile
from pathlib import Path
from typing import Any

from app.config import settings
from app.exceptions import ExternalServiceError
from app.services.ffmpeg_utils import extract_audio

logger = logging.getLogger(__name__)


def transcribe_video(video_path: Path) -> dict[str, Any]:
    """Transcribe a video file's audio track with OpenAI Whisper.

    Returns {"full_text": str, "segments": [{"start", "end", "text"}], "language": str | None}.
    Synchronous/blocking — must only be called from a background task.
    """
    try:
        from openai import OpenAI  # imported lazily so tests can run without network/keys
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ExternalServiceError("openai package is not installed") from exc

    if not settings.OPENAI_API_KEY:
        raise ExternalServiceError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    with tempfile.TemporaryDirectory() as tmp_dir:
        audio_path = extract_audio(video_path, Path(tmp_dir) / "audio.mp3")
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
        except Exception as exc:
            logger.error("OpenAI Whisper transcription failed: %s", exc)
            raise ExternalServiceError(f"Transcription failed: {exc}") from exc

    segments = [
        {
            "start": float(seg.get("start", 0.0) if isinstance(seg, dict) else seg.start),
            "end": float(seg.get("end", 0.0) if isinstance(seg, dict) else seg.end),
            "text": (seg.get("text", "") if isinstance(seg, dict) else seg.text).strip(),
        }
        for seg in (getattr(transcript, "segments", None) or [])
    ]
    full_text = getattr(transcript, "text", None) or " ".join(s["text"] for s in segments)
    language = getattr(transcript, "language", None)

    return {"full_text": full_text, "segments": segments, "language": language}
