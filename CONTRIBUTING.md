# Contributing to ArcadeForge

Thank you for your interest in contributing to ArcadeForge!

## Getting Started

### Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.12+
- Docker Desktop

### Setup

```bash
git clone https://github.com/michelbr84/arcadeforge.git
cd arcadeforge
pnpm install
docker compose -f infra/docker-compose.yml up -d
cd apps/api && python -m alembic upgrade head
bash scripts/dev.sh
```

### Running Tests

```bash
# All tests
cd apps/api && python -m pytest tests/ -v

# Unit tests only (no DB)
python -m pytest tests/test_auth_passwords.py tests/test_generator.py tests/test_scanner.py

# Frontend build
pnpm --filter @arcadeforge/web build
```

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `refactor:` — code refactoring
- `test:` — adding tests
- `chore:` — maintenance

## Code Style

- **Python**: PEP 8, type hints, async/await for DB operations
- **TypeScript**: strict mode, no `any`, prefer `const`
- **CSS**: TailwindCSS utility classes

## Security

If you find a security vulnerability, please see [SECURITY.md](SECURITY.md).
Do NOT open a public issue for security problems.

## Adding a New Game Genre

1. Add the genre to `apps/api/app/games/genres.py`
2. Add a template to `apps/api/app/games/generator.py`
3. Add difficulty presets
4. Write tests
5. Update the frontend genre list

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
