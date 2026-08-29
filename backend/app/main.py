"""FastAPI application entrypoint."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth.rate_limit import limiter
from app.config import settings
from app.exceptions import register_exception_handlers
from app.routers import auth, highlights, projects, shorts, transcripts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(transcripts.router)
app.include_router(highlights.router)
app.include_router(shorts.projects_router)
app.include_router(shorts.shorts_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint used by Docker/orchestration to verify the app is up."""
    return {"status": "healthy"}
