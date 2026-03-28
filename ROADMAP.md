# ArcadeForge — Project Roadmap

> Last updated: 2026-03-28

## Status Legend

- [ ] Not started
- [~] In progress
- [x] Completed
- [!] Blocked / changed

---

## Phase 1 — Foundation & Monorepo Setup

**Goal:** Project skeleton that boots with one command. No features — only clean structure.

### Commit 1: `feat: bootstrap ArcadeForge monorepo workspace`

- [x] 1.1 Create root repo structure (folders, .gitignore, README)
- [x] 1.2 Add `pnpm-workspace.yaml`
- [x] 1.3 Create `apps/web` — Next.js 15 skeleton (App Router, TailwindCSS)
- [x] 1.4 Create `apps/api` — FastAPI skeleton (uvicorn, pydantic-settings)
- [x] 1.5 Create `packages/shared` — shared TypeScript types stub
- [x] 1.6 Create `infra/docker-compose.yml` — PostgreSQL, Redis, MinIO
- [x] 1.7 Create `scripts/dev.sh` — one-command dev startup
- [x] 1.8 Create root `.env.example`

**Checkpoint:** ✅ workspace recognized by pnpm, `apps/web` builds, `apps/api` loads, folder layout matches plan.

### Commit 2: `feat: add docker compose core services (postgres, redis, minio)`

- [x] 1.9 Docker Compose with PostgreSQL 16, Redis 7, MinIO
- [x] 1.10 Health checks for all services
- [x] 1.11 Nginx reverse proxy config (`services/reverse-proxy/nginx.conf`)
- [x] 1.12 `docker compose up` boots all services cleanly ✅ All healthy + Alembic migration verified

### Commit 3: `feat: initialize FastAPI config and Alembic baseline`

- [x] 1.13 pydantic-settings config loader (`apps/api/app/config.py`)
- [x] 1.14 SQLAlchemy async engine + session setup
- [x] 1.15 Alembic init + first migration (7 tables: users, sessions, user_pages, games, game_versions, validation_runs, play_sessions)
- [x] 1.16 arq workers wired to Redis config (`workers/shared_settings.py`)
- [x] 1.17 API health endpoint with lifespan hooks (`GET /api/health`)

---

## Phase 2 — Authentication & User System

**Goal:** Secure email+password registration and login with HttpOnly session cookies.

- [x] 2.1 Argon2id password hashing (`apps/api/app/auth/passwords.py`)
- [x] 2.2 `POST /api/auth/register` endpoint
- [x] 2.3 `POST /api/auth/login` → HttpOnly cookie session
- [x] 2.4 `POST /api/auth/logout` → invalidate session
- [x] 2.5 Session middleware + session ID rotation (CSPRNG 256-bit IDs, rotate on login)
- [x] 2.6 CSRF protection (SameSite=Lax, `__Host-` cookie prefix)
- [x] 2.7 Rate limiting on auth endpoints (Redis-backed: 5 login/min, 3 register/10min)
- [ ] 2.8 Email verification flow (optional, behind env flag) — deferred, nice-to-have
- [x] 2.9 Password reset flow — ✅ Completed in Phase 10 (token-based, single-use, 30min TTL)
- [~] 2.10 Frontend auth pages — moved to Phase 3 first slice
- [x] 2.11 Auth dependency for protected routes (`get_current_user`)
- [x] 2.12 `GET /api/auth/me` endpoint
- [x] 2.13 Integration tests: 20 tests covering register, login, session rotation, logout, /me, rate limits
- [x] 2.14 Pydantic schemas with validation (email, username format, password length)

---

## Phase 3 — Dashboard, Auth Pages & Personal Pages

**Goal:** Frontend auth pages, dashboard, navbar, and public profile. First user-visible slice.

### Slice 1: Auth pages + API client (from Phase 2.10)
- [x] 3.1 API client library (`apps/web/src/lib/api.ts`)
- [x] 3.2 `/auth/login` page
- [x] 3.3 `/auth/register` page
- [x] 3.4 Auth state management (Zustand store)

