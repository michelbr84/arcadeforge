---
name: refactor-module
description: Safely refactor a module — captures a test baseline first, applies the refactor, then verifies all tests still pass.
arguments:
  - name: file
    description: Path to the file to refactor
    required: true
  - name: goal
    description: Description of the refactoring goal
    required: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# Skill: refactor-module

Safely refactor an ArcadeForge module with test-backed confidence.

## Arguments

- `--file <path>` — file to refactor (required)
- `--goal <description>` — what to achieve (required)

## Workflow

### Step 1: Read the file
Read the full implementation. Understand:
- Public API (functions, classes, exports)
- Internal structure and dependencies
- Any TODOs or known issues

### Step 2: Find the test file
Look for a corresponding test file:

| Source | Test |
|--------|------|
| `apps/api/app/auth/*.py` | `apps/api/tests/test_auth_*.py` |
| `apps/api/app/games/*.py` | `apps/api/tests/test_games_*.py` |
| `apps/api/app/db/*.py` | `apps/api/tests/test_db_*.py` |
| `workers/**/*.py` | `workers/**/test_*.py` |
| `apps/web/src/**/*.ts` | `apps/web/src/**/*.test.ts` |

If no test file exists, stop and tell the user.

### Step 3: Capture test baseline
```bash
cd apps/api && python -m pytest <test-file> -v --tb=short
```
Record: total tests, pass/fail counts. If tests already fail, stop.

### Step 4: Plan the refactor
Based on `--goal`, identify:
- What changes are needed
- What should NOT change (public API, behavior)
- Order of changes to minimize breakage

### Step 5: Apply the refactor
Make targeted changes with Edit. Prefer:
- Small, incremental edits
- Rename across all call sites (Grep to find usages)
- Keep public API intact unless goal explicitly requires it

### Step 6: Run tests
```bash
cd apps/api && python -m pytest <test-file> -v --tb=short
```
If tests fail: fix the refactor error (not the test), re-run until green.

### Step 7: Run full suite
```bash
cd apps/api && python -m pytest --tb=short -q
```

### Step 8: Report
- What was refactored
- Public API changes (if any)
- Test results: before vs. after
- Issues discovered during refactoring
