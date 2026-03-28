---
name: assemble-team
description: Analyze ArcadeForge and assemble an optimal agent team tailored to the user's goals
arguments:
  - name: mode
    description: "new-feature, bug-fix, refactor, or audit"
    required: true
  - name: goals
    description: "Goals or pending items to accomplish"
    required: true
  - name: team-size
    description: "Max number of teammates (default: 5)"
    required: false
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Agent
---

# Skill: assemble-team

Assemble an agent team optimized for ArcadeForge work. This turns Claude from a solo assistant
into a coordinated engineering team.

## Workflow

### Step 1: Validate inputs

```
MODE = $mode (required: "new-feature", "bug-fix", "refactor", or "audit")
GOALS = $goals (required)
TEAM_SIZE = $team-size (default: 5, max: 7)
```

### Step 2: Analyze project context

1. Read `CLAUDE.md` and `ROADMAP.md` for conventions and priorities
2. Map directory structure with Glob
3. Parse goals:
   - If goals reference GitHub issues, fetch with `gh issue view`
   - If free-text, break into discrete tasks
   - If "pending items", scan for `TODO`, `FIXME`, `HACK`
4. Identify dependencies between tasks

### Step 3: Design team composition

Select from these roles:

| Role | Best For | Tools |
|------|----------|-------|
| **Architect** | API design, DB schema, module boundaries | Read, Glob, Grep, Write |
| **Implementer** | Production code (Python API or TypeScript frontend) | Read, Edit, Write, Bash, Glob, Grep |
| **Tester** | pytest tests, Playwright E2E | Read, Edit, Write, Bash, Glob, Grep |
| **Reviewer** | Code review, bug catching, security | Read, Glob, Grep |
| **Doc Writer** | README, API docs, inline docs | Read, Edit, Write, Glob, Grep |
| **Analyst** | Codebase mapping, tech debt, dependencies | Read, Glob, Grep, Bash |
| **Security Auditor** | OWASP, sandbox security, auth audit | Read, Glob, Grep, Bash |
| **DevOps** | Docker, CI/CD, infra configs | Read, Edit, Write, Bash, Glob, Grep |

Rules:
- Always include a **Reviewer**
- `new-feature`: Architect + Implementer + Tester required
- `bug-fix`: Analyst first, then Implementer + Tester
- `refactor`: Analyst + Implementer + Tester
- `audit`: Security Auditor + Analyst + Reviewer
- Sandbox/auth changes: Security Auditor mandatory

### Step 4: Create shared task list

Use `TaskCreate` for each work item. Dependencies:
- Architect → Implementer → Reviewer → Doc Writer
- Analyst blocks all other tasks (bug-fix/refactor modes)

### Step 5: Spawn the team

Use the `Agent` tool for each teammate:

```
Agent(
  name: "<role-name>",
  subagent_type: "general-purpose",
  prompt: "<role-specific prompt with ArcadeForge context and assigned tasks>",
  isolation: "worktree"  // only for agents that edit files
)
```

Spawn order:
1. First wave: Architect or Analyst
2. Second wave: Implementers + Testers (parallel)
3. Third wave: Reviewer
4. Fourth wave: Doc Writer

### Step 6: Coordinate and synthesize

As teammates complete:
1. Check output and task status
2. If reviewer finds issues, create fix tasks for implementer
3. When all done, synthesize summary

### Step 7: Report

```markdown
## Team Assembly Report

**Mode:** [mode]
**Team Size:** N teammates
**Tasks:** X completed / Y total

### Team Composition
| Teammate | Role | Tasks | Status |
|----------|------|-------|--------|

### Completed Work
- [what was accomplished]

### Review Findings
- [issues found and resolved]

### Next Steps
- [remaining work or recommendations]
```
