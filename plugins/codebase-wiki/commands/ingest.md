# /ingest — Code Repository Ingest

Extract structural knowledge from source repositories and progressively evolve the wiki.

## Trigger

```
/ingest <repo-path> [<repo-name>] [--verify] [--full] [--auto]
```

- `<repo-path>`: Source directory (read-only)
- `<repo-name>`: Identifier in the wiki; defaults to the last segment of `<repo-path>`
- `--verify`: Enable Step 5 independent verification (disabled by default)
- `--full`: Force full re-extraction (skip delta detection)
- `--auto`: Skip all pause points, execute fully automatically (summary still written to log)

When the user asks to analyze, ingest, or add a code repository to the wiki.

### Multi-Repo Parallelism

When the user specifies multiple repos at once:

```
Steps 1+2 in parallel (each repo gets its own agent, concurrent)
  agent-1: repo-A → Entity extraction → Problem Space mapping
  agent-2: repo-B → Entity extraction → Problem Space mapping
  agent-3: repo-C → Entity extraction → Problem Space mapping

After all complete, converge:

Step 3  Problem Space matching (needs cross-repo info, unified processing)
  → All repos' problem-maps + existing seed bank + existing Concept pages
  → Produce candidate list (cross-repo comparison data now available → A/B/D types possible)

Steps 4-6 continue
```

**The parallel vs. serial dividing line: whether cross-repo information is needed.**
- Entity extraction (Step 1): only looks at single repo source → parallelizable
- Problem Space mapping (Step 2): only looks at single repo entity pages → parallelizable
- Problem Space matching (Step 3): needs comparison against other repos → must wait for all to complete

### Re-ingest (Incremental Update)

Running ingest again on a previously-ingested repo. Delta detection is not an optimization — without it, every re-ingest would require re-reading 500 repos' source code from scratch, an unacceptable token cost.

#### `.ingest-state.json` format

Stored inside the wiki project: `wiki/repos/<name>/.ingest-state.json` (sibling to `entities/` and `overview.md` — does not pollute the source repo).

```json
{
  "repo": "<name>",
  "source_path": "<absolute path to source directory>",
  "last_ingest": "<ISO 8601 timestamp>",
  "files": {
    "<repo-relative-path>": "<SHA-256 hex>",
    ...
  },
  "entity_map": {
    "<entity-slug>": ["<file-path>", ...]
  }
}
```

- `source_path`: Path to the source directory. If the user moved the repo, a changed path also counts as "needs re-detection."
- `files`: SHA-256 hashes of all source files actually read during ingest. Not every file in the repo — only those Step 1 actually read.
- `entity_map`: Which source files each entity depends on. Used during change detection for reverse mapping: file changed → which entities are affected.

#### Step 0 — Delta Detection

```
Your task is to perform delta detection for <repo-name>, determining what needs re-extraction.

## Input

- Source directory: <source-path>
- Last ingest snapshot: wiki/repos/<repo-name>/.ingest-state.json

## Detection logic

1. If wiki/repos/<repo-name>/.ingest-state.json does not exist:
   → Report "first ingest", trigger full pipeline (Steps 1-6)

2. Read .ingest-state.json, compare source_path:
   - If source_path differs from current source directory → path moved, trigger full re-ingest
   - Same → continue

3. Extract the files dictionary; for each path, compute SHA-256 of current file content, compare to snapshot
4. Record changed file list

5. If no changes:
   → Report "no changes", end. Do not execute subsequent steps.

6. If new files exist that weren't in the last snapshot (repo added files):
   → Read these new files, determine whether they contain new independent modules (entities)
   → If yes, mark them as affected entities

7. Reverse-map changed files + entity_map:
   → Does each entity's dependent files appear in the change list?
   → Yes: mark that entity as "affected", needs re-extraction

8. Output:
   - Changed files: <N>
   - Affected entities: <list>
   - New entity candidates: <list> (if any)
```

#### Step 1 (incremental mode)

Only re-extract affected entities + new entity candidates. Unaffected entity pages remain untouched.

overview.md is always refreshed — the entity list may have changed (additions/removals), and the tags description may be stale.

#### Snapshot update

In Step 6 wrap-up, overwrite `.ingest-state.json` with the files and SHA-256 hashes actually read during this ingest.

---

## Pipeline Overview

