# writing-skills

Create, test, and bulletproof Claude Code skills using TDD methodology (RED-GREEN-REFACTOR). Based on [obra/superpowers](https://github.com/obra/superpowers) writing-skills.

## Installation

```
/plugin marketplace add kossakovsky/cc-plugins
/plugin install writing-skills@cc-plugins
```

## Usage

The skill is automatically available after installation. Invoke it when creating or editing skills:

```
/skill writing-skills
```

## What's Included

| File | Description |
|------|-------------|
| `SKILL.md` | Main skill - TDD-based skill creation methodology |
| `anthropic-best-practices.md` | Anthropic's official skill authoring guide |
| `persuasion-principles.md` | Psychology principles for bulletproofing skills against rationalization |
| `testing-skills-with-subagents.md` | Testing methodology with pressure scenarios |
| `graphviz-conventions.dot` | Graphviz style guide for flowcharts in skills |
| `render-graphs.js` | Script to render dot diagrams from SKILL.md to SVG |
| `examples/CLAUDE_MD_TESTING.md` | Worked example of testing CLAUDE.md documentation variants |

## Approach

Skills are treated as production code - no skill ships without failing tests first:

1. **RED** - Run pressure scenarios without the skill, document baseline failures
2. **GREEN** - Write minimal skill addressing those specific failures
3. **REFACTOR** - Close loopholes, add rationalization counters, re-verify

## License

MIT
