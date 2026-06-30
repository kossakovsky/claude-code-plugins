# /evolve-apply — Concept Evolution

Wikipedia-style Concept page evolution: merge, split, redirect.

## Trigger

```
/evolve-apply <signal-file>                 # Process all signals in the specified file
/evolve-apply                               # List all available signal files
/evolve-apply <signal-file> --skip-check    # Skip precondition checks (dangerous, only when user explicitly requests)
/evolve-apply <signal-file> --auto          # Skip operation confirmation prompts, execute directly after preconditions pass
/evolve-apply <signal-file> --skip-check --auto  # Fully automatic, no questions
```

`<signal-file>` can be a filename (e.g., `2026-06-24-hermes-agent.md`) or a full path.

Triggered when the user expresses intent to merge, split, or redirect Concept pages — whether from `/ingest` Type D signals, structural discoveries during `/compare`, or direct instructions.

## Execution Protocol

Every evolution operation appends to `wiki/log.md` with trigger source noted:

```
[<ts>] evolve merge <slug-A> → <slug-B> [trigger: /compare session]
[<ts>] evolve split <slug-src> → <new-slug> [trigger: /ingest pause point 2]
[<ts>] evolve redirect <alias> → <target> [trigger: user direct instruction]
```

### Step 0 — List signal files

```bash
ls -1 evolve-signals/
```

Display:

```
Available evolve signal files:

| File | Date | Source ingest |
|------|------|--------------|
| 2026-06-24-hermes-agent.md | 2026-06-24 | hermes-agent |
| 2026-06-20-openclaw.md     | 2026-06-20 | openclaw    |

Run `/evolve-apply <filename>` to process. Example:
  /evolve-apply 2026-06-24-hermes-agent.md
```

Stop.

### Step 1 — Read signal file

Read `evolve-signals/<filename>`, parse each signal:

- Problem: <name>
- Related Concept: <slug>
- Signal type: granularity mismatch / merge candidate / split candidate
- Reason: <one sentence>

Present grouped summary to user:

```
Signal file: <filename>
Total <N> evolve signals:

  Merge candidates (<K>):
    - "<slug-A>" should merge into "<slug-B>": <reason>
    ...

  Split candidates (<K>):
    - Split out "<sub-topic>" from "<slug-src>": <reason>
    ...

  Redirect candidates (<K>):
    - "<alias>" → "<slug-target>": <reason>
    ...

Process each? Confirm to proceed.
```

After user confirmation, process each in order: merge → split → redirect.

### Step 2 — Per-signal precondition check

For each signal, run precondition checks first. Only proceed to execution if checks pass. Skip and log reason if not.

**If user passed `--skip-check`:** Skip precondition checks, proceed directly to execution. But must show warning before executing:

```
⚠️ --skip-check: skipping precondition checks, executing directly.
The following operations will proceed without condition verification and may cause irreversible wiki structural changes.
Confirm to continue?
```

User must confirm again before execution.

**If user passed `--auto`:** Skip per-operation "confirm execution?" prompts. Operations that pass precondition checks execute directly; those that don't pass are still skipped (unaffected by `--auto`). After executing all operations, output a summary. `--skip-check --auto` combined = fully automatic, process all signals without asking.

**This skill only defines precondition criteria and execution steps for the three operations.** Specific operation prompts are in their respective subsections — these prompts are for the independent agent dispatched to execute each operation.

**Key: after each operation completes, continue to the next — don't stop midway to ask "continue?".** The precondition pass/fail already gives the user the choice. The execution phase is batch-driven.

---

## User Direct Instruction Path

When the user directly expresses merge/split/redirect intent (e.g., "merge A and B", "split memory-management into two", "add alias Y for X"), don't use the signal file flow — use this path.

**Key difference from signal-driven path:**
- Signal-driven: rigid threshold, precondition failure → skip directly
- User direct instruction: **soft analysis**, give recommendation but allow user override

### Step A — Feasibility analysis (must run first)

Read the relevant Concept pages, analyze against the corresponding operation's precondition criteria.

**Merge analysis:**
1. Is A's problem a sub-dimension of B's problem?
2. Can A's content be fully expressed within B's page after merging? (no loss of independent discussion value)
3. Does A have any independent concerns or comparison dimensions not covered by B?

**Split analysis:**
1. Does the sub-topic already have ≥2 repos with different solutions? (count from the page)
2. Is there a real trade-off between solutions? (not one solution strictly dominates on all dimensions)
3. After splitting into an independent page, can the sub-topic still pass Concept admission criteria ①②③? (single-source definition in `schema/concept-criteria.md`)

**Redirect analysis:**
1. Does the target page exist?
2. Do both names genuinely point to the same problem space?

### Step B — Give judgment + recommendation

