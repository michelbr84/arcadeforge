---
name: generate-docs
description: Auto-generate documentation from ArcadeForge source code — extracts public APIs and creates markdown docs.
arguments:
  - name: dir
    description: Directory to scan for source files
    required: true
  - name: output
    description: Output directory for docs (default: docs/)
    required: false
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# Skill: generate-docs

Scan ArcadeForge source files and generate structured markdown documentation.

## Arguments

- `--dir <directory>` — source directory to scan (required)
- `--output <dir>` — where to write docs (optional, defaults to `docs/`)

## Workflow

### Step 1: Discover source files

Use Glob to find source files in the target directory:
- Python: `**/*.py` (exclude `test_*`, `__init__.py`)
- TypeScript: `**/*.ts`, `**/*.tsx` (exclude `*.test.*`, `node_modules`)

### Step 2: Extract public API from each file

For each source file:
- **Python**: extract `def` and `class` definitions not starting with `_`
  - Include docstrings and type hints
- **TypeScript**: extract `export function`, `export class`, `export const`
  - Include JSDoc and type signatures

### Step 3: Add missing docstrings (in-source)

For public functions/classes missing documentation:
1. Infer purpose from name and body
2. Add docstring directly (Python: Google style, TS: JSDoc)
3. Only add docstrings — do not change logic

### Step 4: Create docs files

For each source file `app/foo.py`, create `docs/api/foo.md`:

```markdown
# foo

> <one-line description>

## Functions

### `function_name(param1: type, param2: type) -> return_type`

<docstring content>

**Parameters:**
- `param1` — description
- `param2` — description

**Returns:** description

**Example:**
```python
result = function_name(arg1, arg2)
```
```

### Step 5: Update docs index

Create/update `docs/api/README.md`:

```markdown
# API Reference

| Module | Description |
|--------|-------------|
| [foo](foo.md) | <one-liner> |
```

### Step 6: Report
- Files scanned: N
- Functions/classes documented: M
- Docstrings added: K
- Docs files created/updated: X
- Output location