```
Step 1  Entity Extraction
        Input: source directory
        Output: wiki/repos/<name>/entities/<slug>.md (one file per Entity)
                wiki/repos/<name>/overview.md

Step 2  Entity Problem Space Mapping
        Input: Entity pages + optionally read source
        Output: seeds/<name>-problem-map.md

★ Pause Point 1 (user confirms problem space list completeness)

Step 3  Problem Space Matching
        Input: problem-map + seed bank + existing Concept pages
        Output: seeds/<name>-candidates.md
                evolve-signals/<date>-<name>.md (Type D signals)

★ Pause Point 2 (user confirms candidate list + capability coverage table)

Step 4  Concept Writing (per-Concept independent agent)
        Input: Type A/B entries from candidates.md
        Output: wiki/concepts/<slug>.md (new or appended)

Step 5  [optional, --verify] Independent Verification + Repair
        Input: Step 4 output
        Output: verification report → repaired Concept pages

Step 6  Seed Bank Update + Evolution Report Finalization
        Input: problem-map + candidates.md
        Output: seeds/master.md updated
                wiki/log.md + wiki/hot.md updated

★ Pause Point 3 (user reviews ingest summary, decides whether to trigger /evolve-apply)
```

Outside of pause points, the LLM executes autonomously.

---

## Step 1: Entity Extraction

Run the following prompt:

```
Your task is to extract all Structural Entities from <repo-name> source code.

## Input source

Source directory: <source-path>
This is the sole source of information — do not use prior knowledge from training data.

## Approach

Decide for yourself which files to read. Explore broadly until you comprehensively understand the repo structure.
Criterion: does a module have an independent responsibility boundary, external interface, and can it be understood and replaced in isolation?

## Output each Entity as a separate file

Path: wiki/repos/<repo-name>/entities/<slug>.md

Format:

---
type: entity
repo: <repo-name>
slug: <slug>
problem: <one-sentence problem description, "how to..." form>
generated: <YYYY-MM-DD>
source_files:
  - <repo-relative-path>
---

# <Entity Name>

**Code location**: <directory/package path>
**What problem this module solves**:
- Implementation layer: <what this repo concretely does, one sentence>
- Problem layer: <same as frontmatter problem field, "how to..." form>
**What it exposes**: <key classes/functions/interfaces, with file-path:line>
**What it interacts with**:
- Depends on [[entities/<slug>]] (<one-sentence explanation>)
- Called by [[entities/<slug>]] (<one-sentence explanation>)
(same-repo entities use wikilinks; external libraries use plain text)
**Why it is separable**: <independent directory? independent interface? independent package?>

**Key Mechanisms** (visible in source):
- <mechanism 1>: <description> ^[file-path:line]
- <mechanism 2>: ...

**Source evidence**:
- Entry file: <path>
- Core type/interface definitions: <path:line>

## Additional output: Repo Overview

Path: wiki/repos/<repo-name>/overview.md

Content:
- What this repo is (one paragraph)
- Core subsystem list, **each item with wikilink**: `- [[repos/<repo-name>/entities/<slug>]]`
- What it explicitly does NOT do

## Core constraints

1. Every factual claim must have ^[file-path:line] provenance
2. Each Entity gets its own file — do not merge
3. Explore broadly — do not miss independent directories or independent packages
```

---

## Step 2: Entity Problem Space Mapping

Run the following prompt:

