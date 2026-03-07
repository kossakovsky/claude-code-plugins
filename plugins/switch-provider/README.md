# switch-provider

Switch Claude Code between AI providers (Anthropic, Z.AI, Kimi, MiniMax) with a single command.

## Installation

```bash
/plugin marketplace add kossakovsky/cc-plugins
/plugin install switch-provider@cc-plugins
```

## Usage

Switch to a provider:

```bash
/switch-provider:anthropic          # Switch back to native Anthropic
/switch-provider:zai                # Switch to Z.AI
/switch-provider:kimi               # Switch to Kimi (Moonshot)
/switch-provider:minimax            # Switch to MiniMax
```

Optionally pass API key as argument:

```bash
/switch-provider:zai your-api-key
```

Utility commands:

```bash
/switch-provider:status             # Show current provider and models
/switch-provider:setup              # Configure and save API keys
```

## Supported Providers

| Provider | Base URL | Models |
|----------|----------|--------|
| Anthropic | native | default (claude-opus-4-6, claude-sonnet-4-6, etc.) |
| Z.AI | `https://api.z.ai/api/anthropic` | glm-5 / glm-4.7 / glm-4.5-air |
| Kimi | `https://api.moonshot.cn/anthropic` | kimi-k2.5 |
| MiniMax | `https://api.minimax.io/anthropic` | MiniMax-M2.5 |

## How It Works

Each provider command updates `~/.claude/settings.json`:
- Sets `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL` in the `env` section
- Configures model overrides via `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, and `ANTHROPIC_SMALL_FAST_MODEL`
- API keys are read from the command argument, `~/.claude/provider-keys.json`, existing settings, or prompted interactively

## Key Storage

Use `/switch-provider:setup` to save API keys to `~/.claude/provider-keys.json` (chmod 600). Keys are stored per-provider and reused automatically when switching.

## License

MIT
