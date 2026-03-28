#!/usr/bin/env bash
# ArcadeForge — Session Stop Hook
# Persists session state to .estado.md for the next session.
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ESTADO_FILE=".estado.md"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo ""
echo "[stop hook] Saving session state to $ESTADO_FILE..."

SUMMARY="${CLAUDE_STOP_HOOK_SUMMARY:-Session ended at $TIMESTAMP. No summary provided.}"

ENTRY="## Session: $TIMESTAMP

$SUMMARY

---
"

if [ -f "$ESTADO_FILE" ]; then
  EXISTING=$(cat "$ESTADO_FILE")
  printf '%s\n%s' "$ENTRY" "$EXISTING" > "$ESTADO_FILE"
else
  printf '# Session State Log\n\n%s' "$ENTRY" > "$ESTADO_FILE"
fi

echo -e "${GREEN}Session state saved to $ESTADO_FILE${NC}"

# Stage the state file if in a git repo
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  if git diff --name-only "$ESTADO_FILE" 2>/dev/null | grep -q "$ESTADO_FILE" || \
     ! git ls-files --error-unmatch "$ESTADO_FILE" &>/dev/null 2>&1; then
    git add "$ESTADO_FILE" 2>/dev/null || true
    echo -e "${YELLOW}Staged $ESTADO_FILE (not committed)${NC}"
  fi
fi

echo ""
