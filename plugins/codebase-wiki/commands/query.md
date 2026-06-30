# /query — Knowledge Query

Answer questions using the wiki knowledge base. Follow the retrieval escalation chain — start cheap, escalate only as needed.

## Trigger

```
/query <question>
/query --repo react,vue <question>
```

## Wikilink Traversal (structural questions first)

If the question matches the following patterns, do wikilink traversal first rather than the Retrieval Escalation Chain:

- "What does X affect?" / "What would changing X impact?" / "X's blast radius"
- "Why does X exist?" / "Why is X designed this way?"
- "Which other repos also have X?" / "How do different repos approach X?"

### Why wikilink traversal suffices for these questions

Because entity pages are connected through concept pages — entity → concept → other entities.
Following this network shows you "what different choices other repos made on the same problem," which is exactly what structural questions are asking.

### Traversal steps

1. Identify keywords from the question, scan `wiki/repos/*/entities/` and `wiki/concepts/`:
   ```bash
   # Find entity pages by keyword (read frontmatter problem: field)
   grep -rl "关键词" wiki/repos/*/entities/ --include="*.md" | head -5
   ```

2. Read matching entity frontmatter (first 10 lines) — find the `problem:` field to filter by relevance

3. From relevant entities, follow wikilinks:
   - `[[concepts/<slug>]]` → read concept page → find other repos' entities via `[[repos/<name>/entities/<slug>]]`
   - This yields: same problem, different repos, different solutions → structural answer

4. If the traversal path found enough information → answer with provenance `^[file:line]`. If not enough → fall through to Retrieval Escalation Chain.

## Retrieval Escalation Chain

### Level 1 — Index Scan (cheapest)
Read `wiki/index.md`. If the question has obvious keyword matches in the Concepts table → go directly to the corresponding concept page.

### Level 2 — Section Grepping (moderate cost)
```bash
grep -n "^## \|^### " wiki/concepts/<slug>.md
```
Read only the most relevant sections of candidate concept pages, not the whole file.

### Level 3 — Full Page Read (most expensive, last resort)
Read the entire entity page or concept page — only when Levels 1-2 still leave unanswered questions.

## Post-Answer Content Accuracy Check

After producing the answer, if Level 3 source-code reading reveals information that is more accurate or more complete than what the Concept page (or Entity page) currently states, this triggers the **wiki knowledge freshness closed-loop protocol**:

- (a) Actively present the diff (old description → new description), inform the user of the discrepancy
- (b) After user confirmation, write the correction to the wiki page on the spot
- (c) After correction, regenerate the affected output
- (d) Log append: `[源码验证: <page> <section> 修正]`

## Archive Decision

After answering:

```
> Is this analysis worth archiving in the wiki?
> - A: Don't archive (answer already in existing pages, just a summary)
> - B: Supplement existing pages (found additions or corrections to existing Entity or Concept pages)
> - C: Create new Insight page (synthesis has standalone value)
```

### Option B — Supplement existing pages
Apply the content accuracy fix protocol above, then update `wiki/log.md`.

### Option C — Create new Insight page
- Write `wiki/insights/<YYYY-MM-DD>-<slug>.md` with frontmatter: `type: insight`, original question, generation date, source array, provenance_repos array
- Add wikilinks to relevant entities and concepts
- Append to `wiki/log.md` with `[query]` tag
- Update `wiki/index.md` `## Insights` section

### After B or C — completion-gate
Invoke `/completion-gate` as a REQUIRED SUB-SKILL before claiming completion.