### Slice 2: Layout + Dashboard
- [x] 3.5 Root layout with Navbar (auth-aware: avatar, logout, "Create Game")
- [x] 3.6 `/dashboard` page (My Games grid placeholder, Create Game CTA)
- [x] 3.7 Protected route middleware (redirect to /auth/login if not authenticated)

### Slice 3: Profile + Settings
- [x] 3.8 `/u/[username]` public profile page (avatar initial, join date, games placeholder)
- [x] 3.9 `/settings` page (username change + password change with current pw verification)
- [x] 3.10 API: `PATCH /api/auth/me` (partial update), `GET /api/users/:username` (public profile)
- [x] 3.11 Tests: 9 new tests (profile lookup, case-insensitive, username change, password change, auth checks)

---

## Phase 4 — Game CRUD & AI Generation

**Goal:** Users create games via prompt+genre, stored with versioning.

### Slice 1: Creation pipeline
- [x] 4.1 Genre catalog API (`GET /api/genres`, `GET /api/genres/:id`)
- [x] 4.2 `POST /api/games` → 202 Accepted, enqueue arq generator job
- [x] 4.3 Create game form (`/create` — genre selector, title, prompt, difficulty)
- [x] 4.4 Tests: 12 new tests (genres, create, list, detail, delete, auth) — 41 total passing
- [x] 4.4a Game detail page `/games/[gameId]` (Overview + Code tabs)
- [x] 4.4b Game list API (`GET /api/games`), game delete (`DELETE /api/games/:id`)

### Slice 2: Worker + persistence
- [x] 4.5 Generator worker calls template engine via `asyncio.to_thread()`
- [x] 4.6 Game version v0 created automatically with blueprint + source code
- [x] 4.7 Save generated files to `/data/workspaces/<user_id>/<game_id>/v0/` (atomic via tmpdir)
- [x] 4.7a Game status field (queued → generating → ready / failed) + migration
- [x] 4.7b GET /api/games/:id/status endpoint
- [x] 4.7c Template-based generator for 4 genres with difficulty presets
- [x] 4.7d 8 new generator tests (49 total passing)

### Slice 3: Read path
- [x] 4.8 Game detail page `/games/:id` (status banners, blueprint metadata, controls, code viewer)
- [x] 4.9 Version history displayed with metadata
- [x] 4.10 Dashboard shows real game list with status badges, play counts, genre, dates
- [x] 4.10a Status polling: game detail auto-refreshes when status is queued/generating

### Slice 4: Realtime progress — deferred (polling works, revisit before Phase 6)
- [ ] 4.11 WebSocket progress channel for generation status
- [ ] 4.12 Client subscribes while job is running

### Slice 5: Optional/harder — deferred
- [ ] 4.13 LLM-assist mode (optional, behind `LLM_MODE` env)
- [ ] 4.14 Async-compatible game loop (WASM-ready from day 1)

---

## Phase 5 — Validation & Artifacts

**Goal:** Automated game validation with reports, screenshots, and artifacts.

- [x] 5.1 Static code scanner with pluggable strategy (DenylistStrategy, 25+ patterns)
- [x] 5.2 `POST /api/games/:id/validate` → scanner + arq validator worker
- [x] 5.3 `POST /api/games/:id/scan` → synchronous scan endpoint
- [x] 5.4 `GET /api/games/:id/validations` → list validation runs
- [x] 5.5 Validator worker: structural smoke checks (pygame import, game loop, QUIT handler, display update)
- [x] 5.6 Validation tab on game detail page (run validation, view results, scan status)
- [x] 5.7 Auto-validate: scanner runs automatically after generation in generator worker
- [x] 5.8 17 new tests (13 scanner + 4 validation endpoints) — 66 total passing
- [ ] 5.9 Artifact storage (screenshots, reports to S3/MinIO) — deferred to Phase 6 prep

---

