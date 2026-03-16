---
name: pre-commit
description: "Scan staged files for secrets, debug code, security issues, and lint problems before committing."
tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Pre-Commit Skill

Intelligent pre-commit verification for ArcadeForge.

## Workflow

### Step 1: Inspect staged changes

```bash
git diff --cached --name-only
git diff --cached --stat
```

List all staged files and their change summary.

### Step 2: Secret detection (BLOCKING)

Scan staged diffs for patterns that suggest credentials:

```bash
git diff --cached -U0
```

Look for:
- `api_key`, `API_KEY`, `apikey`
- `secret`, `SECRET`
- `password` (not `password_hash`)
- `token` (not in variable names like `token_ttl`)
- `ANTHROPIC_API_KEY=sk-...`
- `OPENAI_API_KEY=sk-...`
- `DATABASE_URL=postgresql://...` with real credentials
- AWS access keys (`AKIA...`)
- Private keys (`-----BEGIN`)

**If secrets found: HALT and report. Do not proceed.**

### Step 3: Debug artifact detection (WARNING)

Scan for leftover debug code:

- Python: `breakpoint()`, `pdb.set_trace()`, `print(` in non-test files, `import pdb`
- TypeScript: `console.log(`, `debugger;`
- General: `TODO: remove`, `FIXME`, `HACK`

Report as warnings — user decides whether to proceed.

### Step 4: ArcadeForge-specific security checks (WARNING)

For Python files in `apps/api/`:
- `eval(` or `exec(` outside of sandbox code
- `import os` or `import subprocess` in game-related code
- `shell=True` in subprocess calls
- SQL string concatenation (`f"SELECT` or `"SELECT" +`)

For TypeScript files in `apps/web/`:
- `dangerouslySetInnerHTML`
- `document.write`
- Inline `<script>` tags

### Step 5: Large file detection (WARNING)

```bash
git diff --cached --name-only | while read f; do
  size=$(wc -c < "$f" 2>/dev/null || echo 0)
  if [ "$size" -gt 1048576 ]; then
    echo "WARNING: $f is $(($size / 1024))KB"
  fi
done
```

Flag files > 1MB.

### Step 6: Lint check (WARNING)

For Python files:
```bash
cd apps/api && python -m ruff check <changed_files> 2>/dev/null || echo "ruff not installed, skipping"
```

For TypeScript files:
```bash
cd apps/web && pnpm lint 2>/dev/null || echo "lint not configured, skipping"
```

### Step 7: Generate commit message suggestion

Based on the staged changes, suggest a Conventional Commits message:

```
<type>: <short description>

<body if needed>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Step 8: Summary report

```
========================================
  Pre-Commit Scan Results
========================================

Files staged: <count>
Secrets found: <count> (BLOCKING)
Debug artifacts: <count> (warning)
Security issues: <count> (warning)
Large files: <count> (warning)
Lint issues: <count> (warning)

Verdict: ✅ SAFE TO COMMIT / ⚠️ REVIEW NEEDED / 🛑 BLOCKED
Suggested message: <commit message>
========================================
```
