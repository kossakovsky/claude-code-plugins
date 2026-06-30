# codebase-wiki

> A growing markdown directory maintained by LLM — not a graph database.

A [Claude Code](https://claude.ai/code) plugin that turns source code repositories into a **living, cross-referenced knowledge base**. It implements the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern by Andrej Karpathy.

## Install

```
/plugin marketplace add kossakovsky/cc-plugins
/plugin install codebase-wiki@cc-plugins
```

Or install standalone:

```
/plugin marketplace add myl17/codebase-wiki
/plugin install codebase-wiki@codebase-wiki
```

## What it does

Each time you ingest a repo, the LLM reads the source, extracts structural modules (**Entities**), maps them to cross-repo design questions (**Problem Spaces**), and writes or updates **Concept** pages with comparison tables, wikilinks, and source provenance. The `[[wikilink]]` network **is** the graph — open it in Obsidian to see the knowledge structure directly.

## Skills

| Skill | Description |
|-------|-------------|
| `/ingest` | Read source → extract entities → map problem spaces → write/update concept pages |
| `/query` | Answer questions via wikilink traversal + 3-level retrieval escalation |
| `/compare` | Cross-repo comparison: Concept → Entity → Source code |
| `/lint` | Full wiki health check: wikilinks, frontmatter, orphans, provenance |
| `/evolve-apply` | Wikipedia-style concept evolution: merge, split, redirect |

## Quick Start

```
/ingest /path/to/your/repo my-repo-name
```

After ingest, open `wiki/` in Obsidian with Graph View to see the wikilink network. Ingest a second repo in the same domain and it will update existing Concept pages with comparisons.

## Documentation

See the [GitHub repo](https://github.com/myl17/codebase-wiki) for full documentation.

## License

MIT
