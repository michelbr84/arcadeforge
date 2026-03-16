#!/usr/bin/env bash
# ArcadeForge — Database Backup Script
#
# Creates a compressed PostgreSQL backup using pg_dump custom format.
# Custom format (-Fc) is recommended because:
# - Works with pg_restore for selective/parallel restore
# - Compressed by default
# - Supports reordering during restore
#
# Usage: bash scripts/backup-db.sh
# Requires: docker (for containerized DB) or pg_dump (for direct access)
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/arcadeforge_${TIMESTAMP}.dump"

# DB connection (from env or defaults)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-arcadeforge}"
DB_USER="${POSTGRES_USER:-postgres}"

mkdir -p "$BACKUP_DIR"

echo "=== ArcadeForge Database Backup ==="
echo "Timestamp: $TIMESTAMP"
echo "Database: $DB_NAME"
echo "Output: $BACKUP_FILE"

# Try docker first, then local pg_dump
if docker exec arcadeforge-db pg_isready -U "$DB_USER" > /dev/null 2>&1; then
    echo "Using Docker container..."
    docker exec arcadeforge-db pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -Fc \
        --no-owner \
        --no-privileges \
        > "$BACKUP_FILE"
elif command -v pg_dump > /dev/null 2>&1; then
    echo "Using local pg_dump..."
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -Fc \
        --no-owner \
        --no-privileges \
        > "$BACKUP_FILE"
else
    echo "ERROR: No pg_dump available (neither Docker nor local)"
    exit 1
fi

SIZE=$(wc -c < "$BACKUP_FILE")
echo "Backup complete: $BACKUP_FILE ($SIZE bytes)"

# Cleanup: keep last 7 backups
echo "Cleaning old backups (keeping last 7)..."
ls -t "$BACKUP_DIR"/arcadeforge_*.dump 2>/dev/null | tail -n +8 | xargs -r rm
echo "Done."
