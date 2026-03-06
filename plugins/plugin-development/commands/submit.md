---
description: Submit a plugin to the Claude Code Community Marketplace via Pull Request
argument-hint: [plugin-path]
---

# Submit Plugin to Marketplace

Guide the user through submitting their plugin to the community marketplace (`kossakovsky/claude-code-plugins`).

## Arguments

- `$1` (optional): Path to the plugin directory. If not provided, detect from current directory.

## Instructions

### Step 1: Locate the Plugin

1. If `$1` is provided, use that path
2. Otherwise, look for `.claude-plugin/plugin.json` in the current directory or parent directories
3. If not found, ask the user which plugin to submit

Read the plugin's `.claude-plugin/plugin.json` and `README.md`.

### Step 2: Validate the Plugin

Run the same checks as `/plugin-development:validate`:

- `.claude-plugin/plugin.json` exists and is valid JSON
- Required fields present: `name` (kebab-case), `version`, `description`
- `README.md` exists with installation and usage sections
- At least one component directory (commands/, skills/, agents/, or hooks/)
- No security issues (no hardcoded secrets, no data exfiltration patterns)

If validation fails, show errors and stop. The user must fix issues before submitting.

### Step 3: Generate Marketplace Entry

Using data from `plugin.json`, generate a marketplace entry:

```json
{
  "name": "<from plugin.json>",
  "description": "<from plugin.json>",
  "version": "<from plugin.json>",
  "source": "./plugins/<name>",
  "author": { "name": "<from plugin.json or ask user>" },
  "category": "<ask user to choose>",
  "tags": ["<from plugin.json keywords or ask user>"]
}
```

Available categories: `utilities`, `developer-tools`, `productivity`, `ai-tools`, `integrations`.

Show the generated entry to the user for confirmation.

### Step 4: Check Prerequisites

Check if `gh` CLI is available:

```bash
gh --version
```

**If `gh` is available:** Offer automated submission (Step 5a).
**If `gh` is not available:** Provide manual instructions (Step 5b).

### Step 5a: Automated Submission (with `gh` CLI)

Ask the user for confirmation before each step.

1. **Fork the repository:**
   ```bash
   gh repo fork kossakovsky/claude-code-plugins --clone=true
   ```
   If already forked, clone the existing fork:
   ```bash
   gh repo clone <user>/claude-code-plugins
   ```

2. **Create a branch:**
   ```bash
   cd claude-code-plugins
   git checkout -b add-plugin/<plugin-name>
   ```

3. **Copy plugin files:**
   ```bash
   cp -r <plugin-path> plugins/<plugin-name>/
   ```

4. **Update marketplace.json:** Read the existing `.claude-plugin/marketplace.json`, add the new entry to the `plugins` array, and write it back.

5. **Commit and push:**
   ```bash
   git add plugins/<plugin-name>/ .claude-plugin/marketplace.json
   git commit -m "feat: add <plugin-name> plugin"
   git push -u origin add-plugin/<plugin-name>
   ```

6. **Create Pull Request:**
   ```bash
   gh pr create \
     --repo kossakovsky/claude-code-plugins \
     --title "feat: add <plugin-name> plugin" \
     --body "$(cat <<'EOF'
   ## Plugin Submission

   **Plugin name:** `<plugin-name>`
   **Description:** <description from plugin.json>

   ### Checklist

   - [x] Plugin directory: `plugins/<name>/`
   - [x] `.claude-plugin/plugin.json` with required fields (`name`, `version`, `description`)
   - [x] `README.md` with installation and usage instructions
   - [x] Entry added to `.claude-plugin/marketplace.json`
   - [x] Plugin name is kebab-case and matches directory name
   - [x] No security issues (no data exfiltration, no dangerous operations)
   EOF
   )"
   ```

7. **Show the PR URL** to the user and explain next steps:
   - CI will run automated validation
   - Claude Code will perform an automated review
   - The maintainer will review and merge if everything looks good

### Step 5b: Manual Submission (without `gh` CLI)

Provide clear step-by-step instructions:

```
To submit your plugin to the marketplace:

1. Fork: https://github.com/kossakovsky/claude-code-plugins

2. Clone your fork:
   git clone https://github.com/<your-username>/claude-code-plugins
   cd claude-code-plugins

3. Create a branch:
   git checkout -b add-plugin/<plugin-name>

4. Copy your plugin:
   cp -r <plugin-path> plugins/<plugin-name>/

5. Add to marketplace.json:
   <show the generated entry and where to insert it>

6. Commit and push:
   git add plugins/<plugin-name>/ .claude-plugin/marketplace.json
   git commit -m "feat: add <plugin-name> plugin"
   git push -u origin add-plugin/<plugin-name>

7. Open a Pull Request:
   https://github.com/kossakovsky/claude-code-plugins/compare

   Use the PR template to fill in your submission details.
```

### Step 6: Post-Submission

Inform the user:

```
Your plugin has been submitted!

What happens next:
1. CI runs automated validation (structure, manifest, duplicates)
2. Claude Code performs an automated security and quality review
3. The maintainer reviews and merges approved submissions

You can track your PR at: <PR URL>
```

## Notes

- Never push to the main repository directly — always via fork and PR
- The PR template at `.github/PULL_REQUEST_TEMPLATE.md` is used automatically
- All marketplace entries require `name`, `source`, `description`, `version`
- Plugin name must be kebab-case and match the directory name
