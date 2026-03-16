# ArcadeForge — Project Roadmap

> Last updated: 2026-03-16

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
- [ ] 1.12 `docker compose up` boots all services cleanly (requires Docker Desktop)

### Commit 3: `feat: initialize FastAPI config and Alembic baseline`

- [x] 1.13 pydantic-settings config loader (`apps/api/app/config.py`)
- [x] 1.14 SQLAlchemy async engine + session setup
- [x] 1.15 Alembic init + first migration (7 tables: users, sessions, user_pages, games, game_versions, validation_runs, play_sessions)
- [x] 1.16 arq workers wired to Redis config (`workers/shared_settings.py`)
- [x] 1.17 API health endpoint with lifespan hooks (`GET /api/health`)

---

## Phase 2 — Authentication & User System

**Goal:** Secure email+password registration and login with HttpOnly session cookies.

- [ ] 2.1 Argon2id password hashing (`apps/api/app/auth/passwords.py`)
- [ ] 2.2 `POST /api/auth/register` endpoint
- [ ] 2.3 `POST /api/auth/login` → HttpOnly cookie session
- [ ] 2.4 `POST /api/auth/logout` → invalidate session
- [ ] 2.5 Session middleware + session ID rotation
- [ ] 2.6 CSRF protection (SameSite=Lax + token)
- [ ] 2.7 Rate limiting on auth endpoints
- [ ] 2.8 Email verification flow (optional, behind env flag)
- [ ] 2.9 Password reset flow (secure token, 30min TTL)
- [ ] 2.10 Frontend: `/auth/login`, `/auth/register`, `/auth/forgot-password`

---

## Phase 3 — Dashboard & Personal Pages

**Goal:** Authenticated users see dashboard and have a public profile page.

- [ ] 3.1 `/dashboard` page (My Games grid, Create Game CTA)
- [ ] 3.2 `/@username` public profile page
- [ ] 3.3 `/settings` page (update email, username, password)
- [ ] 3.4 Navbar with auth state
- [ ] 3.5 API: `GET /api/me`, `PATCH /api/me`, `GET /api/users/:username`

---

## Phase 4 — Game CRUD & AI Generation

**Goal:** Users create games via prompt+genre, stored with versioning.

- [ ] 4.1 Genre catalog API (`GET /api/genres`)
- [ ] 4.2 Create game form (genre selector, prompt, params)
- [ ] 4.3 `POST /api/games` → enqueue to arq generator worker
- [ ] 4.4 Generator worker: calls genre_forge, saves to `/data/workspaces/`
- [ ] 4.5 Game version v0 created automatically
- [ ] 4.6 LLM-assist mode (optional, behind `LLM_MODE` env)
- [ ] 4.7 Game detail page `/games/:id` (Overview + Code tabs)
- [ ] 4.8 Version history API
- [ ] 4.9 Real-time generation progress (WebSocket/SSE)
- [ ] 4.10 Async-compatible game loop (WASM-ready from day 1)

---

## Phase 5 — Validation & Artifacts

**Goal:** Automated game validation with reports, screenshots, and artifacts.

- [ ] 5.1 `POST /api/games/:id/validate` → enqueue to arq validator worker
- [ ] 5.2 Static code scanner (denylist → evolve to allowlist)
- [ ] 5.3 Validator worker: SmokeChecker + GameRunner headless
- [ ] 5.4 Artifact storage (local + S3/MinIO driver)
- [ ] 5.5 Validation tab on game page (report + screenshot)
- [ ] 5.6 Auto-validate after generation

---

## Phase 6 — Cloud Play (noVNC Sandbox) ⚠️ HARDEST PHASE

**Goal:** Users play games in-browser via server-side sandbox container.

