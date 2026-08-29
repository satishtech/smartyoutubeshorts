"""Wraps yt-dlp for downloading a YouTube video and probing its metadata."""
import logging
import re
from pathlib import Path
from typing import Any

from app.exceptions import BadRequestError, ExternalServiceError

logger = logging.getLogger(__name__)

_YOUTUBE_URL_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com/(watch\?v=|shorts/|live/)|youtu\.be/)[\w-]{6,}",
    re.IGNORECASE,
)


def is_valid_youtube_url(url: str) -> bool:
    """Validate that a URL looks like a genuine YouTube video URL."""
    if not url or len(url) > 1000:
        return False
    return bool(_YOUTUBE_URL_RE.match(url.strip()))


def validate_youtube_url(url: str) -> None:
    if not is_valid_youtube_url(url):
        raise BadRequestError("Invalid YouTube URL")


def download_youtube_video(url: str, dest_dir: Path) -> dict[str, Any]:
    """Download a YouTube video with yt-dlp into dest_dir.

    Returns {"path": str, "duration_seconds": float, "title": str}.
    Raises ExternalServiceError on failure. This function is synchronous/blocking
    and must only ever be called from a background task, never inline in a request handler.
    """
    validate_youtube_url(url)

    try:
        import yt_dlp  # imported lazily so unit tests can run without the dependency installed
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ExternalServiceError("yt-dlp is not installed") from exc

    dest_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(dest_dir / "source.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": 500 * 1024 * 1024,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            # merge_output_format may change extension after postprocessing
            mp4_path = Path(filepath).with_suffix(".mp4")
            final_path = mp4_path if mp4_path.exists() else Path(filepath)
            return {
                "path": str(final_path),
                "duration_seconds": float(info.get("duration") or 0),
                "title": info.get("title") or "Untitled",
            }
    except Exception as exc:  # yt_dlp raises its own DownloadError subclasses
        logger.error("yt-dlp download failed for %s: %s", url, exc)
        raise ExternalServiceError(f"Failed to download YouTube video: {exc}") from exc
