---
description: Switch to Qwen (Alibaba) provider
argument-hint: "[api-key]"
---

# Switch to Qwen

Switch Claude Code to use Qwen (Alibaba) as the AI provider.

## Provider Config

- **ANTHROPIC_BASE_URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **CLAUDE_CODE_MAX_MODEL**: `qwen-max`
- **CLAUDE_CODE_DEFAULT_MODEL**: `qwen-plus`
- **CLAUDE_CODE_MINI_MODEL**: `qwen-turbo`

## Steps

1. **Resolve API key** (in order of priority):
   a. If an argument was provided, use it as the API key
   b. Read `~/.claude/provider-keys.json` — if it exists and has a `qwen` key, use it
   c. Read `~/.claude/settings.json` — if `env.ANTHROPIC_AUTH_TOKEN` exists and `env.ANTHROPIC_BASE_URL` contains `aliyuncs`, reuse the existing key
   d. If no key found, ask the user to provide their Qwen API key

2. **Read** `~/.claude/settings.json` using the Read tool

3. **Update** the `env` section with:
   ```json
   {
     "ANTHROPIC_AUTH_TOKEN": "<resolved-api-key>",
     "ANTHROPIC_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
     "CLAUDE_CODE_MAX_MODEL": "qwen-max",
     "CLAUDE_CODE_DEFAULT_MODEL": "qwen-plus",
     "CLAUDE_CODE_MINI_MODEL": "qwen-turbo"
   }
   ```

4. **Write** the updated settings back to `~/.claude/settings.json`

5. **Confirm** the switch and tell the user: **Restart Claude Code to apply changes.**
