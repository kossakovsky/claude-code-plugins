# Claude Code Community Marketplace

[![Validate Plugins](https://github.com/kossakovsky/claude-code-plugins/actions/workflows/validate-plugins.yml/badge.svg)](https://github.com/kossakovsky/claude-code-plugins/actions/workflows/validate-plugins.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Community marketplace of plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Claude Code plugins extend your CLI with new skills, slash commands, hooks, and agents. This marketplace is a single place where the community shares and discovers plugins — all installable with one command.

## Installation

Add the marketplace:

```bash
/plugin marketplace add kossakovsky/claude-code-plugins
```

Install any plugin:

```bash
/plugin install <plugin-name>@claude-code-plugins
```

## Plugins

| Plugin | Version | Category | Description |
|--------|---------|----------|-------------|
| [switch-provider](plugins/switch-provider/) | 1.0.0 | utilities | Switch Claude Code between AI providers (Anthropic, Z.AI, Kimi, MiniMax) |
| [plugin-development](plugins/plugin-development/) | 1.3.0 | developer-tools | Scaffold, validate, and submit Claude Code plugins |
| [commit](plugins/commit/) | 1.0.0 | developer-tools | Smart git commits with conventional commit messages |
| [skill-creator](plugins/skill-creator/) | 1.0.0 | developer-tools | Create and improve skills with evals and benchmarks |

## Create & Submit Your Plugin

Anyone can contribute a plugin to the marketplace via Pull Request. Every PR goes through automated CI validation and a Claude Code review before being merged.

The fastest way to create and submit a plugin:

```bash
# Install the plugin-development toolkit
/plugin install plugin-development@claude-code-plugins

# Scaffold a new plugin
/plugin-development:init my-plugin

# Add commands, skills, agents, hooks
/plugin-development:add-command my-command "What it does"

# Validate before submitting
/plugin-development:validate

# Submit to the marketplace via PR
/plugin-development:submit
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## License

MIT License — see [LICENSE](LICENSE) for details.
