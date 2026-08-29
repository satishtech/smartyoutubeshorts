"""Shared pytest fixtures. Uses an in-memory SQLite DB and mocks all external services."""
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.jwt import create_access_token, hash_password
from app.auth.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.models.highlight_segment import HighlightSegment
from app.models.project import Project, ProjectStatus, SourceType
from app.models.transcript import Transcript
from app.models.user import User

TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Rate limiting is disabled during tests so a full suite run never trips 429s.
limiter.enabled = False


@pytest.fixture(autouse=True)
def _no_background_pipelines(monkeypatch):
    """Prevent router tests from triggering real media pipeline work.

    BackgroundTasks execute synchronously within TestClient's request/response
    cycle, so without this, every project/highlight/short "trigger" endpoint
    would actually try to call yt-dlp/ffmpeg/OpenAI/Anthropic. Service-level
    behavior is covered separately (with explicit mocks) in test_services.py.
    """
    import app.routers.highlights as highlights_router
    import app.routers.projects as projects_router
    import app.routers.shorts as shorts_router

    monkeypatch.setattr(projects_router, "run_import_pipeline", lambda *a, **k: None)
    monkeypatch.setattr(highlights_router, "run_highlight_detection_pipeline", lambda *a, **k: None)
    monkeypatch.setattr(shorts_router, "run_shorts_generation_pipeline", lambda *a, **k: None)


@pytest.fixture(autouse=True)
def _storage_dir(monkeypatch):
    """Redirect STORAGE_DIR to a throwaway temp directory for every test."""
    tmp_dir = tempfile.mkdtemp(prefix="shorts_test_storage_")
    from app.config import settings

    monkeypatch.setattr(settings, "STORAGE_DIR", tmp_dir)
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db) -> User:
    user = User(email="test@example.com", hashed_password=hash_password("password123"), full_name="Test User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db) -> User:
    user = User(email="other@example.com", hashed_password=hash_password("password123"), full_name="Other User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(other_user) -> dict:
    token = create_access_token({"sub": str(other_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project(db, test_user) -> Project:
    p = Project(
        user_id=test_user.id,
        title="Test Project",
        source_type=SourceType.upload,
        source_video_path="does/not/matter.mp4",
        duration_seconds=120.0,
        status=ProjectStatus.ready_for_review,
        num_shorts_requested=3,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def transcript(db, project) -> Transcript:
    t = Transcript(
        project_id=project.id,
        full_text="Hello world this is a test transcript.",
        segments=[
            {"start": 0.0, "end": 2.0, "text": "Hello world"},
            {"start": 2.0, "end": 4.0, "text": "this is a test transcript."},
        ],
        language="en",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def highlight(db, project) -> HighlightSegment:
    h = HighlightSegment(
        project_id=project.id,
        order=0,
        start_time=0.0,
        end_time=10.0,
        title="Great moment",
        reason="It's engaging",
        score=0.9,
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    return h
