# /lint — Wiki Health Check

Full-structural health check of the entire wiki. Manually invoked by the user.

## Role

`lint.py` is the comprehensive health-check tool for wiki structural integrity. It scans all wiki pages, checking wikilink validity, frontmatter compliance, repo consistency, orphan pages, provenance coverage, and view freshness.

**Relationship to completion-gate:** The gate is a scoped self-check ("Did I do this operation correctly?"), lint is a full audit ("Is the entire wiki healthy?"). The gate does not auto-run lint. Users manually run `/lint` periodically for full health checks, or when the gate suggests it.

## Trigger

```
/lint
/lint --fix      # attempt auto-fix for INFO-level issues
```

## Execution Protocol

### Step 1 — Run lint.py

```bash
python scripts/lint.py --wiki wiki/
```

### Step 2 — Frontmatter compliance check

Scan all entity pages and concept pages, verify required fields.

**Entity pages** (`wiki/repos/*/entities/*.md`) must each have:
- `type: entity`
- `repo:` — owning repo name
- `slug:` — entity identifier
- `problem:` — problem-level description, "how to..." form
- `source_files:` — source file list (at least one)
- `generated:` — generation date

Missing any → `[ERROR] entity_missing_frontmatter`

**Concept pages** (`wiki/concepts/*.md`) must each have:
- `type: concept`
- `concept:` — concept identifier
- `problem:` — core problem, one sentence
- `concerns:` — concern list (can be empty array `[]`)
- `repos:` — repo list
- `generated:` — generation date

Missing any → `[ERROR] concept_missing_frontmatter`

**Concept page structure check:**
Must contain `## Evolution Log` section. Missing → `[WARN] concept_missing_evolution_log`

**Entity → Concept backlink check:**
For each concept page, take the repos in its `repos:` list, check that the corresponding source entity pages have `**Associated Concepts**: [[concepts/<slug>]]` at the end of the file.
Missing → `[WARN] entity_missing_concept_backlink`

### Step 3 — Report findings

Present a summary organized by severity:

**Errors (must fix):**
- List each [ERROR] finding with file and detail

**Warnings (should fix):**
- List each [WARN] finding

**Info (optional):**
- List each [INFO] finding

**Health score:**
- Wikilink integrity: X% (broken links / total links)
- Entity frontmatter compliance: X%
- Concept frontmatter compliance: X%
- Concept evolution log coverage: X%

### Step 4 — Remediation guidance

ERROR level:
- `check_broken_wikilinks` → check whether the target file exists. If pointing to old `nodes/` or `dimensions/` paths, these are legacy links — delete them directly
- `entity_missing_frontmatter` → fill in missing frontmatter fields for the entity page
- `concept_missing_frontmatter` → fill in missing frontmatter fields for the concept page

WARN level:
- `concept_missing_evolution_log` → append `## Evolution Log` section to end of concept page (at minimum one initial-creation entry)
- `entity_missing_concept_backlink` → append `**Associated Concepts**: [[concepts/<slug>]]` to end of entity page

Never auto-fix errors without user confirmation. Auto-fix only INFO-level issues with `--fix`.
