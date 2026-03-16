#!/usr/bin/env bash
# ArcadeForge — Post-tool-use hook
# Runs relevant tests after file edits to catch regressions early.
set -euo pipefail

FILE="${CLAUDE_TOOL_OUTPUT_FILE_PATH:-}"
TOOL="${CLAUDE_TOOL_NAME:-unknown}"

# Only run after Edit or Write tools
if [ "$TOOL" != "Edit" ] && [ "$TOOL" != "Write" ]; then
    exit 0
fi

# Skip non-source files
case "$FILE" in
    *.md|*.txt|*.json|*.yaml|*.yml|*.toml|*.ini|*.cfg|*.gitkeep|*.env*|*.lock)
        exit 0
        ;;
esac

# === Python files ===
if [[ "$FILE" == *.py ]]; then
    # Find test directory (search up 3 levels)
    DIR=$(dirname "$FILE")
    TEST_DIR=""
    for i in 1 2 3; do
        if [ -d "$DIR/tests" ]; then
            TEST_DIR="$DIR/tests"
            break
        fi
        DIR=$(dirname "$DIR")
    done

    if [ -n "$TEST_DIR" ]; then
        echo "🧪 Running tests in $TEST_DIR..." >&2
        if cd "$DIR" && python -m pytest "$TEST_DIR" -q --tb=short 2>&1; then
            echo "✅ Tests passed" >&2
        else
            echo "❌ Tests FAILED — fix the failing tests before proceeding" >&2
        fi
    fi
fi

# === TypeScript/JavaScript files ===
if [[ "$FILE" == *.ts ]] || [[ "$FILE" == *.tsx ]] || [[ "$FILE" == *.js ]] || [[ "$FILE" == *.jsx ]]; then
    # Find nearest package.json (search up 3 levels)
    DIR=$(dirname "$FILE")
    PKG_DIR=""
    for i in 1 2 3; do
        if [ -f "$DIR/package.json" ]; then
            PKG_DIR="$DIR"
            break
        fi
        DIR=$(dirname "$DIR")
    done

    if [ -n "$PKG_DIR" ]; then
        # Only run if test script exists
        if cd "$PKG_DIR" && grep -q '"test"' package.json 2>/dev/null; then
            echo "🧪 Running tests in $PKG_DIR..." >&2
            if pnpm test --if-present 2>&1; then
                echo "✅ Tests passed" >&2
            else
                echo "❌ Tests FAILED — fix the failing tests before proceeding" >&2
            fi
        fi
    fi
fi

exit 0
