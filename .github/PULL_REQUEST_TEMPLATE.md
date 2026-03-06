> Tip: You can automate this entire process with `/plugin-development:submit`

## Plugin Submission

**Plugin name:** `your-plugin-name`
**Description:** Brief description of what your plugin does
**What problem does it solve?** Explain the use case

### Checklist

- [ ] Plugin directory: `plugins/<name>/`
- [ ] `.claude-plugin/plugin.json` with required fields (`name`, `version`, `description`)
- [ ] `README.md` with installation and usage instructions
- [ ] Entry added to `.claude-plugin/marketplace.json`
- [ ] Plugin name is kebab-case and matches directory name
- [ ] No security issues (no data exfiltration, no dangerous operations)

### Testing

- [ ] Validated with `/plugin-development:validate`
- [ ] Tested locally with `/plugin-development:test-local`
- [ ] All commands work as documented
