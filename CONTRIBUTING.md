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

Minimum required fields:

```json
{
  "name": "your-plugin",
  "version": "1.0.0",
  "description": "What your plugin does",
  "author": { "name": "your-github-username" },
  "license": "MIT"
}
```

### Steps

1. Fork this repository
2. Create your plugin in `plugins/your-plugin/`
3. Add your plugin entry to `.claude-plugin/marketplace.json`
4. Ensure your plugin has a `README.md`
5. Open a Pull Request

### PR Requirements

- `marketplace.json` includes your plugin entry with correct `source` path
- `plugin.json` is valid JSON with required fields (`name`, `version`, `description`, `author`)
- `README.md` exists and describes installation and usage
- CI validation passes (`validate-plugins.yml`)

### What Gets Reviewed

PRs are automatically reviewed by CI and Claude. Checks include:

- Plugin structure and manifest validity
- No duplicate plugin names in marketplace
- Security review of commands and hooks
- Plugin usefulness and quality
