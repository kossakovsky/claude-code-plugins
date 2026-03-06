---
description: Configure and save API keys for providers
argument-hint: "[provider]"
---

# Setup Provider Keys

Configure and save API keys for providers to `~/.claude/provider-keys.json`.

## Steps

1. **Read** existing keys from `~/.claude/provider-keys.json` if the file exists (use Read tool, handle file not found gracefully)

2. **Determine which provider to configure**:
   - If an argument was provided (e.g., `deepseek`), configure that provider
   - If no argument, ask the user which provider(s) they want to configure. Options: `zai`, `deepseek`, `kimi`, `qwen`, `minimax`

3. **For each provider to configure**:
   - Ask the user for their API key
   - Add or update the key in the keys object under the provider name

4. **Write** the updated keys to `~/.claude/provider-keys.json`:
   ```json
   {
     "zai": "key-here",
     "deepseek": "sk-key-here",
     "kimi": "sk-key-here",
     "qwen": "sk-key-here",
     "minimax": "key-here"
   }
   ```

5. **Set permissions** using Bash: `chmod 600 ~/.claude/provider-keys.json`

6. **Confirm** which providers were configured and remind the user they can now switch with `/switch-provider:<provider>`
