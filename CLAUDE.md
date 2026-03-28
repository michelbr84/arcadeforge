# ArcadeForge — Project Instructions

> Generate. Play. Share. AI-powered browser arcade.

## Project Overview

ArcadeForge is a multi-tenant SaaS platform where users generate games with AI, play them in-browser, edit/remix, and share publicly. Built on top of the [infinity-arcade](https://github.com/michelbr84/infinity-arcade) game generation engine.

## Tech Stack (Locked)

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 + React 19 + TailwindCSS v4 + Zustand |
| Backend | FastAPI + Pydantic Settings + SQLAlchemy (async) |
| Database | PostgreSQL 16 + Alembic migrations |
| Queue | arq (async Redis queue) — NOT RQ, NOT Celery |
| Cache/Sessions | Redis 7 |
| Object Storage | MinIO (dev) / S3 (prod) |
| Game Runtime v1 | Sandbox container + Xvfb + VNC + noVNC |
| Game Runtime v2 | pygbag / WebAssembly (future) |
| Auth | Email+password, Argon2id, HttpOnly session cookies |
| Testing | pytest (API) + Playwright (E2E) |

## Repository Structure

```
arcadeforge/
├── apps/web/          # Next.js 15 frontend (English-only UI)
├── apps/api/          # FastAPI backend
│   └── app/
│       ├── auth/      # Authentication (Argon2id, sessions)
│       ├── db/        # SQLAlchemy models + Alembic migrations
│       ├── games/     # Game CRUD, generation, sandbox
│       ├── jobs/      # arq queue client
│       └── pages/     # User pages
├── workers/           # arq worker processes
│   ├── generator/     # Game generation worker
│   ├── validator/     # Validation + smoke check worker
│   └── sandbox/       # Sandbox lifecycle worker
├── packages/shared/   # Shared TypeScript types
├── packages/ui/       # Shared React components
├── services/          # Sandbox runtime + nginx
├── infra/             # Docker Compose
├── data/              # Local storage (workspaces, artifacts, sandboxes, validation)
├── skills/            # Reusable AI workflow skills
├── workflows/         # Headless automation scripts (batch-fix, parallel-review, etc.)
└── .claude/           # Hooks, agents, settings
    ├── hooks/         # session-start, pre-tool-use, post-tool-use, stop
    └── agents/        # team-coordinator, code-reviewer, security-auditor, doc-writer
```

## Conventions

### Code Style
- **Python**: PEP 8, type hints required, async/await for all DB/Redis operations
- **TypeScript**: strict mode, no `any` types, prefer `const` over `let`
- **SQL**: Alembic migrations for all schema changes, never raw SQL in application code
- **CSS**: TailwindCSS utility classes, no custom CSS unless absolutely necessary

### Git
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`
- Never push directly to `main` without verification
- Never commit `.env`, credentials, or secrets
- Co-author line: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`

### Security (Critical)
- All user input validated via Pydantic schemas
- Passwords hashed with Argon2id (never bcrypt, never plaintext)
- Sessions: HttpOnly + Secure + SameSite=Lax cookies (never JWT in localStorage)
- Game code execution: always in isolated sandbox container, never on main server
- Code scanner must check generated code before sandbox execution
- Rate limiting on all public endpoints

### Testing
- API tests: `cd apps/api && pytest`
- Frontend: `cd apps/web && pnpm test` (when configured)
- E2E: Playwright (when configured)
- Always fix code to pass tests, never modify tests to pass code

### UI Language
- All user-facing text must be in **English**
- Routes, labels, emails, error messages: English only

## Available Skills

Invoke with `/skill-name [arguments]`:

| Skill | Purpose |
|-------|---------|
| `/assemble-team --mode <mode> --goals "<goals>"` | Assemble a coordinated agent team for any task |
| `/fix-issue --issue <number>` | Read GitHub issue → write tests → fix → open PR |
| `/tdd-loop --spec "<description>"` | TDD cycle: write failing tests → implement → iterate |
| `/pre-commit` | Scan staged files for secrets, debug code, lint issues |
| `/review-pr --pr <number>` | Structured code review with security + test checks |
| `/refactor-module --file <path> --goal "<goal>"` | Safe refactor with test baseline verification |
| `/generate-docs --dir <path>` | Auto-generate API docs from source code |

## Available Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `team-coordinator` | opus | Orchestrates agent teams — spawns, coordinates, synthesizes |
| `code-reviewer` | sonnet | Strict code review: correctness, security, conventions |
| `security-auditor` | sonnet | OWASP-focused security scan of codebase |
| `doc-writer` | sonnet | Documentation generation — README, API docs, guides |

## Workflows (Headless Automation)

Shell scripts in `workflows/` for batch operations using Claude headless mode:

| Script | Usage |
|--------|-------|
| `batch-fix.sh` | Fix multiple GitHub issues: `./workflows/batch-fix.sh owner/repo 10 11 12` |
| `parallel-review.sh` | Writer/Reviewer pattern: `./workflows/parallel-review.sh --feature branch --task "desc"` |
| `mass-refactor.sh` | Batch refactor: `./workflows/mass-refactor.sh --pattern "old_fn" --goal "rename"` |
| `dependency-graph.sh` | Generate dependency graph: `./workflows/dependency-graph.sh --dir apps/api/app` |

## Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` | Session opens | Shows git context, session state, available skills/agents |
| `pre-tool-use.sh` | Before Bash | Blocks dangerous commands, logs to audit.log |
| `post-tool-use.sh` | After Edit/Write | Auto-runs tests for changed source files |
| `stop.sh` | Session ends | Saves session state to `.estado.md` |

## Infrastructure

### Local Development
- **Dev**: `docker compose -f infra/docker-compose.yml up -d` (Postgres, Redis, MinIO)
- **API**: `cd apps/api && uvicorn app.main:app --reload --port 8000`
- **Web**: `pnpm dev:web` (port 3000)
- **All at once**: `bash scripts/dev.sh`

### Cloud (Production)
| Service | Platform | Config |
|---------|----------|--------|
| Frontend | Vercel | `apps/web/vercel.json` |
| API | Fly.io | `apps/api/fly.toml` + `Dockerfile.cloud` |
| Workers | Fly.io | `workers/fly.toml` + `Dockerfile.cloud` |
| Sandbox | Fly.io Machines | `services/sandbox-runtime/fly.toml` |
| Database | Fly Postgres | Internal networking (flycast) |
| Redis | Upstash | TLS via `rediss://` URL |
| CI/CD | GitHub Actions | `.github/workflows/deploy.yml` |

- **Deploy API**: `cd apps/api && fly deploy --remote-only`
- **Deploy Workers**: `cd workers && fly deploy --remote-only` (from repo root)
- **Env vars**: `.env.cloud.example` documents all cloud env vars

## Key Files

- `ROADMAP.md` — Phase-by-phase delivery plan with checkboxes
- `.env.example` — All environment variables (local dev)
- `.env.cloud.example` — All environment variables (cloud deployment)
- `apps/api/app/db/models.py` — Database models (7 tables)
- `apps/api/app/config.py` — Pydantic settings configuration
- `apps/api/app/storage.py` — S3/local storage abstraction
- `apps/api/app/games/sandbox_fly.py` — Fly.io Machines sandbox driver
- `workers/shared_settings.py` — Shared arq Redis settings
