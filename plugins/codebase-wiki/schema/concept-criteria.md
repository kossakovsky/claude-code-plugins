# Concept Admission Criteria

**Version:** v1.0
**Role:** Determines whether a problem space entry should be promoted to an independent Concept page. Referenced by `/ingest` Step 3, `/evolve-apply` Split, and `/compare` Concept structure review — this is the single-source definition.

---

## Hard Thresholds (all three must pass)

### 1. Multiple Solutions

At least two different repos solve the same problem in clearly different ways.

Note: if after analysis one solution dominates another on all trade-off dimensions, this is not a genuine design trade-off — does not qualify.

### 2. Independent Design Space

This problem cannot be fully covered by an existing problem space — merging it in would cause its own discussion dimensions to disappear, and the Framework Builder would lose decision value on this problem.

### 3. Persistent Trade-off

No silver bullet across different solutions — satisfying Concern A increases the cost of satisfying Concern B, and vice versa.

---

## Auxiliary Criterion (does not veto if unmet; affects priority)

### 4. Sustainable Extensibility

New repos are likely to contribute new solutions to this problem in the future. If no new repos join long-term, trigger "downgrade" evolution recommendation.

---

## Four Case Types

| Case | Condition | Action |
|------|-----------|--------|
| **A** | Hits existing Concept (core problem is the same) | Append to existing Concept page |
| **B** | New problem space, passes ①②③ | Create new Concept page |
| **C** | Currently only one repo faces this | Enter seed bank (`seeds/master.md`); do not promote |
| **D** | Partially overlaps with existing Concept but doesn't fully match | Record as evolve signal in `evolve-signals/` |

---

## Few-shot Examples

### Example Domain 1: AI Agent Frameworks

Input Entities (cross-repo):

- **OpenClaw**: Agent (YAML config), Workflow (explicit orchestration), Memory (external context injection), ToolTimeout (per-tool YAML timeout config)
- **HermesAgent**: Agent (@agent decorator), EventBus (event-driven coordination), Memory (internal state sync), ToolTimeout (per-toolset timeout)

---

**Positive — "Agent Definition Style":**

1. At least two repos, different approaches: config-driven vs. decorator-driven. ✅
2. Independent design space: evaluation dimensions are declarative convenience vs. programming flexibility; does not share evaluation dimensions with "multi-Agent coordination." ✅
3. Persistent trade-off: config is simple but inflexible vs. programming freedom with higher barrier; no silver bullet. ✅
4. Sustainable extensibility: new frameworks will still make different choices on this question. ✅

Decision: ✅ Create new Concept page `agent-definition-style`

---

**Counter-example 1 — fails 1: single repo only**

Candidate group "HermesAgent SafeWriter pipeline protection":

1. Multiple solutions: ❌ Only HermesAgent has this; other repos have no corresponding Entity.

Decision: ❌ Enter seed bank for observation; does not qualify as a Concept

---

**Counter-example 2 — fails 2: not an independent design space**

Candidate group "Tool Execution Timeout Configuration":

1. Multiple solutions: OpenClaw uses per-tool YAML timeout; HermesAgent uses per-toolset timeout. ✅
2. Independent design space: ❌ "Timeout configuration" is a sub-dimension of the existing problem space "Tool Execution Safety & Control." Merging it in would not lose discussion dimensions.

Decision: ❌ Does not qualify; handle as sub-dimension of "Tool Execution Safety" Concept

---

**Counter-example 3 — fails 3: no genuine trade-off**

Candidate group "Structured Log Format":

1. Multiple solutions: OpenClaw uses plain text; HermesAgent uses structured JSON + auto-redaction. ✅
2. Independent design space: log format has its own evaluation dimensions. ✅
3. Persistent trade-off: ❌ Structured JSON dominates plain text on all concerns; this is not a mutually-constraining trade-off — one solution simply hasn't evolved yet.

Decision: ❌ Does not qualify; record plain-text format as historical note

---

**Counter-example 4 — fails 4 (auxiliary; does not veto but affects priority)**

Candidate group "Agent Process Startup Order":

1. ✅ 2. ✅ 3. ✅
4. Sustainable extensibility: ⚠️ As async runtimes proliferate, this problem space may converge quickly.

Decision: ⚠️ Create page tentatively; note "low extensibility expectation" in evolve signal file

---

### Example Domain 2: Embedded Databases

Input Entities (cross-repo):

- **SQLite**: B-Tree (storage structure), WAL (write-ahead log)
- **LevelDB**: LSM-Tree (storage structure), MemTable+SSTable (write pipeline)
- **RocksDB**: ColumnFamily, Compaction (compaction strategy), BloomFilter

---

**Positive — "Storage Engine Core Data Structure":**

1. B-Tree vs LSM-Tree, fundamentally different design philosophies. ✅
2. Independent evaluation dimensions from persistence strategy. ✅
3. Read-optimized vs. write-optimized; classic no-silver-bullet trade-off. ✅

Decision: ✅ Create new Concept page `storage-engine-data-structure`

---

**Counter-example — fails 1: single repo only**

Candidate group "Bloom Filter Strategy":

1. Multiple solutions: ❌ Only RocksDB has BloomFilter.

Decision: ❌ Enter seed bank for observation

---

## Criteria Use in Evolution

`/evolve-apply` Split reuses ①②③ for precondition checks — the split-out sub-topic must independently pass all three hard thresholds to be allowed.

`/compare` after completing a comparison uses these criteria to review the structural quality of involved Concepts: are there pages covering broadly divergent sub-topics (suggest split)? Are there pages that are essentially the same (suggest merge)?
