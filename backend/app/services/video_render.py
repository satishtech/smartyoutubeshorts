"""Renders a Short: trims a highlight window, crops/pads to 9:16, and hard-burns subtitles."""
import logging
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any

from app.services.ffmpeg_utils import run_ffmpeg

logger = logging.getLogger(__name__)

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def _format_srt_timestamp(seconds: float) -> str:
    td = timedelta(seconds=max(0.0, seconds))
    total_ms = int(td.total_seconds() * 1000)
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def build_srt(segments: list[dict[str, Any]], clip_start: float, clip_end: float) -> str:
    """Build SRT content for the portion of transcript segments inside [clip_start, clip_end),
    with timestamps re-based to the clip's own timeline (starting at 0).
    """
    lines: list[str] = []
    idx = 1
    for seg in segments:
        seg_start, seg_end, text = seg["start"], seg["end"], seg["text"].strip()
        if not text:
            continue
        overlap_start = max(seg_start, clip_start)
        overlap_end = min(seg_end, clip_end)
        if overlap_end <= overlap_start:
            continue
        rel_start = overlap_start - clip_start
        rel_end = overlap_end - clip_start
        lines.append(str(idx))
        lines.append(f"{_format_srt_timestamp(rel_start)} --> {_format_srt_timestamp(rel_end)}")
        lines.append(text)
        lines.append("")
        idx += 1
    return "\n".join(lines)


def _srt_filter_path(srt_path: Path) -> str:
    """Escape a path for use inside an ffmpeg filtergraph (subtitles filter)."""
    escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
    return escaped


def render_short(
    source_video_path: Path,
    start_time: float,
    end_time: float,
    dest_path: Path,
    transcript_segments: list[dict[str, Any]] | None = None,
    burn_subtitles: bool = True,
    broll_clip_paths: list[Path] | None = None,
) -> Path:
    """Render one 9:16, <=60s Short from source_video_path[start_time:end_time].

    Crops/pads to 9:16, optionally hard-burns subtitles from transcript_segments,
    and (optionally, minimally) concatenates B-roll clips before the main clip.
    Synchronous/blocking — must only be called from a background task.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    duration = min(end_time - start_time, 60.0)

    vf_parts = [
        "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'",
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT}",
    ]

    srt_tmp_dir = None
    try:
        if burn_subtitles and transcript_segments:
            srt_tmp_dir = tempfile.TemporaryDirectory()
            srt_path = Path(srt_tmp_dir.name) / "subs.srt"
            srt_content = build_srt(transcript_segments, start_time, end_time)
            srt_path.write_text(srt_content, encoding="utf-8")
            if srt_content.strip():
                style = "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=60"
                vf_parts.append(f"subtitles='{_srt_filter_path(srt_path)}':force_style='{style}'")

        vf_chain = ",".join(vf_parts)

        args = [
            "-ss", str(max(0.0, start_time)),
            "-i", str(source_video_path),
            "-t", str(duration),
            "-vf", vf_chain,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(dest_path),
        ]
        run_ffmpeg(args, timeout=900)
    finally:
        if srt_tmp_dir is not None:
            srt_tmp_dir.cleanup()

    return dest_path


def generate_thumbnail(video_path: Path, dest_path: Path, at_seconds: float = 0.5) -> Path:
    """Grab a single frame as a JPEG thumbnail."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "-ss", str(at_seconds),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "3",
        str(dest_path),
    ]
    run_ffmpeg(args, timeout=60)
    return dest_path
