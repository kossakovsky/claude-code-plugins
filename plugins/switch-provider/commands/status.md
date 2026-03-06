---
description: Show current provider, models, and API key status
---

# Provider Status

Show the current AI provider configuration.

## Steps

1. **Read** `~/.claude/settings.json` using the Read tool

2. **Determine current provider** by checking `env.ANTHROPIC_BASE_URL`:
   - Not set or missing → **Anthropic** (native)
   - Contains `z.ai` → **Z.AI**
   - Contains `deepseek` → **DeepSeek**
   - Contains `moonshot` → **Kimi**
   - Contains `aliyuncs` → **Qwen**
   - Contains `minimax` → **MiniMax**
   - Other → **Custom** (show the URL)

3. **Display** the following information:
   - **Provider**: name of the current provider
   - **Base URL**: value of `ANTHROPIC_BASE_URL` (or "native" if not set)
   - **Max model**: value of `CLAUDE_CODE_MAX_MODEL` (or "default" if not set)
   - **Default model**: value of `CLAUDE_CODE_DEFAULT_MODEL` (or "default" if not set)
   - **Mini model**: value of `CLAUDE_CODE_MINI_MODEL` (or "default" if not set)
   - **API key**: show first 8 characters + "..." if `ANTHROPIC_AUTH_TOKEN` is set, or "not set"

4. **Check saved keys**: Read `~/.claude/provider-keys.json` if it exists, and list which providers have saved keys (just the provider names, not the keys themselves)
