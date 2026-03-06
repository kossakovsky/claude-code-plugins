# Contributing

## Adding a Plugin

### Plugin Structure

Your plugin must follow this structure:

```
plugins/your-plugin/
├── .claude-plugin/
│   └── plugin.json       # Required: plugin manifest
├── commands/              # Slash commands (*.md)
├── skills/                # Skills (optional)
├── agents/                # Sub-agents (optional)
├── hooks/                 # Hooks (optional)
└── README.md              # Required: documentation
```

### plugin.json

Required fields:

```json
{
  "name": "your-plugin",
  "version": "1.0.0",
  "description": "What your plugin does"
}
```

Optional but recommended:

```json
{
  "name": "your-plugin",
  "version": "1.0.0",
  "description": "What your plugin does",
  "author": { "name": "your-github-username" },
  "license": "MIT"
}
```

### marketplace.json Entry

Add your plugin to the `plugins` array in `.claude-plugin/marketplace.json`:

```json
{
  "name": "your-plugin",
  "description": "What your plugin does",
  "version": "1.0.0",
  "source": "./plugins/your-plugin",
  "author": { "name": "your-github-username" },
  "category": "utilities",
  "tags": ["tag1", "tag2"]
}
```

Required fields: `name`, `source`, `description`, `version`. The `name` must match your plugin directory name and the `name` in `plugin.json`.

### Steps

1. Fork this repository
2. Create your plugin in `plugins/your-plugin/`
3. Add your plugin entry to `.claude-plugin/marketplace.json`
4. Ensure your plugin has a `README.md`
5. Open a Pull Request

### Local Validation

Before submitting, verify your plugin passes validation:

```bash
# Validate plugin structure
plugins/plugin-development/scripts/validate-plugin.sh
```

You can also use the `plugin-development` plugin to scaffold and validate your plugin interactively.

### PR Requirements

- `marketplace.json` includes your plugin entry with correct `source` path
- `plugin.json` is valid JSON with required fields (`name`, `version`, `description`)
- Plugin name is kebab-case and matches directory name
- `README.md` exists and describes installation and usage
- CI validation passes (`validate-plugins.yml`)

### Security Restrictions

Plugins must NOT:
- Exfiltrate user data (send files, environment variables, or secrets to external services)
- Execute destructive operations without user confirmation
- Modify system files outside the project directory
- Include obfuscated or minified code that hides functionality

### What Gets Reviewed

PRs are automatically reviewed by CI and Claude Code. Checks include:

- Plugin structure and manifest validity
- No duplicate plugin names in marketplace
- Directory name matches plugin name in plugin.json
- Security review of commands and hooks
- Plugin usefulness and quality
