# ArcadeForge

**Generate. Play. Share. AI-powered browser arcade.**

ArcadeForge is an open-source platform where users generate games with AI, play them instantly in the browser, edit the code, and share with the world.

---

## Features

- **AI Game Generation** — Describe your game, pick a genre, and get playable Pygame code via LLM (OpenAI, Anthropic, or OpenRouter)
- **Browser Gameplay** — Games run in secure sandbox containers via noVNC — no downloads, no installs
- **Monaco Code Editor** — Edit game code with full syntax highlighting, save new versions, auto-validate
- **Code Scanner** — 25+ pattern denylist catches dangerous code before sandbox execution
- **Validation Pipeline** — Automated smoke checks verify game structure, loop, and display
- **Public Arcade** — Browse, search, and filter community games by genre and popularity
- **Share & Embed** — Share links with Open Graph previews, embed games on any website via iframe
- **Fork & Remix** — Fork any public game into your library and make it your own
- **Secure Auth** — Argon2id password hashing, server-side sessions, rate limiting, password reset
- **Bring Your Own LLM** — Connect OpenAI, Anthropic, or OpenRouter API keys in account settings

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 · React 19 · TailwindCSS v4 · Zustand · Monaco Editor |
| Backend | FastAPI · Pydantic · SQLAlchemy (async) · Alembic |
| Database | PostgreSQL 16 |
| Queue | arq (async Redis queue) |
| Cache/Sessions | Redis 7 |
| Game Runtime | Docker · Xvfb · x11vnc · websockify · noVNC · pygame-ce |
| CI/CD | GitHub Actions (3 workflows) |
| Testing | pytest (95 tests) |

## Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 20+
- [pnpm](https://pnpm.io/) 9+
- [Python](https://www.python.org/) 3.12+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Clone and install

```bash
git clone https://github.com/michelbr84/arcadeforge.git
cd arcadeforge
pnpm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set APP_SECRET_KEY to a random string
```

### 3. Start infrastructure

```bash
docker compose -f infra/docker-compose.yml up -d
```

This starts PostgreSQL, Redis, and MinIO.

### 4. Run database migrations

```bash
cd apps/api
python -m alembic upgrade head
```

### 5. Build the sandbox image

```bash
docker build -t arcadeforge-sandbox:latest services/sandbox-runtime/
```

### 6. Start development servers

```bash
bash scripts/dev.sh
```

Or start them separately:

```bash
# Terminal 1 — API
cd apps/api && uvicorn app.main:app --reload --port 8000

# Terminal 2 — Web
pnpm dev:web
```

### 7. Open the app

- **Web:** http://localhost:3000
- **API Docs:** http://localhost:8000/api/docs
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

## Project Structure

```
arcadeforge/
├── apps/
│   ├── web/                    # Next.js 15 frontend
│   │   ├── src/app/            # App Router pages (11 routes)
│   │   ├── src/components/     # React components
│   │   ├── src/lib/            # API client
│   │   └── src/stores/         # Zustand stores
│   │
│   └── api/                    # FastAPI backend
│       ├── app/
│       │   ├── auth/           # Auth: passwords, sessions, rate limiting, reset
│       │   ├── db/             # Models, migrations, session factory
│       │   ├── games/          # CRUD, generator, scanner, sandbox, validation
│       │   ├── jobs/           # arq queue client
│       │   └── pages/          # User profile routes
│       └── tests/              # 95 pytest tests
│
├── workers/                    # arq background workers
│   ├── generator/              # Game code generation
│   ├── validator/              # Smoke checks + validation
│   └── sandbox/                # Container lifecycle management
│
├── services/
│   ├── sandbox-runtime/        # Docker image: Xvfb + VNC + noVNC + pygame
│   └── reverse-proxy/          # Nginx configs (dev + prod)
│
├── packages/
│   ├── shared/                 # Shared TypeScript types
│   └── ui/                     # Shared React components
│
├── infra/                      # Docker Compose (dev + prod)
├── scripts/                    # dev.sh, backup-db.sh
├── skills/                     # Claude Code skills
└── .github/workflows/          # CI, nightly eval, Docker build
```

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Sign in (sets session cookie) |
| POST | `/api/auth/logout` | Sign out |
| GET | `/api/auth/me` | Current user |
| PATCH | `/api/auth/me` | Update username or password |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Confirm reset with token |

### Games
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/games/genres` | List game genres |
| POST | `/api/games` | Create game (202 — async generation) |
| GET | `/api/games` | List my games |
| GET | `/api/games/:id` | Game detail |
| GET | `/api/games/:id/status` | Generation status |
| DELETE | `/api/games/:id` | Delete game (owner only) |
| GET | `/api/games/:id/versions` | Version history |
| POST | `/api/games/:id/versions` | Save new version |
| POST | `/api/games/:id/fork` | Fork a public game |

### Validation
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/games/:id/validate` | Run validation |
| POST | `/api/games/:id/scan` | Run code scanner |
| GET | `/api/games/:id/validations` | List validation runs |

### Play
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/games/:id/play` | Start play session (202) |
| GET | `/api/games/:id/play/:sessionId` | Session status + ws_url |
| POST | `/api/games/:id/play/:sessionId/stop` | Stop session |

### Public
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/arcade/games` | Public game listing (search, filter, sort) |
| GET | `/api/users/:username` | Public user profile |
| GET | `/api/health` | Health check |

## Running Tests

```bash
cd apps/api

# All tests (requires Postgres + Redis running)
python -m pytest tests/ -v

# Unit tests only (no database needed)
python -m pytest tests/test_auth_passwords.py tests/test_generator.py tests/test_scanner.py -v

# Specific test file
python -m pytest tests/test_auth_flow.py -v
```

## Security

ArcadeForge executes user-generated code. The security model includes:

- **Sandbox isolation** — Games run in Docker containers with no network, CPU/memory limits, read-only filesystem, non-root user, and seccomp profiles
- **Code scanning** — All game code is scanned for dangerous patterns before execution
- **Auth security** — Argon2id hashing, server-side sessions (256-bit IDs), HttpOnly cookies, session rotation on login
- **Rate limiting** — Redis-backed limits on auth, play, and guest endpoints
- **Password reset** — SHA-256 hashed tokens, 30-minute TTL, single-use, all sessions invalidated

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## CI/CD

Three GitHub Actions workflows:

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `ci-web.yml` | PR + push to main | Web build, API unit tests, integration tests with Postgres + Redis |
| `nightly-eval.yml` | Daily 03:00 UTC | Full test suite + game generation eval (4 genres x 3 difficulties) |
| `docker-build.yml` | Sandbox changes | Buildx with SBOM, provenance, and smoke test |

## Cloud Deployment

ArcadeForge runs entirely in the cloud — no local servers needed.

| Component | Service | URL |
|-----------|---------|-----|
| Frontend | Vercel | [arcadeforge-web.vercel.app](https://arcadeforge-web.vercel.app) |
| API | Fly.io | [arcadeforge-api.fly.dev](https://arcadeforge-api.fly.dev) |
| Database | Fly Postgres | Internal (flycast) |
| Redis | Upstash | TLS connection |
| Workers | Fly.io | 3 processes (generator, validator, sandbox) |
| Sandbox | Fly.io Machines | On-demand containers |

### Deploy from scratch

```bash
# 1. Install Fly CLI
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login

# 2. Create apps
fly apps create arcadeforge-api
fly apps create arcadeforge-workers
fly apps create arcadeforge-sandbox

# 3. Create Postgres
fly postgres create --name arcadeforge-db --region iad --vm-size shared-cpu-1x

# 4. Set secrets (see .env.cloud.example for all vars)
fly secrets set -a arcadeforge-api APP_ENV=production DATABASE_URL="..." REDIS_URL="..." ...

# 5. Deploy API
cd apps/api && fly deploy --remote-only

# 6. Run migrations
fly ssh console -a arcadeforge-api -C "sh -c 'cd /app && alembic upgrade head'"

# 7. Deploy workers
cd workers && fly deploy --remote-only

# 8. Connect Vercel
# Import repo at vercel.com/new, set root dir to apps/web
# Add env var: API_URL=https://arcadeforge-api.fly.dev
```

See `.env.cloud.example` for all required environment variables.

### Self-hosted (Docker Compose)

```bash
cp .env.example .env
# Edit .env with production values

docker compose -f infra/docker-compose.prod.yml up -d
docker compose exec api python -m alembic upgrade head
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## License

MIT
