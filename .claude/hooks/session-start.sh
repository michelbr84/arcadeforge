#!/usr/bin/env bash
# ArcadeForge — Session Start Hook
# Orients Claude with project context before any work begins.
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  ArcadeForge — AI Engineering Team${NC}"
echo -e "${BLUE}============================================${NC}"

# Date and time
echo ""
echo -e "Date: $(date '+%Y-%m-%d %H:%M:%S')"

# Git context
if git rev-parse --is-inside-work-tree &>/dev/null; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  echo -e "Branch: ${GREEN}${BRANCH}${NC}"
  echo ""
  echo "Recent commits:"
  git log --oneline -5 2>/dev/null | sed 's/^/  /' || echo "  (no commits yet)"
else
  echo -e "${YELLOW}Not inside a git repository.${NC}"
fi

# Session state file
echo ""
if [ -f ".estado.md" ]; then
  echo -e "${GREEN}Previous session state found (.estado.md):${NC}"
  echo "---"
  head -30 .estado.md
  echo "---"
else
  echo "No previous session state. Starting fresh."
fi

# Environment check
echo ""
if [ -f ".env" ]; then
  echo -e "${GREEN}.env file found.${NC}"
  if grep -q "your_token_here\|changeme\|REPLACE_ME" .env 2>/dev/null; then
    echo -e "${YELLOW}Warning: .env has unfilled placeholder values.${NC}"
  fi
else
  echo -e "${YELLOW}Warning: .env not found. Copy from .env.example${NC}"
fi

# Available skills
echo ""
echo "Available skills:"
if [ -d "skills" ]; then
  for f in skills/*.md; do
    name=$(basename "$f" .md)
    echo "  /$name"
  done
else
  echo "  (skills/ directory not found)"
fi

# Available agents
echo ""
echo "Available agents:"
if [ -d ".claude/agents" ]; then
  for f in .claude/agents/*.md; do
    name=$(basename "$f" .md)
    echo "  $name"
  done
fi

# Auto Dream — background memory consolidation
if [ -f "scripts/auto-dream.sh" ]; then
  bash scripts/auto-dream.sh &>/dev/null &
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo ""
