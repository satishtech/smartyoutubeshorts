"""Low-level ffmpeg/ffprobe subprocess helpers shared by transcription and video_render."""
import json
import logging
import subprocess
from pathlib import Path

from app.config import settings
from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


def probe_duration_seconds(video_path: Path) -> float:
    """Return media duration in seconds via ffprobe."""
    cmd = [
        settings.FFPROBE_BIN,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (subprocess.SubprocessError, KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.error("ffprobe failed for %s: %s", video_path, exc)
        raise ExternalServiceError(f"Failed to probe video duration: {exc}") from exc


def extract_audio(video_path: Path, dest_path: Path) -> Path:
    """Extract a compressed mono audio track (mp3) from a video for transcription."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        settings.FFMPEG_BIN,
        "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-b:a", "64k",
        str(dest_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=600)
        return dest_path
    except subprocess.SubprocessError as exc:
        logger.error("ffmpeg audio extraction failed for %s: %s", video_path, exc)
        raise ExternalServiceError(f"Failed to extract audio: {exc}") from exc


def run_ffmpeg(args: list[str], timeout: int = 900) -> None:
    """Run an ffmpeg command with the configured binary, raising ExternalServiceError on failure."""
    cmd = [settings.FFMPEG_BIN, "-y", *args]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
    except subprocess.CalledProcessError as exc:
        logger.error("ffmpeg command failed: %s\nstderr: %s", cmd, exc.stderr)
        raise ExternalServiceError(f"ffmpeg command failed: {exc.stderr[:500]}") from exc
    except subprocess.SubprocessError as exc:
        logger.error("ffmpeg command failed: %s", exc)
        raise ExternalServiceError(f"ffmpeg command failed: {exc}") from exc