**If analysis passes all checks:**
```
Analysis: this operation is valid.
- <specific reason 1>
- <specific reason 2>
Recommend proceeding. Continue?
```
User confirms → execute per the corresponding operation (Merge/Split/Redirect) execution steps. Log: `[分析通过]`.

**If analysis shows issues:**
```
Analysis: this operation has risks.
- <specific risk 1>
- <specific risk 2>
Recommend against proceeding.

If you still wish to proceed, I will continue but will mark "user overrode precondition" in the evolution log.
Proceed anyway?
```
User insists → execute (evolution log marked `[⚠️ user overrode precondition]` + risk description).
User declines → abort.

**If analysis is clearly unreasonable:**
```
Analysis: this operation is not recommended.
- A discusses "<A's core problem>", B discusses "<B's core problem>"
  These are two entirely different problem spaces; merging would confuse the Concept page definition.
Strongly recommend against proceeding.
```
User still insists → execute (evolution log marked `[⚠️ user overrode precondition] [severe]`).

### Log format

```
[<ts>] evolve merge <slug-A> → <slug-B> [trigger: user direct instruction] [analysis passed]
[<ts>] evolve split <slug-src> → <new-slug> [trigger: user direct instruction] [⚠️ user overrode precondition] risk: <brief>
[<ts>] evolve redirect <alias> → <target> [trigger: user direct instruction] [analysis passed]
```

**Contrast: signal-driven path log format unchanged:**
```
[<ts>] evolve merge <slug-A> → <slug-B> [trigger: /ingest pause point 2]
```

---

## Operation A: Merge

### Preconditions (must check each before execution)

Read the source page `wiki/concepts/<slug-A>.md` and target page `wiki/concepts/<slug-B>.md`, check:

1. Does `<slug-A>`'s problem represent a sub-dimension of `<slug-B>`'s problem?
2. Can `<slug-A>`'s content be fully expressed within `<slug-B>`'s page after merging? (no loss of independent discussion value)
3. Does `<slug-A>` have any independent concerns or comparison dimensions not covered by `<slug-B>`?

**All three pass → proceed, show change preview, execute after user confirmation.**
**Any one fails → don't proceed, explain reason to user, skip this signal.**

### Change preview

```
Merge operation preview:

  Merge all content of [[<slug-A>]] into [[<slug-B>]]
  <slug-A> will become a redirect page

  Scope of impact:
  - Will append <N> repo solutions to <slug-B>
  - Will update <slug-B>'s comparison table (new comparison dimension)
  - <slug-A> will be rewritten as a redirect page
  - seeds/master.md corresponding entries marked merged_into

  Confirm execution?
```

### Execution (independent agent)

Dispatch an agent with the following prompt:

```
Your task is to merge two Concept pages into one.

## Input

- Source page: wiki/concepts/<slug-A>.md
- Target page: wiki/concepts/<slug-B>.md
- Merge reason: <description from evolve signal file>

## Validation check (must verify before executing)

Merge validity requires:
- <slug-A>'s problem is a sub-dimension of <slug-B>'s problem
- <slug-A>'s content can be fully expressed within <slug-B>'s page
- <slug-A> has no independent concerns or comparison dimensions absent from <slug-B>

If any condition fails, stop and explain why.

## Execution steps

1. Merge each repo's solutions from <slug-A> into the corresponding sections of <slug-B>
2. Update <slug-B>'s comparison table to include dimensions introduced by <slug-A>
3. Update <slug-B>'s evolution log with merge source and date
4. Rewrite <slug-A>.md as a redirect page:

   ---
   redirect_to: <slug-B>
   reason: <one sentence>
   date: <YYYY-MM-DD>
   ---
   # <slug-A original title>
   > This page has been merged into [[<slug-B>]]. Reason: <reason>

5. Update wiki/index.md Concepts table: remove <slug-A> row, update <slug-B> row
6. Update seeds/master.md, mark related entries merged_into: <slug-B>
7. Overwrite wiki/hot.md (update pending evolve signals count)
8. Append to wiki/log.md: [<timestamp>] evolve merge <slug-A> → <slug-B>

## Do not modify

Existing repo content in <slug-B> — only append, never overwrite.
```

---

## Operation B: Split

### Preconditions (must check each before execution)

Read the source page `wiki/concepts/<slug-src>.md`, check:

1. Does the sub-topic already have ≥2 repos with different solutions? (count from within the page)
2. Is there a real trade-off between solutions? (not one solution strictly dominates on all dimensions)
3. After splitting into an independent page, can the sub-topic still pass Concept admission criteria ①②③? (single-source definition in `schema/concept-criteria.md`)

**All three pass → proceed, show change preview, execute after user confirmation.**
**Any one fails → don't proceed, explain reason to user, skip this signal.**

### Change preview

