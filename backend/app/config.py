"""Application settings loaded from environment variables (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration.

    All values are read from environment variables / a local .env file.
    Nothing here should ever be hardcoded in application code.
    """

    APP_NAME: str = "Smart YouTube Shorts Generator"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/shorts_generator"

    # Auth / JWT
    SECRET_KEY: str = "dev-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # External media/AI APIs
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    PIXABAY_API_KEY: str = ""
    PEXELS_API_KEY: str = ""

    # Storage / media
    STORAGE_DIR: str = "./backend/app/storage"
    FFMPEG_BIN: str = "ffmpeg"
    FFPROBE_BIN: str = "ffprobe"
    MAX_UPLOAD_SIZE_MB: int = 500

    # CORS / frontend
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
