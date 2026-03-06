# Claude Code Community Marketplace

[![Validate Plugins](https://github.com/kossakovsky/claude-code-plugins/actions/workflows/validate-plugins.yml/badge.svg)](https://github.com/kossakovsky/claude-code-plugins/actions/workflows/validate-plugins.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Community marketplace of plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Skills, commands, hooks, and agents — all installable with a single command.

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

| Plugin | Description |
|--------|-------------|
| [switch-provider](plugins/switch-provider/) | Switch Claude Code between AI providers (Anthropic, Z.AI, Kimi, MiniMax) with a single command |
| [plugin-development](plugins/plugin-development/) | Toolkit for creating, validating, and distributing Claude Code plugins |
| [commit](plugins/commit/) | Smart git commits with conventional commit message generation |
| [skill-creator](plugins/skill-creator/) | Create, test, and improve Claude Code skills with evals and benchmarks |

## Create Your Own Plugin

Anyone can contribute a plugin to the marketplace via Pull Request. Every PR goes through automated CI validation and a Claude Code review before being merged.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, or use the `plugin-development` plugin to scaffold your plugin interactively.

## License

MIT License — see [LICENSE](LICENSE) for details.