```
Your task is to translate all Entity pages for <repo-name> into problem space entries.

## Who you are translating for

Framework Builder — someone studying the design space of a framework class.
They need to know: is this a question that everyone building a similar framework must answer?
What choice did this repo make on this question?

## Input

- Entity pages: wiki/repos/<repo-name>/entities/*.md
- Source directory: <source-path> (read on demand when Entity page "problem layer" descriptions are unclear)
- Do not read the existing seed bank or other repos' results; work independently

## Phase 1: Per-Entity Mapping

For each Entity:

1. Determine whether its "problem layer" question is worth entering as a candidate:
   Would someone building a similar framework have to make a design choice on this question?
   → Yes: generate one problem space entry (only one), focused on the fundamental reason this Entity exists
   → No (implementation detail / unique to this repo): skip

2. When generating an entry, supplement with this repo's solution and concerns

## Phase 2: Cross-Entity Coverage Check

After Phase 1 completes, perform the following purely mechanical operation:

1. Collect every item listed in the **Key Mechanisms** section of each mapped Entity's body.
   For each item, ask yourself: if you strip away the domain-specific terminology belonging to that Entity's problem domain,
   does the remaining structure still describe an independent design choice?
   If yes → add to candidate pool, annotate with source Entity
   If no → ignore (it's just that Entity's implementation tactic within its problem domain)

2. After the candidate pool is collected, check whether the same design choice (or highly similar)
   is mentioned by ≥2 different Entities.
   For each that satisfies this:
   - If the current problem-map already has an entry covering this design dimension → skip
   - If not → generate a supplementary problem space entry, same format as Phase 1,
     **Source Entity** listing all Entity slugs involved in this design

## Output format

Path: seeds/<repo-name>-problem-map.md

Each problem space entry:

---
## <Problem Name> ("how to..." form)

**Problem Statement**: <why everyone building a similar framework must face this question, one sentence>
**Core Concerns**:
- Concern 1: <mutually-constraining requirements, one sentence>
- Concern 2: ...
**<repo-name>'s Solution**: <one sentence>
**Source Evidence**: <file-path:line>
**Source Entity**: <Entity slug>
**Level**: Architectural Decision / Technology Choice

End-of-file notes:

### Skipped Entities
- <slug>: <reason>

### Cross-Entity Coverage Check
| Candidate Design Element | Involved Entities | Added Entry | Rationale |
|-------------------------|-------------------|-------------|-----------|
| ...                     | ...               | Yes/No      | ...       |
```

---

## ★ Pause Point 1: Problem Space Completeness Confirmation

After Step 2 completes, present the following summary and wait for user confirmation:

```
Extracted <N> problem spaces from <M> Entities:

| Problem Space                 | Source Entity    | Level              |
|-------------------------------|------------------|--------------------|
| How to...                     | <entity-slug>    | Architectural      |
| ...                           | ...              | ...                |

Skipped Entities (<K>, implementation details):
- <slug>: <reason>

Any missing capability domains? Confirm to proceed to Step 3.
```

User can: point out omissions → LLM supplements extraction, updates problem-map → continues.
No response from user → auto-continue.

**If --auto: skip user confirmation, proceed directly to Step 3. Still output problem space list and skipped entity summary to log.**

---

## Step 3: Problem Space Matching

Run the following prompt:

