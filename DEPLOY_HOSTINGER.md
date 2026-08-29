# Deploying to a Hostinger VPS

Minimal path to get this running on a Hostinger VPS (Ubuntu 22.04+) using the
`docker-compose.yml` at the repo root. No Kubernetes, no managed DB — one box,
Docker Compose, done.

## 1. Provision

- Hostinger hPanel → VPS → pick a plan (2 vCPU / 4GB RAM minimum — ffmpeg
  rendering and Whisper calls are the heavy parts) → OS: **Ubuntu 22.04 LTS**.
- Point your domain's A record at the VPS's public IP (skip if using the
  server by IP only, no HTTPS).

## 2. Install Docker

SSH in, then:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # log out/in once for this to take effect
sudo apt-get install -y docker-compose-plugin
```

## 3. Get the code + configure

```bash
git clone <your-repo-url> shorts-generator && cd shorts-generator
cp .env.example .env
nano .env   # set SECRET_KEY, DB_PASSWORD, OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
```

Set `VITE_API_URL` and `GOOGLE_REDIRECT_URI` in `.env` to your real domain
(e.g. `https://shorts.example.com`) before building — `VITE_API_URL` is baked
into the frontend at build time, not read at runtime.

## 4. Build and run

```bash
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head
```

- Backend: `http://<vps-ip>:8000` (proxied under `/api` by the frontend container)
- Frontend: `http://<vps-ip>:80`

## 5. Put HTTPS in front of it (recommended)

Simplest option — Caddy as a host-level reverse proxy in front of the two
exposed ports, handling Let's Encrypt automatically:

```bash
sudo apt-get install -y caddy
```

`/etc/caddy/Caddyfile`:

```
shorts.example.com {
    reverse_proxy localhost:80
}
```

```bash
sudo systemctl reload caddy
```

Then re-run step 3/4 with `VITE_API_URL=https://shorts.example.com` and
`GOOGLE_REDIRECT_URI=https://shorts.example.com/api/auth/google/callback`,
and rebuild (`docker compose build frontend && docker compose up -d`).

## 6. Operational notes

- Rendered media lives in the `media_storage` Docker volume (mounted at
  `/app/app/storage` in the backend container) and Postgres data in
  `postgres_data` — both persist across `docker compose down` (not `down -v`).
- Storage grows fast (source videos + rendered shorts). Set up a cron job to
  prune old `Project`s/files, or attach a larger Hostinger block storage
  volume and point `STORAGE_DIR` at it via `.env`.
- Logs: `docker compose logs -f backend`
- Update/redeploy: `git pull && docker compose build && docker compose up -d && docker compose exec backend alembic upgrade head`
- This is a single-VPS deployment — the in-memory rate limiter and
  `BackgroundTasks` job runner (see CLAUDE.md) assume one backend instance;
  don't scale `backend` to multiple replicas without moving to Redis-backed
  rate limiting and a real task queue first.
