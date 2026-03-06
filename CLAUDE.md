# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Community marketplace of plugins for Claude Code. Plugins are installed via:
```
/plugin marketplace add kossakovsky/claude-code-plugins
/plugin install <plugin-name>@claude-code-plugins
```

## Validation

CI runs on push to main/develop and on PRs to main (`.github/workflows/validate-plugins.yml`):
- Validates `marketplace.json` structure and required fields
- Validates each plugin's `plugin.json` (valid JSON, required fields, kebab-case name)
- Checks for duplicate plugin names
- Verifies plugin directories and README.md exist

Local validation for plugin development:
```bash
# Validate plugin structure (used by plugin-development hook on Write/Edit)
plugins/plugin-development/scripts/validate-plugin.sh
```

PR review is automated via Claude Code Action (`.github/workflows/review-pr.yml`).

## Architecture

### Marketplace Registry

`.claude-plugin/marketplace.json` — central registry listing all plugins. Each entry requires: `name`, `source` (relative path like `./plugins/<name>`), `description`, `version`, `author.name`.

### Plugin Structure

Each plugin lives in `plugins/<name>/` and must contain:
- `.claude-plugin/plugin.json` — manifest with required fields: `name` (kebab-case), `version`, `description`
- `README.md` — documentation

Optional component directories:
- `commands/` — slash commands as `.md` files with YAML frontmatter (`description` field recommended)
- `skills/` — skill definitions
- `agents/` — sub-agent definitions as `.md` files
- `hooks/` — hooks configuration (`hooks.json`)

### Current Plugins

| Plugin | Purpose |
|--------|---------|
| `switch-provider` | Switch between AI providers (Anthropic, Z.AI, Kimi, MiniMax) |
| `plugin-development` | Scaffold, validate, and review plugins |
| `commit` | Smart git commits with conventional commit messages |
| `skill-creator` | Create skills with evals and benchmarks |

## PR Review Instructions

When reviewing a PR, check the following:

### Required Checks

1. **Plugin structure**: directory `plugins/<name>/` contains `.claude-plugin/plugin.json` and `README.md`
2. **plugin.json**: valid JSON with required fields (`name`, `version`, `description`, `author`)
3. **marketplace.json**: entry added with correct `source` path, no duplicate names
4. **Security**: commands and hooks contain no malicious code, no data exfiltration, no dangerous operations
5. **Usefulness**: plugin solves a real problem, is not spam or an empty shell

### Response Format

Use one of these statuses:
- **APPROVE** — everything looks good, ready to merge
- **NEEDS_CHANGES** — issues found, changes required (list specifics)
- **BLOCK** — critical security issues or structural violations