## Phase 6 — Cloud Play (noVNC Sandbox) ⚠️ HARDEST PHASE

**Goal:** Users play games in-browser via server-side sandbox container.

### Milestone 1: Sandbox image + play pipeline (complete)
- [x] 6.1 Sandbox Docker image (Python + pygame + Xvfb + x11vnc + websockify + noVNC)
- [x] 6.2 Security baseline: non-root user, seccomp profile, read-only FS, tmpfs /tmp
- [x] 6.3 Sandbox orchestrator (`sandbox.py`): start/stop/status + port allocation
- [x] 6.4 `POST /api/games/:id/play` → 202 Accepted, enqueue sandbox worker
- [x] 6.5 `GET /api/games/:id/play/:sessionId` → poll session status + ws_url
- [x] 6.6 `POST /api/games/:id/play/:sessionId/stop` → kill container
- [x] 6.7 Sandbox worker: start container with game mounted read-only, return ws_url
- [x] 6.8 `GamePlayerNoVNC.tsx` — iframe-based noVNC embed with status indicator
- [x] 6.9 Play tab on game detail page with "Play Now" button + session polling
- [x] 6.10 `play_count` incremented on session start
- [x] 6.11 Nginx WebSocket proxy with proper Upgrade headers + 30min timeout
- [x] 6.12 Resource limits: CPU quota, memory limit, network=none (configurable)

### Milestone 2: Hardening + testing (complete)
- [x] 6.13 Built sandbox image on Docker Desktop (684MB, pygame-ce 2.5.7, verified Xvfb+VNC+noVNC)
- [x] 6.14 TTL reaper: background task kills expired containers + marks sessions expired
- [x] 6.15 Stale session reaper: cleans up sessions stuck in "starting" > 2 min
- [x] 6.16 Max concurrent sessions per user (2 max, returns 429)
- [x] 6.17 Integration tests: 6 play session tests (start, not-ready, play_count, not-found, concurrency, reaper)
- [x] 6.18 Reaper integrated into FastAPI lifespan as background task
- [ ] 6.19 E2E test with Playwright — deferred to Phase 11

---

## Phase 7 — Game Editor (2 weeks)

- [x] 7.1 Monaco Editor component (`GameCodeEditor.tsx` with @monaco-editor/react)
- [x] 7.2 `POST /api/games/:id/versions` — save as new version (v1, v2, etc.)
- [x] 7.3 Code tab replaced with live Monaco editor (read-only for non-owners)
- [x] 7.4 Auto-validate on save (scanner + enqueue smoke checks)
- [x] 7.5 Dirty state tracking + "Unsaved changes" indicator
- [x] 7.6 6 new tests (create version, increments, auth, ownership, listing)
- [x] 7.7 Fixed version numbering bug (`0 or -1` → explicit `None` check)
- [ ] 7.8 Version diff viewer (Monaco DiffEditor) — deferred to polish phase

---

## Phase 8 — Public Arcade (2 weeks)

- [x] 8.1 `GET /api/arcade/games` — public listing with search, genre filter, trending/newest sort
- [x] 8.2 `/arcade` page with game cards, search bar, genre pills, sort toggle
- [x] 8.3 Genre placeholder thumbnails (emoji-based, real screenshots deferred to artifact storage)
- [x] 8.4 Owner username displayed on game cards
- [x] 8.5 Prompts hidden from public API responses (privacy)
- [x] 8.6 Guest play rate limiting: 3 sessions/hour per IP, returns 429 + Retry-After
- [x] 8.7 7 new tests (listing, privacy, search, genre filter, prompt hiding, username, no-auth)
- [x] 8.8 Suspense boundary for search params SSR compatibility

---

## Phase 9 — Sharing & Social (1 week)