```
Split operation preview:

  Split out new sub-Concept page [[<new-slug>]] from [[<slug-src>]]

  Scope of impact:
  - Will create wiki/concepts/<new-slug>.md (<N> repo solutions)
  - Will update <slug-src> (remove migrated content, retain summary and link)
  - seeds/master.md related entries marked split_to

  Confirm execution?
```

### Execution (independent agent)

Dispatch an agent with the following prompt:

```
Your task is to split a new sub-Concept page out of an existing Concept page.

## Input

- Source page: wiki/concepts/<slug-src>.md
- Split sub-topic: <sub-topic name>
- Split reason: <description from evolve signal file>

## Validation check (must verify before executing)

Split validity requires:
- The sub-topic has ≥2 repos with different solutions, with real trade-offs between them
- After splitting into an independent page, the sub-topic can still pass Concept admission criteria ①②③ (single-source definition in `schema/concept-criteria.md`):
  ① Multiple solutions: at least two different repos solve the same problem in clearly different ways.
     Note: if one solution dominates another on all trade-off dimensions after analysis, it doesn't qualify.
  ② Independent design space: this problem cannot be fully covered by an existing problem space —
     merging it in would cause its discussion dimensions to disappear and decision value to be lost.
  ③ Persistent trade-off: no silver bullet across different solutions —
     satisfying concern A increases the cost of satisfying concern B, and vice versa.
- The split sub-topic is not just a standalone description of one solution from the source page

If any condition fails, stop and explain why.

## Execution steps

1. Create wiki/concepts/<new-slug>.md
   Include repo solutions, concerns, and comparison table extracted from the source page
   Evolution log: "Split from [[<slug-src>]] on <date>"

2. Update source page:
   - Remove migrated detailed content
   - Keep summary (one sentence) with wikilink to the new page
   - Evolution log: "Split out [[<new-slug>]] on <date>"

3. Update wiki/index.md Concepts table: add <new-slug> row, update <slug-src> row
4. Update seeds/master.md, mark related entries split_to: <new-slug>
5. Overwrite wiki/hot.md (update pending evolve signals count)
6. Append to wiki/log.md: [<timestamp>] evolve split <slug-src> → <new-slug>
```

---

## Operation C: Redirect

### Preconditions

Check that the target page `wiki/concepts/<slug-target>.md` exists.

**Exists → pass.**
**Doesn't exist → fail, stop.**

### Change preview

```
Redirect operation preview:

  Will create redirect page [[<alias-slug>]] → [[<slug-target>]]

  Scope of impact:
  - Will create wiki/concepts/<alias-slug>.md (frontmatter + one line only)
  - No changes to <slug-target>

  Confirm execution?
```

### Execution (independent agent)

Dispatch an agent with the following prompt:

```
Your task is to create a redirect alias for a Concept page.

## Input

- Target page: wiki/concepts/<slug-target>.md
- Alias name: <alias-name>
- Reason: <why both names point to the same problem space>

## Execution steps

1. Create wiki/concepts/<alias-slug>.md:

   ---
   redirect_to: <slug-target>
   reason: <one sentence>
   date: <YYYY-MM-DD>
   ---
   # <alias-name>
   > This name redirects to [[<slug-target>]]. Reason: <reason>

2. Update wiki/index.md Concepts table: add <alias-slug> row (marked as redirect)
3. Overwrite wiki/hot.md (update pending evolve signals count)
4. Append to wiki/log.md: [<timestamp>] evolve redirect <alias-slug> → <slug-target>

## Do not modify any content in the target page
```

---

## Step 3 — Summary

After all signals are processed, output a summary.

## After Step 3

**REQUIRED SUB-SKILL:** If at least one evolution operation (merge/split/redirect) was executed, invoke `completion-gate` before claiming "complete". If all signals were skipped (no actual operations), skip completion-gate.

```
Evolve signal processing complete: <filename>

  ✅ Merge: <N> succeeded, <K> skipped
     - <slug-A> → <slug-B> ✅
     - <slug-C> → <slug-D> ⏭️ Reason: failed precondition #3
  ✅ Split: <N> succeeded, <K> skipped
  ✅ Redirect: <N> succeeded, <K> skipped

Skip reason details:
  - <slug-C> → <slug-D>: <slug-C>'s independent concern "<description>" has no corresponding dimension in <slug-D>; merging would lose discussion value.
```

## Edge Cases

- If source page is already a redirect page → skip, note "<slug-A> is already a redirect page, nothing to merge"
- If merge target page doesn't exist → stop, note "<slug-B> doesn't exist, verify slug correctness first"
- If split target already exists → prompt user, confirm whether to append or rename
- If signal file contains duplicate signals (multiple signals for the same slug) → process only the first

## Irreversibility Warning

Merge and split operations modify wiki page content. While git can roll back, confirm git state is clean before proceeding:

```bash
git status --short
```
