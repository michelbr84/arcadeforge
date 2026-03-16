---
name: review-pr
description: "Perform a thorough code review of a GitHub PR and post structured feedback."
arguments:
  - name: pr
    description: "PR number to review"
    required: true
  - name: repo
    description: "Repository (default: michelbr84/arcadeforge)"
    required: false
tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Review PR Skill

Structured code review for ArcadeForge pull requests.

## Workflow

### Step 1: Load context

```bash
REPO="${repo:-michelbr84/arcadeforge}"
PR="${pr}"
```

### Step 2: Fetch PR metadata and diff

```bash
gh pr view $PR --repo $REPO
gh pr diff $PR --repo $REPO
```

Read: title, description, linked issues, labels, full diff.

### Step 3: Analyze the diff

Evaluate across these dimensions:

**Correctness**
- [ ] Logic errors or unhandled edge cases?
- [ ] Off-by-one errors, null dereferences, race conditions?
- [ ] Error handling (not just happy path)?

**Security (CRITICAL for ArcadeForge)**
- [ ] SQL injection risk? (string-concatenated queries)
- [ ] XSS risk? (user input rendered directly)
- [ ] Secrets or credentials in code?
- [ ] Unsafe code execution? (`eval`, `exec`, `subprocess` without validation)
- [ ] Sandbox escape vectors? (network access, filesystem escape)
- [ ] Auth bypass? (missing session checks, broken access control)
- [ ] CSRF protection intact?

**ArcadeForge-Specific**
- [ ] Game code handled safely? (scanner check before execution)
- [ ] Async/await used correctly for DB and Redis operations?
- [ ] arq tasks properly defined and enqueued?
- [ ] Alembic migration included for schema changes?
- [ ] UI text is in English?

**Tests**
- [ ] New features covered by tests?
- [ ] Bug fixes have regression tests?
- [ ] Tests actually test what they claim?
- [ ] `pytest` passes?

**Style and Maintainability**
- [ ] Consistent with CLAUDE.md conventions?
- [ ] Type hints present (Python)?
- [ ] No `any` types (TypeScript)?
- [ ] No unnecessary comments or dead code?

### Step 4: Compose structured review

```markdown
## Review: PR #$PR

**Verdict**: APPROVED | CHANGES REQUESTED | NEEDS DISCUSSION

### Summary
<1-2 sentence summary>

### Strengths
- <positive observation>

### Issues (must fix before merge)
- **[BLOCKING]** <file>:<line> — <issue description>

### Suggestions (optional improvements)
- **[SUGGESTION]** <file>:<line> — <suggestion>

### Security
- <any security observations, or "No security concerns found">

### Test Coverage
- <assessment of test coverage>
```

### Step 5: Post the review

If blocking issues:
```bash
gh pr review $PR --repo $REPO --request-changes --body "<review>"
```

If clean:
```bash
gh pr review $PR --repo $REPO --approve --body "<review>"
```

### Step 6: Report to user

Tell the user the verdict and list any blocking issues.
