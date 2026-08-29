# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# ffmpeg is required at runtime for transcription (audio extraction) and shorts
# rendering (crop/trim/subtitle burn-in). yt-dlp itself ships as a pip package
# (see requirements.txt) but benefits from ffmpeg being present for merging.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY alembic.ini .
COPY ./alembic ./alembic

# Non-root runtime user; STORAGE_DIR is created and owned by appuser so
# uploaded/rendered media can be written without root privileges.
RUN useradd -m appuser \
    && mkdir -p /app/app/storage \
    && chown -R appuser:appuser /app

USER appuser

ENV STORAGE_DIR=/app/app/storage \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
