---
description: "Create a git commit with a generated conventional commit message"
argument-hint: "[message]"
---

# Smart Git Commit

Create a git commit with a conventional commit message, either provided or auto-generated.

## Steps

1. **Check for provided message**: If an argument was provided, use it as the commit message directly and skip to step 6.

2. **Check working tree state**: Run `git status` to see the current state of the repository.

3. **Handle staging**:
   - If nothing is staged, show the unstaged changes and ask the user what to stage.
   - Suggest `git add -A` to stage everything, or let the user specify individual files.
   - Never stage files without explicitly showing what will be staged and getting confirmation.

4. **Analyze staged changes**: Run `git diff --staged` to understand what has been changed.

5. **Detect project commit style**: Run `git log --oneline -10` to see recent commit messages and adapt to the project's conventions.

6. **Determine change type**: Analyze the diff to classify the change as one of:
   - `feat` — new feature
   - `fix` — bug fix
   - `refactor` — code restructuring without behavior change
   - `docs` — documentation only
   - `chore` — maintenance, dependencies, config
   - `test` — adding or updating tests
   - `style` — formatting, whitespace, linting
   - `perf` — performance improvement
   - `ci` — CI/CD configuration
   - `build` — build system or external dependencies

7. **Generate commit message**: Create a message following the conventional commit format:
   ```
   type(scope): description
   ```
   - **type**: determined from the diff analysis above
   - **scope**: optional, inferred from the changed files or directories
   - **description**: concise summary of changes in imperative mood (e.g., "add user auth endpoint", not "added user auth endpoint")

8. **Present for approval**: Show the generated commit message and ask the user to approve, edit, or reject it.

9. **Execute commit**: If approved, run `git commit -m "<message>"`.

10. **Show result**: Display the commit output to confirm success.

## Important Rules

- Never force-push or amend commits without an explicit request from the user.
- Never stage files without showing what will be staged first.
- If there are no changes at all (nothing staged, nothing modified, no untracked files), inform the user and stop.
