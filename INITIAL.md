# INITIAL.md - Smart YouTube Shorts Generator

> AI Buildathon MVP. Local, free, no payments.

## PRODUCT

**Name:** Smart YouTube Shorts Generator
**Description:** Upload a video or paste a YouTube URL → AI transcribes it, detects highlight moments, and generates multiple 9:16 vertical shorts (≤60s, subtitled) with an interactive preview/edit step before export.
**Target User:** Content creators, YouTubers, podcasters, educators, marketers.

## TECH STACK

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + Python 3.11+ |
| Frontend | React + Vite + TypeScript |
| DB | PostgreSQL + SQLAlchemy |
| Auth | JWT (email/password) + Google OAuth |
| UI | Tailwind + shadcn/ui |
| Payments | None |
| Media | ffmpeg, yt-dlp, OpenAI Whisper (transcription), Anthropic Claude (highlight detection) |
| Jobs | FastAPI `BackgroundTasks` + DB status polling (no Redis/Celery) |

## MODULES

**1. Auth (built-in)** — User, RefreshToken. `/auth/register|login|refresh|logout|google|me`. Pages: /login /register /profile

**2. Video Import**
`Project(id, user_id, title, source_type[upload|youtube_url], source_url, source_video_path, duration_seconds, status[pending|downloading|transcribing|detecting_highlights|ready_for_review|generating_shorts|completed|failed], status_message, num_shorts_requested[1-10], burn_subtitles, use_broll, created_at, updated_at)`
`POST/GET /api/projects`, `GET/DELETE /api/projects/{id}`, `GET /api/projects/{id}/status`
Pages: /projects/new

**3. Transcription**
`Transcript(id, project_id, full_text, segments JSON[{start,end,text}], language)`
`GET /api/projects/{id}/transcript` (auto-runs after import; no manual trigger)

**4. Highlight Detection (Claude)**
`HighlightSegment(id, project_id, order, start_time, end_time, title, reason, score, created_at, updated_at)`
`POST /api/projects/{id}/highlights/detect`, `GET .../highlights`, `PUT/DELETE .../highlights/{hid}`

**5. Shorts Generation (ffmpeg)**
`Short(id, project_id, highlight_segment_id, file_path, thumbnail_path, duration_seconds, has_subtitles, has_broll, status[pending|rendering|ready|failed])`
`POST /api/projects/{id}/shorts/generate`, `GET .../shorts`, `GET /api/shorts/{sid}/stream`

**6. Preview & Export**
`GET /api/shorts/{sid}/download`, `GET /api/projects/{id}/download-zip`
Pages: /projects/{id} (workspace: transcript + timeline + controls), /projects/{id}/results (preview grid + downloads)

**7. Dashboard** — reuses `GET /api/projects`. Page: /projects (list, doubles as home)

## MVP SCOPE

Must have: auth, upload/YouTube import, transcription, AI highlight detection (1-10 selectable), timeline start/end adjustment, 9:16 ≤60s render, burned-in subtitles, preview, individual/ZIP download, live status polling.

Nice-to-have (only if time permits): B-roll (Pixabay/Pexels), background music toggle, subtitle style customization.

Out of scope: publishing to YouTube/TikTok/Instagram, payments, multi-tenant/teams.

## ACCEPTANCE CRITERIA

- [ ] Register/login (password + Google), JWT refresh works, protected routes redirect
- [ ] Upload or YouTube URL → project status advances visibly through pipeline; bad URLs error clearly
- [ ] Transcript with timestamps viewable; highlight count == num_shorts_requested (or fewer if source too short), each ≤60s
- [ ] Timeline drag-adjust persists
- [ ] Shorts are 9:16, ≤60s, hard-burned subtitles, individually previewable
- [ ] Individual + ZIP download work
- [ ] Ownership enforced on every project/short route
- [ ] Docker builds and runs (backend + ffmpeg + frontend)

## SPECIAL REQUIREMENTS

- ffmpeg + yt-dlp available in runtime; all media work via `BackgroundTasks`, never inline in a request handler
- Storage under `storage/{project_id}/`, served only via authenticated endpoints
- Rate limit auth endpoints; validate upload type/size and YouTube URLs; OAuth `state` CSRF check

## AGENTS (essential only)

| Agent | Scope |
|-------|-------|
| BACKEND-AGENT | DB models + migrations, auth, all API routes, media pipeline services (import/transcribe/detect/render), tests for these |
| FRONTEND-AGENT | All pages/components, upload flow, interactive timeline, preview grid, types, frontend tests |

Docker/CI and a security pass happen as a final short review step within these two agents' work, not as separate parallel agents — keeps the buildathon scope lean.

---
```bash
/generate-prp INITIAL.md
/execute-prp PRPs/smart-youtube-shorts-generator-prp.md
```