- [ ] 6.1 Sandbox Docker image (Xvfb + VNC + websockify + pygame)
- [ ] 6.2 `POST /api/games/:id/play` → enqueue to arq sandbox worker
- [ ] 6.3 Sandbox worker: spin up container, return ws_url
- [ ] 6.4 `GamePlayerNoVNC.tsx` — noVNC embed component
- [ ] 6.5 Session lifecycle (TTL, auto-cleanup, kill switch)
- [ ] 6.6 Resource limits (CPU, memory, no network)
- [ ] 6.7 Security: seccomp, apparmor, non-root, read-only FS
- [ ] 6.8 Increment `play_count` on session start
- [ ] 6.9 Nginx WebSocket proxy for `/play/ws/*`

---

## Phase 7 — Game Editor (2 weeks)

- [ ] 7.1 Monaco Editor component
- [ ] 7.2 Save as new version
- [ ] 7.3 Version diff viewer
- [ ] 7.4 Re-validate on save

---

## Phase 8 — Public Arcade (2 weeks)

- [ ] 8.1 `/arcade` public game listing with thumbnails
- [ ] 8.2 Search + filter by genre, title
- [ ] 8.3 Trending sort by `play_count`
- [ ] 8.4 Guest play (rate limited)

---

## Phase 9 — Sharing & Social (1 week)

- [ ] 9.1 Open Graph meta tags for social preview
- [ ] 9.2 Embed `<iframe>` snippet generator
- [ ] 9.3 Remix/Fork public games
- [ ] 9.4 Copy share link

---

## Phase 10 — Security Hardening (2-3 weeks)

- [ ] 10.1 Input sanitization (strict Pydantic schemas)
- [ ] 10.2 Rate limiting across all endpoints
- [ ] 10.3 Audit logging
- [ ] 10.4 Account security (lockout, session listing)
- [ ] 10.5 Privacy (data export, account deletion)
- [ ] 10.6 `SECURITY.md`
- [ ] 10.7 Dependency scanning in CI

---

## Phase 11 — Testing & CI/CD (2-3 weeks)

- [ ] 11.1 Unit tests (API): pytest
- [ ] 11.2 Integration tests: docker compose + pytest
- [ ] 11.3 E2E tests: Playwright (signup → create → validate → play)
- [ ] 11.4 `ci-web.yml` pipeline
- [ ] 11.5 `nightly-eval.yml` pipeline
- [ ] 11.6 Reproducible Docker deploy

---

## Phase 12 — Production Launch (1-2 weeks)

- [ ] 12.1 Domain + SSL
- [ ] 12.2 Monitoring (Sentry + metrics)
- [ ] 12.3 CDN for static assets
- [ ] 12.4 Database backups
- [ ] 12.5 Landing page (n8n-style, auto-signup modal)
- [ ] 12.6 `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`

---

## Phase 13 — WASM Runtime / pygbag (Future)

- [ ] 13.1 pygbag integration (compile pygame → HTML+WASM)
- [ ] 13.2 WASM build worker
- [ ] 13.3 CDN hosting for WASM builds
- [ ] 13.4 Fallback to noVNC for incompatible games

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
| 1. Foundation | 2 weeks | 🔵 In Progress |
| 2. Auth & Users | 3 weeks | ⚪ Not Started |
| 3. Dashboard & Pages | 2 weeks | ⚪ Not Started |
| 4. Game CRUD & Generation | 3 weeks | ⚪ Not Started |
| 5. Validation & Artifacts | 2 weeks | ⚪ Not Started |
| 6. Cloud Play (noVNC) | 5-7 weeks | ⚪ Not Started |
| 7. Game Editor | 2 weeks | ⚪ Not Started |
| 8. Public Arcade | 2 weeks | ⚪ Not Started |
| 9. Sharing | 1 week | ⚪ Not Started |
| 10. Security Hardening | 2-3 weeks | ⚪ Not Started |
| 11. Testing & CI/CD | 2-3 weeks | ⚪ Not Started |
| 12. Production Launch | 1-2 weeks | ⚪ Not Started |
| **Total** | **~27-34 weeks** | |
