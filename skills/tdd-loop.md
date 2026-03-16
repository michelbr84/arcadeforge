---
name: tdd-loop
description: "Write failing tests from a spec, then iterate on implementation until all tests are green. Max 10 iterations."
arguments:
  - name: spec
    description: "What to implement (e.g., 'Argon2id password hashing with verify')"
    required: true
  - name: file
    description: "Target source file path (optional, auto-derived if omitted)"
    required: false
tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# TDD Loop Skill

Autonomous Red-Green-Refactor cycle for ArcadeForge.

## Workflow

### Step 1: Parse the specification

From the `--spec` argument, identify:
- Required functions/classes/endpoints
- Expected behavior (happy path)
- Edge cases and error scenarios
- Constraints (security, performance)

### Step 2: Derive file paths

Auto-derive test file from source file:

| Source | Test |
|--------|------|
| `apps/api/app/auth/passwords.py` | `apps/api/tests/test_auth_passwords.py` |
| `apps/api/app/games/service.py` | `apps/api/tests/test_games_service.py` |
| `apps/api/app/games/scanner.py` | `apps/api/tests/test_games_scanner.py` |
| `workers/generator/worker.py` | `workers/generator/test_worker.py` |

If `--file` is provided, use it. Otherwise, infer from spec context.

### Step 3: Write tests FIRST (RED phase)

Write comprehensive tests covering:
- Happy path (normal input → expected output)
- Edge cases (empty input, boundary values)
- Error cases (invalid input, missing data)
- Security cases (for auth: timing attacks, weak passwords, injection)

Tests MUST fail initially. Run to confirm:

```bash
cd apps/api && pytest <test_file> -v --tb=short
```

Expected: RED (failures).

### Step 4: Implement minimally (GREEN phase)

Write the simplest code that makes ALL tests pass. Rules:
- No over-engineering
- No features beyond the spec
- No premature abstractions
- Follow ArcadeForge conventions (type hints, async where needed)

### Step 5: Iterate (max 10 rounds)

For each failing test:
1. Read the failure message
2. Fix the implementation (not the test)
3. Re-run tests
4. If new test fails, go back to step 1

```bash
cd apps/api && pytest <test_file> -v --tb=short
```

If all green after ≤10 iterations, proceed. If stuck after 10, report to user.

### Step 6: Refactor (REFACTOR phase)

Only after ALL tests are green:
- Remove duplication
- Improve naming
- Add type hints if missing
- Do NOT add comments unless logic is non-obvious

Re-run tests after refactor:

```bash
cd apps/api && pytest --tb=short -q
```

### Step 7: Report

Tell the user:
- Number of iterations
- Tests written (count)
- Coverage notes
- Any edge cases discovered during implementation
