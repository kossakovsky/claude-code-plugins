# commit

Smart git commits with conventional commit message generation.

## Installation

```bash
/plugin marketplace add kossakovsky/cc-plugins
/plugin install commit@cc-plugins
```

## Usage

Generate a commit message automatically:

```bash
/commit:commit
```

Use a custom commit message:

```bash
/commit:commit "feat: add new feature"
```

## How It Works

1. Analyzes staged changes with `git diff --staged`
2. Detects the project's commit style from recent history
3. Determines the change type (feat, fix, refactor, etc.)
4. Generates a conventional commit message
5. Asks for approval before committing

## Conventional Commits Format

Messages follow the format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `style`, `perf`, `ci`, `build`

## License

MIT
