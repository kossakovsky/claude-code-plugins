# skill-creator

Create, modify, and improve Claude Code skills. Originally from [anthropics/skills](https://github.com/anthropics/skills).

## Installation

```bash
/plugin marketplace add kossakovsky/claude-code-plugins
/plugin install skill-creator@claude-code-plugins
```

## What It Does

The skill-creator activates automatically when you want to create or improve a Claude Code skill. It guides you through:

1. **Capturing intent** -- understanding what the skill should do and when it should trigger
2. **Writing the SKILL.md** -- structured guidance on frontmatter, progressive disclosure, and writing patterns
3. **Testing** -- running eval test cases with and without the skill
4. **Iterating** -- improving based on feedback until the skill works well
5. **Description optimization** -- tuning triggering accuracy

## Included

- `SKILL.md` -- comprehensive skill creation guide (~480 lines)
- `references/schemas.md` -- JSON schemas for evals, grading, benchmarks, and other data structures

## License

MIT
