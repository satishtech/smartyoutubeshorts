# CLAUDE.md - Smart YouTube Shorts Generator

## Stack

FastAPI + Python 3.11 · React/Vite/TS · PostgreSQL+SQLAlchemy · JWT+Google OAuth · Tailwind+shadcn/ui · ffmpeg/yt-dlp/Whisper/Claude · no payments

## Structure

```
backend/app/{main,config,database}.py
backend/app/models/{user,project,transcript,highlight_segment,short}.py
backend/app/routers/{auth,projects,transcripts,highlights,shorts}.py
backend/app/services/{youtube_import,transcription,highlight_detection,video_render,broll}.py
backend/app/storage/            # gitignored media
backend/alembic/, backend/tests/
frontend/src/components/{UploadForm,Timeline,ShortsGrid,ProgressStatus}/
frontend/src/pages/{Login,Register,Profile,ProjectsDashboard,NewProject,ProjectWorkspace,ProjectResults}.tsx
frontend/src/{hooks,services,context,types}/
```

## Code Standards

- Python: type hints required, async endpoints, docstrings on public functions
- TypeScript: interfaces required, no `any`
- Long-running media work (ffmpeg/yt-dlp/Whisper/Claude) always via `BackgroundTasks`, never inline in a handler — update `Project.status` as it progresses

## Forbidden

`print()` (use `logging`) · plain passwords (bcrypt) · hardcoded secrets · `any` in TS · `console.log` in prod · inline styles · sync media calls in request handlers · serving `storage/` files without an authenticated, ownership-checked endpoint

## Domain Rules

- Every `Short` ≤60s, 9:16, hard-burned subtitles (no soft-sub track)
- `HighlightSegment` count ≤ `num_shorts_requested` (1-10), never exceeded
- Every project/transcript/highlight/short route checks the resource belongs to the requesting user
- B-roll/music are opt-in toggles, default off
- No publishing integrations (YouTube/TikTok/Instagram) — download only

## API Conventions

`/api/` prefix, plural nouns. Status codes: 200/201/400/401/403/404/409/422 (422 for `num_shorts` out of 1-10 range).

## Auth

JWT: access 30min, refresh 7d, HS256. Google OAuth: verify `state` param.

## Env Vars

```env
DATABASE_URL=postgresql://user:password@localhost:5432/shorts_generator
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
OPENAI_API_KEY=          # Whisper transcription
ANTHROPIC_API_KEY=       # highlight detection
PIXABAY_API_KEY=         # optional B-roll
PEXELS_API_KEY=          # optional B-roll
STORAGE_DIR=./backend/app/storage
FFMPEG_BIN=ffmpeg
VITE_API_URL=http://localhost:8000
```

## Commands

```bash
cd backend && pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
docker-compose up -d
pytest backend/tests -v && cd frontend && npm test
ruff check backend/ && cd frontend && npm run lint
```

## Commits

`feat([module]): ...` `fix([module]): ...` `refactor([module]): ...` `test([module]): ...` `docs: ...`

## Agents (essential only)

- **BACKEND-AGENT** — DB models/migrations, auth, all API routes, media pipeline services, backend tests
- **FRONTEND-AGENT** — pages/components, upload flow, interactive timeline, preview grid, types, frontend tests

No separate DEVOPS/TEST/REVIEW agents — Docker setup, tests, and a security pass are done inline by the two agents above to keep buildathon scope lean.
