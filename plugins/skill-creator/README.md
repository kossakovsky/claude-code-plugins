# skill-creator

Create, modify, and improve Claude Code skills. Originally from [anthropics/skills](https://github.com/anthropics/skills).

## Installation

```bash
/plugin marketplace add kossakovsky/cc-plugins
/plugin install skill-creator@cc-plugins
```

## Usage

The skill-creator is a **skill resource** (not a slash command). It activates automatically when you ask Claude Code to create or improve a skill:

```
"Create a skill that generates unit tests for Python code"
"Improve my debugging skill to handle async errors better"
"I want to make a skill for code review"
```

Once activated, the skill guides you through an interactive workflow -- you describe your idea in plain text, and Claude Code handles the structure.

## Workflow

1. **Capture intent** -- Claude interviews you to understand what the skill should do and when it should trigger
2. **Write SKILL.md** -- generates the skill file with proper frontmatter, progressive disclosure, and writing patterns
3. **Test** -- runs eval test cases with and without the skill to measure effectiveness
4. **Iterate** -- improves the skill based on test results until it performs well
5. **Optimize description** -- tunes the trigger description for accurate activation

Advanced features include blind A/B comparison between skill versions and benchmark tracking across iterations.

## Included

- `SKILL.md` -- comprehensive skill creation guide (~440 lines), fully self-contained with no external script dependencies
- `references/schemas.md` -- JSON schemas for evals, grading, benchmarks, and other data structures

## License

MIT
