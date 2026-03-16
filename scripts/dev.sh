#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  ArcadeForge — Development Environment"
echo "========================================="

# 1. Start infrastructure services
echo ""
echo "[1/5] Starting infrastructure (Postgres, Redis, MinIO)..."
docker compose -f "$ROOT_DIR/infra/docker-compose.yml" up -d

echo ""
echo "[2/5] Waiting for services to be healthy..."
sleep 3

until docker exec arcadeforge-db pg_isready -U postgres > /dev/null 2>&1; do
    echo "  Waiting for Postgres..."
    sleep 1
done
echo "  Postgres: ready"

until docker exec arcadeforge-redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 1
done
echo "  Redis: ready"

# 2. Ensure test database exists (so pytest doesn't destroy dev data)
echo ""
echo "[3/5] Ensuring databases..."
docker exec arcadeforge-db psql -U postgres -c "CREATE DATABASE arcadeforge_test;" 2>/dev/null || true

# Run migrations on dev database
cd "$ROOT_DIR/apps/api"
python -m alembic upgrade head 2>&1 | grep -E "Running upgrade|already" || true
echo "  Migrations: up to date"

# 3. Kill any leftover processes on our ports
echo ""
echo "[4/5] Cleaning up old processes..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "arq workers" 2>/dev/null || true
sleep 1

# 4. Start all services
echo ""
echo "[5/5] Starting all services..."
echo ""

trap 'echo ""; echo "Shutting down..."; kill 0' EXIT

# API server
cd "$ROOT_DIR/apps/api" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
sleep 2

# Generator worker (processes game creation jobs)
cd "$ROOT_DIR" && PYTHONDONTWRITEBYTECODE=1 python -B -m arq workers.generator.worker.WorkerSettings &
sleep 1

# Sandbox worker (processes play session jobs)
cd "$ROOT_DIR" && PYTHONDONTWRITEBYTECODE=1 python -B -m arq workers.sandbox.worker.WorkerSettings &
sleep 1

# Web frontend
cd "$ROOT_DIR" && pnpm dev:web &

echo ""
echo "========================================="
echo "  All services running:"
echo "  Web:       http://localhost:3000"
echo "  API Docs:  http://localhost:8000/api/docs"
echo "  MinIO:     http://localhost:9001"
echo ""
echo "  Workers:   generator + sandbox (auto-processing)"
echo "  Press Ctrl+C to stop all services"
echo "========================================="
echo ""

wait
