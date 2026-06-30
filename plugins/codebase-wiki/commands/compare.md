# /compare — Cross-Repo Comparison

Given repo names or design problem keywords, find the cheapest available information source along the escalation chain and produce a comparison.

**Announce at start:** "Running /compare <repo1> <repo2>..."

## Trigger

```
/compare <repo1> <repo2> [<repo3> ...] [--concept <keyword>] [--auto]
/compare --concept <keyword>
/compare <repo1> <repo2> ... --concept <keyword>
```

Examples:
```
/compare hermes-agent nanobot openclaw
/compare --concept memory
/compare hermes-agent openclaw --concept agent
```

## --auto mode

`--auto` skips user interaction but does NOT skip correctness checks. See each section's `[--auto]` annotation for impact.

```
          Normal mode           --auto mode
          ───────────           ───────────
Self-check MUST RUN             MUST RUN (unchanged)
Accuracy   MUST RUN → ask user  MUST RUN → write evolve-signals/ → continue
Structure  MUST RUN → ask user  MUST RUN → write evolve-signals/ → continue
Archive    ask user              skip (don't archive)
```

## 3-Level Escalation Chain

### Level 1 — Concept Comparison (cheapest, pre-computed)
Read `wiki/index.md` → find the Concepts table. For each concept covering the target repos, read the **Comparison** section of the concept page:
```bash
grep -A 50 "^## 对比" wiki/concepts/<slug>.md
```
Extract the comparison table — this is a pre-computed summary across repos.

### Level 2 — Entity Page (slightly more expensive)
When Level 1 doesn't cover a particular problem dimension, go to entity pages for the target repos:
```bash
ls wiki/repos/<name>/entities/
```
Read entity frontmatter (`problem:` field) → identify entities that address the same problem across repos → read their **Key Mechanisms** sections.

### Level 3 — Source Code (most expensive, last resort)
When Levels 1-2 still leave a specific comparison point unaddressed, read the actual source files (via the `source_files:` field in entity frontmatter). Read only the file and function ranges noted in provenance references.

## STOP 1 — Content Accuracy Self-Check

After producing the comparison output at any level, before presenting to the user:

1. Compare the generated comparison against concept page descriptions. Any inconsistency between what Level 3 source reading shows and what concept pages claim?

2. Check: do concept pages used in the comparison have provenance references? Are descriptions complete?

3. If discrepancies found → **STOP 1a: Content Repair Flow**:
   - (a) Present diff (old description → new description), inform user of discrepancy
   - (b) After user confirmation, write correction to wiki page. `[--auto]`: write signal to `evolve-signals/`
   - (c) Regenerate affected parts of the comparison output
   - (d) Log append: `[源码验证: <page> <section>修正] [触发: /compare]`

## STOP 2 — Concept Structure Self-Check

After STOP 1 passes, check concept structure:

1. Do any comparison results suggest a concept needs to be split? (Two very different approaches to the same concern, different enough to be independent design spaces)
2. Do any comparison results suggest concepts need to be merged? (Two concepts where repos choose essentially the same trade-off axis)
3. Do any comparison results suggest a new concept? (A recurring pattern across repos not yet captured)

If yes → present candidate operations, trigger evolve-apply logic. `[--auto]`: write signal to `evolve-signals/` → continue.

## Archive Decision

After comparison output is finalized:

```
> Archive this comparison?
> - A: Don't archive (ad-hoc view)
> - B: Save to wiki/views/
> - C: Initiate /ingest <repo> to fold comparison findings into Concept evolution
```

### Option B — Save as view
- Write `wiki/views/<YYYY-MM-DD>-compare-<slug>.md`
- Append to `wiki/log.md` with `[compare]` tag
- Update `wiki/index.md` `## Views` section

### After B — completion-gate
Invoke `/completion-gate` as a REQUIRED SUB-SKILL before claiming completion.
