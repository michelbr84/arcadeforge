#!/usr/bin/env bash
# ArcadeForge — Pre-tool-use safety hook
# Blocks dangerous commands and logs all tool usage.
set -euo pipefail

CMD="${CLAUDE_TOOL_INPUT_COMMAND:-}"
TOOL="${CLAUDE_TOOL_NAME:-unknown}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE=".claude/audit.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log every command
echo "[$TIMESTAMP] TOOL=$TOOL CMD=$CMD" >> "$LOG_FILE"

# Only check Bash commands
if [ "$TOOL" != "Bash" ]; then
    exit 0
fi

# === BLOCK LIST (dangerous patterns) ===

BLOCKED_PATTERNS=(
    "rm -rf /"
    "rm -rf ~"
    "rm -rf \."
    "mkfs\."
    "dd if=/dev/zero"
    ":(){ :|:& };:"
    "DROP TABLE"
    "DROP DATABASE"
    "git push.*--force.*main"
    "git push.*--force.*master"
    "git push.*-f.*main"
    "git push.*-f.*master"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$CMD" | grep -qiE "$pattern"; then
        echo "🛑 BLOCKED: Command matches dangerous pattern: $pattern" >&2
        echo "[$TIMESTAMP] BLOCKED: $CMD (pattern: $pattern)" >> "$LOG_FILE"
        exit 1
    fi
done

# === WARNING LIST (review-worthy patterns) ===

WARNING_PATTERNS=(
    "pip install"
    "npm install -g"
    "curl.*|.*sh"
    "wget.*|.*sh"
)

for pattern in "${WARNING_PATTERNS[@]}"; do
    if echo "$CMD" | grep -qiE "$pattern"; then
        echo "⚠️  WARNING: $CMD (pattern: $pattern)" >&2
        echo "[$TIMESTAMP] WARNING: $CMD (pattern: $pattern)" >> "$LOG_FILE"
    fi
done

# === SECRET DETECTION ===

SECRET_PATTERNS=(
    "echo.*API_KEY"
    "echo.*SECRET"
    "echo.*PASSWORD"
    "echo.*TOKEN"
    "export.*API_KEY=sk-"
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    if echo "$CMD" | grep -qiE "$pattern"; then
        echo "⚠️  WARNING: Command may expose secrets: $pattern" >&2
        echo "[$TIMESTAMP] SECRET_WARNING: $CMD" >> "$LOG_FILE"
    fi
done

# All clear
exit 0