- [x] 9.1 Open Graph meta tags (og:title, og:description, og:type, twitter:card) via generateMetadata
- [x] 9.2 Embeddable game player at `/embed/games/[id]` — minimal chrome, no navbar, iframe-ready
- [x] 9.3 Embed snippet displayed on game overview (copyable HTML)
- [x] 9.4 Copy share link button on game header
- [x] 9.5 `POST /api/games/:id/fork` — fork public game into user's library (copies code + metadata)
- [x] 9.6 Fork button on game detail (public games only, not for owner)
- [x] 9.7 Embed layout — standalone route group with no navbar/auth for clean iframe embedding
- [x] 9.8 4 new tests (fork success, private fork blocked, unauth fork blocked, code copied)
- [x] 9.9 89 total tests passing

---

## Phase 10 — Security Hardening (2-3 weeks)

### Complete:
- [x] 10.0 **Password reset** (closes deferred 2.9): token-based, single-use, hashed at rest, 30min TTL, all sessions invalidated, generic responses
- [x] 10.1 `SECURITY.md` — vulnerability reporting policy + security model docs
- [x] 10.2 Rate limiting on reset endpoints (3/15min per IP)
- [x] 10.3 6 new tests: generic response, full flow, invalid token, single-use, session invalidation, weak password

### Deferred to pre-launch:
- [ ] 10.4 Audit logging for security events
- [ ] 10.5 Account security (session listing, lockout)
- [ ] 10.6 Privacy (data export, account deletion)
- [ ] 10.7 Dependency scanning in CI (Phase 11)

---

## Phase 11 — Testing & CI/CD (2-3 weeks)

- [x] 11.1 `ci-web.yml` — runs on PR + push to main:
  - Web build + typecheck (pnpm, Node 20)
  - API unit tests (no DB: passwords, generator, scanner)
  - API integration tests (Postgres 16 + Redis 7 service containers, Alembic migrations, full pytest suite)
  - Test results uploaded as artifacts
- [x] 11.2 `nightly-eval.yml` — runs daily at 03:00 UTC + manual trigger:
  - Full test suite
  - Game generation eval across 4 genres × 3 difficulties (12 combinations)
  - Scanner pass rate validation
- [x] 11.3 `docker-build.yml` — runs on sandbox-runtime changes:
  - Docker Buildx with GHA cache
  - SOURCE_DATE_EPOCH for reproducibility
  - SBOM + provenance attestations
  - Sandbox smoke test (build → start → verify noVNC HTTP 200)
- [x] 11.4 pytest markers: unit, integration, e2e (configured in pyproject.toml)
- [ ] 11.5 Playwright E2E tests — deferred (requires browser + API + sandbox running together)
- [x] 11.6 95 tests across all layers

---

## Phase 12 — Production Launch (1-2 weeks)

### Launch gates (closes deferred items):
- [x] 12.0 Dependency review in CI (`actions/dependency-review-action`, fails on high severity)
- [x] 12.1 Production `docker-compose.prod.yml` (Postgres, Redis with password, API, Nginx, Certbot)
- [x] 12.2 SSL-ready Nginx config (`nginx-prod.conf`): HTTPS redirect, Let's Encrypt, HSTS, security headers
- [x] 12.3 Database backup script (`scripts/backup-db.sh`): pg_dump custom format, 7-day rotation
- [x] 12.4 CDN-ready static asset config in Nginx (/_next/static with immutable cache)

### Product launch:
- [x] 12.5 Landing page: hero, features grid, genre showcase, CTA sections, footer
- [x] 12.6 `CONTRIBUTING.md` — setup guide, code style, commit conventions, how to add genres
- [x] 12.7 `CODE_OF_CONDUCT.md` — Contributor Covenant v2.0
- [x] 12.8 `SECURITY.md` — already complete from Phase 10

### Deferred to post-launch:
- [ ] 12.9 Sentry SDK integration (config ready via SENTRY_DSN env, SDK not yet wired)
- [ ] 12.10 Prometheus metrics endpoint
- [ ] 12.11 Certbot initial certificate issuance (requires live domain)

---

## Phase 13 — WASM Runtime / pygbag (Future)