```
Your task is to compare <repo-name>'s problem space mapping results against existing Concept pages and produce a candidate list.

## Input

- New repo problem space mapping: seeds/<repo-name>-problem-map.md
- Existing seed bank: **Do NOT read seeds/master.md in full.** Grep seeds/master.md with keywords from the problem-map, only read matching lines: `grep -i "keyword1\|keyword2\|..." seeds/master.md`
- Existing Concept pages:
  **Scale detection**: first run `ls wiki/concepts/*.md 2>/dev/null | wc -l` to get total Concept count

  **If ≤ 50 Concepts (Strategy A)**:
    1. `for f in wiki/concepts/*.md; do head -10 "$f"; done` scan all Concept frontmatter in one pass
    2. For Concepts the LLM judges to have semantic relevance, deep-read the full "Core Problem" and "Concerns" sections

  **If 50–500 Concepts (Strategy B)**:
    1. From each problem-map entry's "Problem Name," extract 2–4 core technical keywords
       - Choose substantive technical terms; skip connectors like "how to," "the," "a." If common English equivalents exist, include English variants.
       - Example: "How to let main Agent delegate background sub-agent to execute complex tasks" → subagent delegate isolation execution
       - Counter-example: short abbreviations like "MCP," "RAG," "LLM" (2–3 characters) are equally high-value keywords — do NOT skip them due to short length. They are concentrated signals in technical documentation and core signals for precise matching.
    2. 【Per-entry independent grep — strictly forbid cross-entry merging】For each entry in the problem-map, perform one grep using only that entry's own extracted keywords. Do NOT merge keywords from different entries into a single giant grep:
       - Entry 1: `grep -l "entry1-kw1\|entry1-kw2\|..." wiki/concepts/*.md` → record as result list A
       - Entry 2: `grep -l "entry2-kw1\|entry2-kw2\|..." wiki/concepts/*.md` → record as result list B
       - ...and so on. After each entry's grep, record its hit file list separately.
       - **Strictly forbidden**: synthesizing all entries' keywords into one grep — merging breaks the correspondence between hits and entries, and some entries may get zero hits because their keywords are diluted in a long OR chain.
    3. 【Self-check: per-entry grep execution coverage audit】Before merging and deduplicating, audit the grep execution records entry by entry:
       - For every entry in the problem-map, confirm it has a corresponding grep execution record (i.e., result list A, B, ...)
       - If any entry is found without a grep execution (missing its result list), immediately go back to step 2 and run grep for it
       - Only after the self-check passes (all entries have been grep'd and results recorded) may you proceed to step 4
    4. Merge all entries' hit file lists and deduplicate
    5. Only run `head -10` on deduplicated files to confirm frontmatter match
    6. Deep-read the full text of confirmed-matching Concepts

  **If > 500 Concepts (Strategy C)**:
    1. First execute Strategy B
    2. For unmatched entries, extract expanded terms from matched Concepts' `concerns` fields, run a second round of grep
    3. Entries still unmatched → mark as "manual review needed" (not a search failure — genuinely no matching Concept), explain why

## Search behavior constraints

Before starting matching, must execute scale detection and explicitly declare:
"Detected N Concepts → selected Strategy [A/B/C]"

Then execute retrieval per the chosen strategy.

## Classification criteria

For each problem space entry, classify into one of four cases (see below).
When creating new or appending, must pass the following criteria check (single-source definition in `schema/concept-criteria.md`):

Hard thresholds (all three must pass):

① Multiple Solutions
   At least two different repos solve the same problem in clearly different ways.
   Note: if after analysis one solution dominates another on all trade-off dimensions,
   this is not a genuine design trade-off — does not qualify.

② Independent Design Space
   This problem cannot be fully covered by an existing problem space —
   merging it in would cause its own discussion dimensions to disappear,
   and the Framework Builder would lose decision value on this problem.

③ Persistent Trade-off
   No silver bullet across different solutions —
   satisfying Concern A increases the cost of satisfying Concern B, and vice versa.

Auxiliary criterion (not meeting it does not veto; affects priority):

④ Sustainable Extensibility
   New repos are likely to contribute new solutions to this problem in the future.
   If no new repos join long-term, trigger "downgrade" evolution recommendation.

## Few-shot examples

### Example Domain 1: AI Agent Frameworks

Input Entities (cross-repo):
- OpenClaw: Agent (YAML config), Workflow (explicit orchestration), Memory (external context injection),
            ToolTimeout (per-tool YAML timeout config)
- HermesAgent: Agent (@agent decorator), EventBus (event-driven coordination),
               Memory (internal state sync), ToolTimeout (per-toolset timeout)

Positive example — "Agent Definition Style":
① At least two repos, different approaches: config-driven vs. decorator-driven. ✅
② Independent design space: evaluation dimensions are declarative convenience vs. programming flexibility;
   does not share evaluation dimensions with "multi-Agent coordination." ✅
③ Persistent trade-off: config is simple but inflexible vs. programming freedom with higher barrier; no silver bullet. ✅
④ Sustainable extensibility: new frameworks will still make different choices on this question. ✅
Decision: ✅ Create new Concept page agent-definition-style

Counter-example 1 — fails ①: single repo only
Candidate group "HermesAgent SafeWriter pipeline protection":
① Multiple solutions: ❌ Only HermesAgent has this; other repos have no corresponding Entity.
Decision: ❌ Enter seed bank for observation; does not qualify as a Concept

Counter-example 2 — fails ②: not an independent design space
Candidate group "Tool Execution Timeout Configuration":
① Multiple solutions: OpenClaw uses per-tool YAML timeout; HermesAgent uses per-toolset timeout. ✅
② Independent design space: ❌ "Timeout configuration" is a sub-dimension of the existing problem space
   "Tool Execution Safety & Control." Merging it in would not lose discussion dimensions.
Decision: ❌ Does not qualify; handle as sub-dimension of "Tool Execution Safety" Concept

Counter-example 3 — fails ③: no genuine trade-off
Candidate group "Structured Log Format":
① Multiple solutions: OpenClaw uses plain text; HermesAgent uses structured JSON + auto-redaction. ✅
② Independent design space: log format has its own evaluation dimensions. ✅
③ Persistent trade-off: ❌ Structured JSON dominates plain text on all concerns;
   this is not a mutually-constraining trade-off — one solution simply hasn't evolved yet.
Decision: ❌ Does not qualify; record plain-text format as historical note

Counter-example 4 — fails ④ (auxiliary)
Candidate group "Agent Process Startup Order":
① ✅ ② ✅ ③ ✅
④ Sustainable extensibility: ⚠️ As async runtimes proliferate, this problem space may converge quickly.
Decision: ⚠️ Create page tentatively; note "low extensibility expectation" in evolve signal file

### Example Domain 2: Embedded Databases

Input Entities (cross-repo):
- SQLite: B-Tree (storage structure), WAL (write-ahead log)
- LevelDB: LSM-Tree (storage structure), MemTable+SSTable (write pipeline)
- RocksDB: ColumnFamily, Compaction (compaction strategy), BloomFilter

Positive example — "Storage Engine Core Data Structure":
① B-Tree vs LSM-Tree, fundamentally different design philosophies. ✅
② Independent evaluation dimensions from persistence strategy. ✅
③ Read-optimized vs. write-optimized; classic no-silver-bullet trade-off. ✅
Decision: ✅ Create new Concept page storage-engine-data-structure

Counter-example — fails ①:
Candidate group "Bloom Filter Strategy":
① ❌ Only RocksDB has BloomFilter.
Decision: ❌ Enter seed bank for observation

## Four case types

Case A — Hits existing problem space
  Core problem is the same as an existing Concept page
  Action: mark "append to <slug>"

Case B — New problem space, passes all three hard thresholds
  Action: mark "create new Concept page," with one-sentence justification for each criterion

Case C — Pending observation
  Currently only one repo faces this problem
  Action: enter seed bank; do not promote

Case D — Evolve signal
  Partially overlaps with existing Concept but does not fully match
  Action: record as evolve signal; do not enter this round's writing

## Output

File 1: seeds/<repo-name>-candidates.md
  Each entry: case type / problem name / target slug (Case A) or new name (Case B) / justification

  End-of-file capability coverage table (for human review):
  | Capability Domain | <repo1> | <repo2> | <new-repo> |
  |-------------------|---------|---------|------------|
  | <domain>          | ✅/—   | ✅/—   | ✅/—      |

File 2: evolve-signals/<YYYY-MM-DD>-<repo-name>.md
  Only Type D signals, each:
  - Problem: <name>
  - Related Concept: <slug>
  - Signal type: granularity mismatch / merge candidate / split candidate
  - Reason: <one sentence>
```

---

## ★ Pause Point 2: Candidate List Confirmation

After Step 3 completes, present:

```
Concept candidate list:

  Type A (append to existing page): <N>
    - <problem-name> → [[<slug>]]
    ...

  Type B (create new Concept page): <N>
    - <problem-name> (new <slug>)
      Justification: ①<one sentence> ②<one sentence> ③<one sentence>
    ...

  Type C (pending observation): <N>
  Type D (evolve signals): <N>, written to evolve-signals/

Capability coverage table:
| Capability Domain | Repo A | Repo B | New Repo |
|-------------------|--------|--------|----------|
| ...               | ...    | ...    | ...      |

Adjust anything? Confirm to proceed to Step 4.
```

User can: veto a Type B creation / manually promote a Type C / adjust slug naming.
No response from user → auto-continue.

**If --auto: skip user confirmation, proceed to Step 4 directly with model-determined A/B/C/D classification. Still output candidate list summary and capability coverage table to log.**

---

## Step 4: Concept Writing

For each Type A/B entry in candidates.md, launch an independent agent:

```
You are responsible for writing or updating a Concept page. Process one Concept at a time.

## Who is the reader

Framework Builder — someone studying the design space of this framework class.
They don't need to know which is "best"; they need a complete design space map:
on this design problem, what choices did different frameworks make, and what is the cost of each choice.

## Input

- A single entry from the candidate list (Case A or B)
- Entry source: seeds/<repo-name>-candidates.md
- If Case A: existing Concept page wiki/concepts/<slug>.md
- Source directory (must read source to verify; don't rely solely on mapping results)

## Mandatory rules

1. Every claim must have source evidence ^[file-path:line]
2. Case A (append): only add new repo content; do NOT modify existing repo content
3. Concept naming format: <capability-domain>-<decision-dimension> (lowercase kebab-case)
4. Comparison table focuses on tensions between concerns, not a feature list
5. **All repo solutions must read the corresponding entity page to obtain source citations; reproducing from memory is not permitted.** New repo: read `wiki/repos/<new-repo>/entities/<slug>.md`; existing repos: read `wiki/repos/<existing-repo>/entities/<slug>.md`. Format: one section per repo, section header `### <repo-name>`, first line of body `Source: [[repos/<repo-name>/entities/<entity-slug>]]`, each key mechanism annotated with `^[file-path:line]`.
6. **After writing this page, check that the `repos:` frontmatter lists every `### <repo>` section in the body.** If the body discusses N repos, repos must contain N entries.

## Output

Path: wiki/concepts/<slug>.md

---
type: concept
concept: <slug>
problem: <core problem, one sentence>
concerns: [<concern1>, <concern2>]
repos: [<repo-list>]
generated: <YYYY-MM-DD>
---

# <Concept Name>

## Core Problem

<Why everyone building a similar framework must answer this question>
<What is the fundamental tension between different solutions>

## Concerns

<How the concerns constrain each other>

## Solutions by Framework

### <repo-name>

Source: [[repos/<repo-name>/entities/<entity-slug>]]
**Solution**: <one sentence>
**Implementation**: <key mechanisms> ^[file-path:line]
**Trade-offs**: which concerns are satisfied, at what cost

[one section per repo]

## Comparison

| Framework | Concern A | Concern B | Concern C |
|-----------|-----------|-----------|-----------|

## Evolution Log

- <YYYY-MM-DD>: Initial creation, covers <repo-name>
- <YYYY-MM-DD>: Added <repo-name>

## Post-write action

After writing this page, go to **every repo mentioned** in the body's entity pages (`wiki/repos/<name>/entities/<slug>.md`) and append a backlink at the end — not just the new repo; existing repos referenced in the body also need backlinks.
If the entity already has backlinks from other concepts, append to the existing list; if none, create a new list:

```
**Associated Concepts**:
- [[concepts/<this-slug>]]
```

Note: an entity may be associated with multiple concepts — e.g., MemoryManager involves both memory-backend-replaceability and state-synchronization. When appending, do not overwrite existing entries.
```

---

## Step 5: Verification + Repair (when `--verify` is enabled)

```
## Verification agent

Input: wiki/concepts/<slug>.md + corresponding repo source

For each repo's solution, verify one by one:
1. Source evidence exists (path:line can be found)
2. Description matches source (no exaggeration, no omission of key constraints)
3. Comparison table judgments have source support

Output verification report:
  ✅ Accurate
  ⚠️ <description>: partially inaccurate, repairable
  ❌ <description>: critically wrong, needs rewrite

---

## Repair agent

Input: verification report + wiki/concepts/<slug>.md + source

Only repair ⚠️ or ❌ items.
Do not modify content that passed verification.
Every modification must include a repair reason.
```

---

## Step 6: Seed Bank Update + Snapshot Save

```
Complete the wrap-up work for this ingest.

## Input

- Problem space mapping: seeds/<repo-name>-problem-map.md
- Candidate list: seeds/<repo-name>-candidates.md
- Existing seed bank: seeds/master.md (skip if doesn't exist)
- Source directory: <source-path>

## Six operations

1. Merge into seed bank
   Append all problem space entries for <repo-name> (Type A/B/C all go in) to seeds/master.md
   Annotate with source repo and case type

2. Confirm evolve signal file
   Verify evolve-signals/<YYYY-MM-DD>-<repo-name>.md exists and is complete
   (generated in Step 3; this step only confirms integrity)

3. Update wiki/index.md
   - Repos section: add or update <repo-name> row (format per maintenance file spec)
   - Concepts section: refresh Concept table per format (sync added/updated Concept rows)

4. Overwrite wiki/hot.md:
   # Hot Context
   **Last operation:** ingest <repo-name> — <Entity count> entities, <Concept count> concepts
   **Active repos:** <all currently ingested repos, comma-separated>
   **Concept pages:** <N>
   **Pending evolve signals:** <K> (evolve-signals/)

5. Append to wiki/log.md:
   [<YYYY-MM-DD HH:MM>] ingest <repo-name> — <Entity count> entities, <Concept count> concepts updated/created

6. Overwrite wiki/repos/<repo-name>/.ingest-state.json:
   Overwrite the snapshot with the files and SHA-256 hashes actually read during this ingest.
   Write the current source directory path to source_path.
   Populate entity_map: collect mapping from each entity page's frontmatter source_files field.
   Format: { "<entity-slug>": ["<relative-file-path>", ...], ... }
   entity_map is used in Step 0 delta detection for reverse mapping — when a file changes, you know which entities are affected.
   Not populating it forces scanning all entity page frontmatter on every re-ingest, unacceptable at 500-repo scale.
```

---

## Before Step 6 Wrap-up

**REQUIRED SUB-SKILL:** Before claiming "ingest complete," must invoke `completion-gate` to verify maintenance file consistency.

---

## ★ Pause Point 3: Ingest Completion Summary

After Step 6 completes, present:

```
ingest <repo-name> complete:
  - <M> Entities extracted
  - <N> Concept pages updated/created
  - <K> evolve signals written to evolve-signals/<date>-<name>.md

Suggested next steps:
  1. Trigger /evolve-apply to process <K> evolve signals
  2. Continue ingesting next repo: <suggested repo name>
  3. Deep-dive current Concept: /query <slug>
```

**If --auto: don't wait for user decision; default to NOT triggering /evolve-apply. Still output completion summary and suggested next steps to log.**

---

## File Structure Specification

```
wiki/                       ← Persistent knowledge (committed to git)
  repos/
    <name>/
      .ingest-state.json    ← Step 6 maintained (delta snapshot)
      overview.md           ← Step 1 output (new or overwritten)
      entities/             ← Step 1 output
        <slug>.md
  concepts/                 ← Step 4 output
    <slug>.md

seeds/                      ← Pipeline artifacts (project root, sibling to wiki/)
  <name>-problem-map.md     ← Step 2 output
  <name>-candidates.md      ← Step 3 output
  master.md                 ← Step 6 maintained

evolve-signals/             ← Signal inbox (project root, sibling to wiki/)
  <YYYY-MM-DD>-<name>.md    ← Step 3 output (Type D signals)
```

### Path Discipline (Mandatory)

Pipeline artifact (`seeds/` and `evolve-signals/`) path rules:
- **Must write to `seeds/` and `evolve-signals/` at project root, siblings to `wiki/`**
- **Never write under `wiki/repos/<name>/`** — that pollutes the wiki knowledge base, causing false lint positives and maintenance chaos
- `seeds/` and `evolve-signals/` are not wiki pages, not inside the Obsidian vault, do not need wikilinks
- Correct example: `seeds/hermes-agent-problem-map.md` ← ✅
- Incorrect example: `wiki/repos/hermes-agent/seeds/hermes-agent-problem-map.md` ← ❌

## Maintenance File Specs

The following three files are automatically maintained by the LLM after ingest / query / compare / evolve operations.
Format must be strictly followed — `/query` Level 1 index scan and `/lint` checks both depend on these formats.

### wiki/index.md

**Role**: Wiki directory page. The first read target in `/query`'s Level 1 index scan — the LLM uses it to determine "are there relevant pages worth digging into."

**Format**:

```markdown
# Codebase Wiki

## Repos

- [[<name>/overview]] — <one-sentence description> — topics: <comma-separated> — last ingest: <YYYY-MM-DD>

## Concepts

| Problem | Page | Covered Repos |
|---------|------|---------------|
| <one-sentence problem> | [[concepts/<slug>]] | <repo>, <repo> |
| ... | ... | ... |

## Views

- [[views/<filename>]] — <description> — <YYYY-MM-DD>

## Insights

- [[insights/<filename>]] — <title> — <YYYY-MM-DD>
```

### wiki/log.md

**Role**: Operation log. `/lint` checks last operation time etc.

**Format** (append only, never modify existing lines):

```
[YYYY-MM-DD HH:MM] <operation> <detail>
```

### wiki/hot.md

**Role**: Hot context. Overwritten on every operation. `/lint` reads rapidly when checking staleness.

**Format**:

```markdown
# Hot Context

**Last operation:** <most recent operation and result>
**Active repos:** <all currently ingested repos, comma-separated>
**Concept pages:** <N>
**Pending evolve signals:** <K>
```
