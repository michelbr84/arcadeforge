#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  ArcadeForge — Development Environment"
echo "========================================="

# 1. Start infrastructure services
echo ""
echo "[1/3] Starting infrastructure (Postgres, Redis, MinIO)..."
docker compose -f "$ROOT_DIR/infra/docker-compose.yml" up -d

echo ""
echo "[2/3] Waiting for services to be healthy..."
sleep 3

# Check postgres
until docker exec arcadeforge-db pg_isready -U postgres > /dev/null 2>&1; do
    echo "  Waiting for Postgres..."
    sleep 1
done
echo "  Postgres: ready"

# Check redis
until docker exec arcadeforge-redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 1
done
echo "  Redis: ready"

echo "  MinIO: http://localhost:9001 (minioadmin/minioadmin)"

# 2. Start API and Web in parallel
echo ""
echo "[3/3] Starting applications..."
echo "  API:  http://localhost:8000/api/docs"
echo "  Web:  http://localhost:3000"
echo ""

# Run API and Web in parallel, kill both on exit
trap 'kill 0' EXIT

cd "$ROOT_DIR/apps/api" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
cd "$ROOT_DIR" && pnpm dev:web &

wait
