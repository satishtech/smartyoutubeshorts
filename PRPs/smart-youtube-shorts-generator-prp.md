# PRP: Smart YouTube Shorts Generator

> Lean blueprint, 2-agent execution (BACKEND-AGENT, FRONTEND-AGENT). Full model/endpoint detail lives in INITIAL.md — this file sequences the work, it doesn't repeat it.

## METADATA

| Field | Value |
|-------|-------|
| Product | Smart YouTube Shorts Generator |
| Type | Local AI Buildathon MVP |
| Version | 1.0 |
| Complexity | Medium (media pipeline is the risk, not CRUD) |

## OVERVIEW

Upload/YouTube URL → transcribe → AI-detect highlights → user adjusts timeline → render 9:16 ≤60s shorts with burned subtitles → preview → download individually or as ZIP. No payments, no publishing integrations.

MVP: see INITIAL.md § MVP SCOPE (unchanged, not repeated here).

## TECH STACK

FastAPI+Py3.11 · React/Vite/TS · PostgreSQL+SQLAlchemy · JWT+Google OAuth · Tailwind+shadcn/ui · ffmpeg/yt-dlp/Whisper/Claude · `BackgroundTasks` for all media jobs (no Celery/Redis)

Skills: `skills/BACKEND.md`, `skills/FRONTEND.md`, `skills/DATABASE.md` (read by BACKEND-AGENT), `skills/TESTING.md`, `skills/DEPLOYMENT.md`

## SCALE

Models: 6 (User, RefreshToken, Project, Transcript, HighlightSegment, Short)
Endpoints: ~21 · Pages: 7 · Modules: 7 (see INITIAL.md for full schemas)

## AGENT ASSIGNMENT

| Agent | Owns |
|-------|------|
| **BACKEND-AGENT** | All models + migrations (using `skills/DATABASE.md` conventions), auth, all `/api/*` routes, media services (`youtube_import`, `transcription`, `highlight_detection`, `video_render`, `broll`), Dockerfile for backend (ffmpeg+yt-dlp installed), backend tests, `ruff`/security pass on own code |
| **FRONTEND-AGENT** | Vite/TS setup, all pages/components (per `skills/FRONTEND.md`), upload flow, interactive timeline (drag start/end), preview grid + downloads, status polling UI, frontend tests, `npm run lint`/type-check |

No DATABASE/DEVOPS/TEST/REVIEW agents run separately — each owning agent validates its own slice (see Validation Gates). This is a deliberate scope cut for buildathon speed.

## PHASE PLAN

**Phase 1 — Foundation (parallel)**
- BACKEND-AGENT: `main.py`, `config.py`, `database.py`, all 6 models, Alembic migration, `docker-compose.yml` + Dockerfile (ffmpeg/yt-dlp baked in), `.env.example`
- FRONTEND-AGENT: Vite+TS scaffold, Tailwind/shadcn setup, folder structure, base layout/router, `.env.example`

Gate 1: `alembic upgrade head` · `npm install` · `docker-compose config`

**Phase 2 — Modules (sequential by dependency, backend+frontend paired per module)**
1. Auth: JWT+bcrypt+Google OAuth endpoints ↔ /login /register /profile
2. Video Import: upload+yt-dlp import, status polling ↔ /projects, /projects/new
3. Transcription: Whisper service, auto-runs post-import ↔ transcript panel (in workspace page)
4. Highlight Detection: Claude service, CRUD on HighlightSegment ↔ interactive timeline in /projects/{id}
5. Shorts Generation: ffmpeg render pipeline (crop, hard-sub burn-in, optional B-roll) ↔ generation controls in /projects/{id}
6. Preview & Export: stream/download/zip endpoints ↔ /projects/{id}/results

Each step: BACKEND-AGENT ships the endpoints/service first, FRONTEND-AGENT wires the page against them; independent modules (e.g. Transcription UI panel vs. Highlight endpoints) may run in parallel once their dependency is ready.

Gate 2: `ruff check backend/` · `npm run type-check` · manual smoke test of full pipeline on one short sample video

**Phase 3 — Hardening (folded into both agents, not separate)**
- BACKEND-AGENT: ownership checks on every route, rate limit on auth, input validation (file type/size, URL format), `pytest --cov`
- FRONTEND-AGENT: error/loading states on all async calls, `npm test`

Final Gate: `docker-compose up -d` · `curl localhost:8000/health` · end-to-end run (upload → download ZIP) in the browser

## VALIDATION GATES

| Gate | Commands |
|------|----------|
| 1 | `alembic upgrade head`, `npm install`, `docker-compose config` |
| 2 | `ruff check backend/`, `npm run type-check`, manual pipeline smoke test |
| 3 (final) | `pytest --cov --cov-fail-under=80`, `npm test`, `docker-compose up -d`, `curl localhost:8000/health` |

## ENV VARS

See CLAUDE.md § Env Vars (DATABASE_URL, SECRET_KEY, GOOGLE_CLIENT_ID/SECRET, OPENAI_API_KEY, ANTHROPIC_API_KEY, PIXABAY/PEXELS_API_KEY optional, STORAGE_DIR, FFMPEG_BIN, VITE_API_URL) — not duplicated here.

## NEXT STEP

```bash
/execute-prp PRPs/smart-youtube-shorts-generator-prp.md
```
