---
description: Switch to native Anthropic API (remove provider overrides)
---

# Switch to Anthropic

Switch Claude Code back to the native Anthropic API by removing provider environment variables.

## Steps

1. Read `~/.claude/settings.json` using the Read tool
2. Parse the JSON content
3. Remove the following keys from the `env` section (if they exist):
   - `ANTHROPIC_AUTH_TOKEN`
   - `ANTHROPIC_BASE_URL`
   - `ANTHROPIC_DEFAULT_OPUS_MODEL`
   - `ANTHROPIC_DEFAULT_SONNET_MODEL`
   - `ANTHROPIC_DEFAULT_HAIKU_MODEL`
   - `ANTHROPIC_SMALL_FAST_MODEL`
4. Write the updated settings back to `~/.claude/settings.json`
5. Confirm the switch and tell the user: **Restart Claude Code to apply changes.**
