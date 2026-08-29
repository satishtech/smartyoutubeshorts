"""Filesystem helpers for storing project media under STORAGE_DIR/{project_id}/."""
from pathlib import Path

from app.config import settings


def project_dir(project_id: int) -> Path:
    """Return (and create) the storage directory for a project."""
    path = Path(settings.STORAGE_DIR) / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def shorts_dir(project_id: int) -> Path:
    path = project_dir(project_id) / "shorts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def source_video_path(project_id: int, filename: str) -> Path:
    return project_dir(project_id) / f"source{Path(filename).suffix or '.mp4'}"


def project_thumbnail_path(project_id: int) -> Path:
    return project_dir(project_id) / "thumbnail.jpg"


def resolve(path_str: str) -> Path:
    """Resolve a stored relative/absolute path string to a Path."""
    p = Path(path_str)
    return p if p.is_absolute() else Path.cwd() / p
