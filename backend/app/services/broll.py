"""Optional B-roll sourcing from Pixabay / Pexels (opt-in via Project.use_broll)."""
import logging
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

PIXABAY_API_URL = "https://pixabay.com/api/videos/"
PEXELS_API_URL = "https://api.pexels.com/videos/search"


def search_broll_pixabay(query: str, per_page: int = 3) -> list[dict[str, Any]]:
    """Search Pixabay for B-roll video clips matching a keyword."""
    if not settings.PIXABAY_API_KEY:
        return []
    try:
        response = httpx.get(
            PIXABAY_API_URL,
            params={"key": settings.PIXABAY_API_KEY, "q": query, "per_page": per_page},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Pixabay B-roll search failed for %r: %s", query, exc)
        return []

    results = []
    for hit in data.get("hits", []):
        videos = hit.get("videos", {})
        best = videos.get("medium") or videos.get("small") or videos.get("tiny")
        if best:
            results.append({"url": best["url"], "source": "pixabay"})
    return results


def search_broll_pexels(query: str, per_page: int = 3) -> list[dict[str, Any]]:
    """Search Pexels for B-roll video clips matching a keyword."""
    if not settings.PEXELS_API_KEY:
        return []
    try:
        response = httpx.get(
            PEXELS_API_URL,
            params={"query": query, "per_page": per_page, "orientation": "portrait"},
            headers={"Authorization": settings.PEXELS_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Pexels B-roll search failed for %r: %s", query, exc)
        return []

    results = []
    for video in data.get("videos", []):
        files = sorted(video.get("video_files", []), key=lambda f: f.get("width", 0))
        if files:
            results.append({"url": files[0]["link"], "source": "pexels"})
    return results


def search_broll(query: str, per_page: int = 3) -> list[dict[str, Any]]:
    """Try Pixabay first, then Pexels. Returns [] if neither is configured or both fail."""
    results = search_broll_pixabay(query, per_page)
    if results:
        return results
    return search_broll_pexels(query, per_page)


def download_broll(url: str, dest_path: Path) -> Path:
    """Download a single B-roll clip to disk."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream("GET", url, timeout=30) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=1024 * 256):
                    f.write(chunk)
        return dest_path
    except httpx.HTTPError as exc:
        logger.error("Failed to download B-roll clip %s: %s", url, exc)
        raise ExternalServiceError(f"Failed to download B-roll clip: {exc}") from exc
