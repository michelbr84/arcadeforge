---
name: fix-issue
description: "Fix a GitHub issue from start to finish, following TDD principles."
arguments:
  - name: issue
    description: "GitHub issue number"
    required: true
  - name: repo
    description: "Repository (default: michelbr84/arcadeforge)"
    required: false
tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# Fix Issue Skill

Fix a GitHub issue end-to-end using TDD principles.

## Workflow

### Step 1: Load environment
```bash
REPO="${repo:-michelbr84/arcadeforge}"
ISSUE="${issue}"
```

### Step 2: Analyze the issue
```bash
gh issue view $ISSUE --repo $REPO
```

Read the issue carefully. Identify:
- Expected behavior vs. actual behavior
- Affected area (auth, games, validation, sandbox, frontend, workers)
- Severity and priority

### Step 3: Locate affected code

Use Glob and Grep to find relevant files. Key locations in ArcadeForge:

| Area | Path |
|------|------|
| Auth | `apps/api/app/auth/` |
| Games | `apps/api/app/games/` |
| Database | `apps/api/app/db/models.py` |
| Workers | `workers/` |
| Frontend | `apps/web/src/` |
| Config | `apps/api/app/config.py` |

### Step 4: Write a failing test FIRST

Before any code changes, write a test that reproduces the bug:

- Python API tests go in `apps/api/tests/`
- Follow naming: `test_<module>_<scenario>.py`
- Run the test to confirm it FAILS:

```bash
cd apps/api && pytest tests/test_<module>.py -v --tb=short
```

### Step 5: Fix the code

Apply the minimal change needed to make the test pass. Do NOT over-engineer.

### Step 6: Validate

```bash
cd apps/api && pytest --tb=short -q
```

All tests must pass — both the new test and all existing ones.

### Step 7: Commit and open PR

```bash
git checkout -b fix/issue-$ISSUE
git add <changed files>
git commit -m "fix: <description> (closes #$ISSUE)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"

git push -u origin fix/issue-$ISSUE

gh pr create \
  --title "fix: <short description>" \
  --body "Closes #$ISSUE

## Root Cause
<what caused the bug>

## Fix
<what was changed>

## Test
<what test was added>

🤖 Generated with Claude Code" \
  --repo $REPO
```

### Step 8: Report to user

Tell the user:
- Root cause
- What test was added
- What code was changed
- PR link
