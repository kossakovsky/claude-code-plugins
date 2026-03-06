---
description: Switch to MiniMax provider
argument-hint: "[api-key]"
---

# Switch to MiniMax

Switch Claude Code to use MiniMax as the AI provider.

## Provider Config

- **ANTHROPIC_BASE_URL**: `https://api.minimax.io/anthropic`
- **ANTHROPIC_DEFAULT_OPUS_MODEL**: `MiniMax-M2.5`
- **ANTHROPIC_DEFAULT_SONNET_MODEL**: `MiniMax-M2.5`
- **ANTHROPIC_DEFAULT_HAIKU_MODEL**: `MiniMax-M2.5`
- **ANTHROPIC_SMALL_FAST_MODEL**: `MiniMax-M2.5`

## Steps

1. **Resolve API key** (in order of priority):
   a. If an argument was provided, use it as the API key
   b. Read `~/.claude/provider-keys.json` — if it exists and has a `minimax` key, use it
   c. Read `~/.claude/settings.json` — if `env.ANTHROPIC_AUTH_TOKEN` exists and `env.ANTHROPIC_BASE_URL` contains `minimax`, reuse the existing key
   d. If no key found, ask the user to provide their MiniMax API key

2. **Read** `~/.claude/settings.json` using the Read tool

3. **Update** the `env` section with:
   ```json
   {
     "ANTHROPIC_AUTH_TOKEN": "<resolved-api-key>",
     "ANTHROPIC_BASE_URL": "https://api.minimax.io/anthropic",
     "ANTHROPIC_DEFAULT_OPUS_MODEL": "MiniMax-M2.5",
     "ANTHROPIC_DEFAULT_SONNET_MODEL": "MiniMax-M2.5",
     "ANTHROPIC_DEFAULT_HAIKU_MODEL": "MiniMax-M2.5",
     "ANTHROPIC_SMALL_FAST_MODEL": "MiniMax-M2.5"
   }
   ```

4. **Write** the updated settings back to `~/.claude/settings.json`

5. **Confirm** the switch and tell the user: **Restart Claude Code to apply changes.**
