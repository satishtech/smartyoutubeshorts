"""Highlight detection service — calls Anthropic Claude to pick highlight moments."""
import json
import logging
import re
from typing import Any

from app.config import settings
from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert short-form video editor. Given a timestamped transcript, "
    "identify the most engaging, self-contained moments suitable for vertical "
    "short-form clips (like YouTube Shorts/TikTok). Respond with ONLY a JSON array, "
    "no prose, no markdown fences. Each element must be an object with keys: "
    '"start_time" (float seconds), "end_time" (float seconds), "title" (short catchy string), '
    '"reason" (one sentence on why it is engaging), "score" (float 0-1, higher is better). '
    "Rules: end_time - start_time must be <= 60 seconds and > 3 seconds. "
    "Segments must not overlap. Use only timestamps present in the transcript. "
    "Return at most the requested number of segments, fewer is fine if the source lacks content."
)


def _extract_json_array(raw_text: str) -> list[dict[str, Any]]:
    text = raw_text.strip()
    # Strip markdown code fences if the model added them despite instructions.
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    json_str = match.group(0) if match else text
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse highlight detection JSON: %s\nraw=%s", exc, raw_text[:1000])
        raise ExternalServiceError("Highlight detection returned invalid JSON") from exc
    if not isinstance(data, list):
        raise ExternalServiceError("Highlight detection did not return a JSON array")
    return data


def detect_highlights(
    segments: list[dict[str, Any]],
    num_shorts_requested: int,
    video_duration: float | None = None,
) -> list[dict[str, Any]]:
    """Ask Claude to pick up to num_shorts_requested highlight segments (each <= 60s).

    Returns a list of dicts with start_time/end_time/title/reason/score, capped at
    num_shorts_requested and clamped to a valid, non-overlapping, <=60s duration.
    Synchronous/blocking — must only be called from a background task.
    """
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ExternalServiceError("anthropic package is not installed") from exc

    if not settings.ANTHROPIC_API_KEY:
        raise ExternalServiceError("ANTHROPIC_API_KEY is not configured")

    transcript_text = "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments)
    user_prompt = (
        f"Requested number of shorts: {num_shorts_requested}\n"
        f"Video duration: {video_duration if video_duration is not None else 'unknown'} seconds\n\n"
        f"Transcript:\n{transcript_text}"
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        logger.error("Anthropic highlight detection call failed: %s", exc)
        raise ExternalServiceError(f"Highlight detection failed: {exc}") from exc

    raw_text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    raw_highlights = _extract_json_array(raw_text)

    highlights: list[dict[str, Any]] = []
    for item in raw_highlights:
        try:
            start = float(item["start_time"])
            end = float(item["end_time"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        if end - start > 60:
            end = start + 60
        if video_duration is not None:
            start = max(0.0, min(start, video_duration))
            end = max(0.0, min(end, video_duration))
        if end - start < 1:
            continue
        highlights.append(
            {
                "start_time": round(start, 2),
                "end_time": round(end, 2),
                "title": str(item.get("title", "Highlight"))[:255],
                "reason": str(item.get("reason", ""))[:1000],
                "score": float(item.get("score", 0.5)) if item.get("score") is not None else None,
            }
        )

    highlights.sort(key=lambda h: h.get("score") or 0, reverse=True)
    return highlights[:num_shorts_requested]