- [ ] 13.1 pygbag integration (compile pygame → HTML+WASM)
- [ ] 13.2 WASM build worker
- [ ] 13.3 CDN hosting for WASM builds
- [ ] 13.4 Fallback to noVNC for incompatible games

---

## Phase 13 — Cloud Deployment

**Goal:** Deploy to cloud without local infrastructure. No ports, no Docker Desktop.

- [x] 13.1 Add cloud config settings (S3, Fly.io, cookie domain, DB SSL)
- [x] 13.2 Create S3 storage abstraction (local filesystem or S3/R2)
- [x] 13.3 Fix Redis URL parsing for Upstash (TLS + password support)
- [x] 13.4 Create Fly.io Machines sandbox driver (alternative to Docker)
- [x] 13.5 Update Next.js rewrite proxy for configurable API_URL
- [x] 13.6 Add CORS expose_headers and cookie domain/secure config
- [x] 13.7 Create Dockerfile.cloud and fly.toml for API + workers
- [x] 13.8 Create GitHub Actions CI/CD (test + deploy to Fly.io)
- [x] 13.9 Deploy API to Fly.io (`arcadeforge-api.fly.dev`)
- [x] 13.10 Deploy Postgres to Fly.io + run migrations
- [x] 13.11 Deploy Redis via Upstash (pay-as-you-go)
- [x] 13.12 Deploy frontend to Vercel (`arcadeforge-web.vercel.app`)
- [ ] 13.13 Deploy sandbox image to Fly.io registry
- [ ] 13.14 Deploy workers to Fly.io
- [ ] 13.15 Set up Cloudflare R2 for object storage
- [ ] 13.16 End-to-end verification (register, create game, play)

**Checkpoint:** Full stack running in cloud. API health check passes. Frontend proxies to API.

---

## Phase 14 — Templates Marketplace (Future)

- [ ] 14.1 Publish genre templates and mechanics modules
- [ ] 14.2 Template catalog with ratings
- [ ] 14.3 Fork/remix from templates

---

## Tech Stack (Locked)

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 15 + React + TailwindCSS + Zustand |
| Backend | FastAPI + Pydantic Settings + SQLAlchemy |
| Database | PostgreSQL 16 + Alembic migrations |
| Queue | arq (async Redis queue) |
| Cache/Sessions | Redis 7 |
| Object Storage | MinIO (dev) / S3 (prod) |
| Game Runtime (v1) | Sandbox container + Xvfb + VNC + noVNC |
| Game Runtime (v2) | pygbag / WebAssembly |
| Auth | Email+password, Argon2id, HttpOnly session cookies |
| CI/CD | GitHub Actions |
| Testing | pytest + Playwright |

---

## Timeline (Solo Developer)

| Phase | Duration | Status |
|-------|----------|--------|
| 1. Foundation | 2 weeks | ✅ Complete |
| 2. Auth & Users | 3 weeks | ✅ Complete (reset deferred to pre-beta) |
| 3. Dashboard & Pages | 2 weeks | ✅ Complete |
| 4. Game CRUD & Generation | 3 weeks | ✅ Core complete (WS + LLM deferred) |
| 5. Validation & Artifacts | 2 weeks | ✅ Core complete (artifact storage deferred) |
| 6. Cloud Play (noVNC) | 5-7 weeks | ✅ Complete (E2E deferred to Phase 11) |
| 7. Game Editor | 2 weeks | ✅ Complete (diff viewer deferred) |
| 8. Public Arcade | 2 weeks | ✅ Complete |
| 9. Sharing | 1 week | ✅ Complete |
| 10. Security Hardening | 2-3 weeks | ✅ Core complete (audit+privacy deferred) |
| 11. Testing & CI/CD | 2-3 weeks | ✅ Complete (Playwright deferred) |
| 12. Production Launch | 1-2 weeks | ✅ Complete |
| 13. Cloud Deployment | 1 week | [~] In progress |
| **Total** | **~28-35 weeks** | |
