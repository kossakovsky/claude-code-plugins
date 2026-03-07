# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Community marketplace of plugins for Claude Code. Plugins are installed via:
```
/plugin marketplace add kossakovsky/cc-plugins
/plugin install <plugin-name>@cc-plugins
```

## Validation

CI runs on push to main/develop and on PRs to main (`.github/workflows/validate-plugins.yml`):
- Validates `marketplace.json` structure and required fields
- Validates each plugin's `plugin.json` (valid JSON, required fields, kebab-case name)
- Checks for duplicate plugin names
- Verifies plugin directories and README.md exist

Local validation for plugin development:
```bash
/plugin-development:validate
```

Note: `plugins/plugin-development/scripts/validate-plugin.sh` is a hook script invoked automatically on Write/Edit — it cannot be run standalone.

PR review is automated via Claude Code GitHub App (auto-reviews all PRs using instructions below).

## Architecture

### Marketplace Registry

`.claude-plugin/marketplace.json` — central registry listing all plugins. Each entry requires: `name`, `source` (relative path like `./plugins/<name>`), `description`, `version`. Optional: `author.name`, `category`, `tags`, `keywords`.

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
| `switch-provider` | Switch Claude Code between AI providers (Anthropic, Z.AI, Kimi, MiniMax) with a single command |
| `plugin-development` | Scaffold, validate, review, and submit Claude Code plugins |
| `commit` | Smart git commits with conventional commit message generation |
| `skill-creator` | Create, improve, and measure skills with evals and benchmarks |

## PR Review Instructions

When reviewing a PR, evaluate against these 4 categories (score each 1-5):

### 1. Structure (blocking if < 3)
- `plugins/<name>/` directory exists
- `.claude-plugin/plugin.json` with `name` (kebab-case, matches directory), `version`, `description`
- `README.md` present with installation and usage sections

### 2. Marketplace Integration (blocking if < 3)
- Entry added to `marketplace.json` with correct `source` path
- No duplicate plugin names
- Category and tags present

### 3. Security (blocking if < 4)
- No data exfiltration patterns (sending files, env vars, secrets to external services)
- No dangerous/destructive operations without user confirmation
- No obfuscated or minified code that hides functionality
- No hardcoded secrets or API keys

### 4. Quality & Usefulness (blocking if < 2)
- Solves a real problem, not spam or empty shell
- Commands/skills have meaningful content
- Documentation is clear and accurate

### Response Format

**Score:** Structure X/5 | Integration X/5 | Security X/5 | Quality X/5
**Total:** XX/20

**Verdict:**
- **APPROVE** (16+) — everything looks good, ready to merge
- **NEEDS_CHANGES** (10-15) — issues found, list specifics
- **BLOCK** (<10 or any blocking criteria failed) — critical issues

**Details:** specific findings per category
