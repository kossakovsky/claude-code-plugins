# /completion-gate — Completion Quality Gate

A shared quality gate that must be passed before any wiki write operation can be declared complete. Not a user-invoked skill — referenced by other skills as `REQUIRED SUB-SKILL` at completion.

## Trigger

```
(not user-invoked — referenced by other skills as REQUIRED SUB-SKILL at completion)
```

**Announce at start:** Execute silently. On a clean pass, output nothing to the user.

## Iron Law

```
NO COMPLETION CLAIMS BEFORE THE GATE IS CLEARED
```

Before claiming "operation complete," every item in this gate must be passed. Skipping any item = not complete.

## The Gate Function

```
BEFORE claiming any wiki operation is complete:

1. IDENTIFY: Which wiki files does this operation touch?
2. CHECK: Is each file in the correct state? (operation scope, not full wiki coverage)
3. VERIFY: Do logs and index reflect this operation?
4. GATE: All pass → declare complete. Any fails → fix and re-check.
```

## Non-Negotiable Checklist

### 1. Write Correctness

- [ ] If Entity pages were written → frontmatter has all 6 required fields (`type`, `repo`, `slug`, `problem`, `source_files`, `generated`)
- [ ] If Concept pages were written →
  - ① frontmatter `repos:` covers **all** repos discussed in the body? (body has `### repo-name` sections or wikilinks but frontmatter doesn't list it = coverage invisible → BLOCK)
  - ② For each frontmatter-listed repo, is there at least one `[[repos/<name>/entities/...]]` wikilink in the body? (repos declared in metadata with no wikilink evidence → WARN, log but don't block)
- [ ] If maintenance files were written (`index.md`, `log.md`, `hot.md`) → format matches spec
- [ ] Every fact claim in new/changed pages has at least one provenance reference `^[path:line]`

### 2. Incremental Wikilink Validation

- [ ] Every wikilink in files written by this operation resolves to an existing file
- [ ] For each new concept page: do source entity pages have backlinks added? (`**Associated Concepts**: [[concepts/<slug>]]`)
- [ ] For each updated concept page: if `repos:` gained a new repo, do that repo's entity pages have backlinks added?

### 3. Maintenance File Sync

- [ ] `wiki/log.md`: new entry appended at bottom, with correct format (`[timestamp] operation detail`)
- [ ] `wiki/hot.md`: overwritten with current status (last operation, active repos, concept count, pending signal count)
- [ ] `wiki/index.md`: if repos were added → Repos section updated. If concepts were created/merged → Concepts table updated. If views/insights were archived → Views or Insights section updated.

### 4. Cleanup

- [ ] No leftover `[源码验证:]` markers in commit messages or page bodies (these are transient during-edit markers, should be resolved)
- [ ] No "I'll do this later" / "TODO" / unfinished write promises in written content
- [ ] If the operation produced `evolve-signals/` files → remind user: "N evolve signals are pending in evolve-signals/"

## Red Flags

Do NOT claim completion if any of:
- ① A written file has broken wikilinks (target doesn't exist)
- ② A written file is missing required frontmatter fields
- ③ A written concept page has `repos:` in frontmatter that don't match the repos actually discussed in body
- ④ `wiki/log.md` or `wiki/hot.md` don't reflect this operation
- ⑤ Source entity pages lack backlinks to newly written concept pages
- ⑥ The operation produced artifacts outside the wiki directory without updating `.gitignore`

## When To Apply

| Operation | Gate invoked by |
|-----------|----------------|
| `/ingest` (write entities + concepts) | `/ingest` itself at completion |
| `/evolve-apply` (merge/split/redirect) | `/evolve-apply` itself at completion |
| `/compare` (archive as view → B or C) | `/compare` itself at completion |
| `/query` (archive as insight → B or C) | `/query` itself at completion |
| Any manual edit to wiki pages | Editor's responsibility to self-check |
