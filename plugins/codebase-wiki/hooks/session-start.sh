#!/usr/bin/env bash
# Inject wiki current state into Claude Code SessionStart context.
# Output follows Claude Code hookSpecificOutput.additionalContext format.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="$(dirname "$SCRIPT_DIR")"
HOT_FILE="$WIKI_ROOT/wiki/hot.md"
LOG_FILE="$WIKI_ROOT/wiki/log.md"
EVOLVE_DIR="$WIKI_ROOT/evolve-signals"

hot_content=""
if [ -f "$HOT_FILE" ]; then
  hot_content="$(cat "$HOT_FILE")"
fi

last_log_lines=""
if [ -f "$LOG_FILE" ]; then
  last_log_lines="$(tail -3 "$LOG_FILE" 2>/dev/null || true)"
fi

# Count pending evolve signals
evolve_count=0
if [ -d "$EVOLVE_DIR" ]; then
  evolve_count=$(ls "$EVOLVE_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
fi

# Build additionalContext safely: use python to produce valid JSON,
# avoiding shell interpolation of quotes/backslashes in content strings.
python3 - <<PYEOF
import json

context = """## Codebase Wiki Status

{hot}

### Recent Operations

{log}

### Health

Pending evolve signals: {evolve}""".format(
    hot="""$hot_content""",
    log="""$last_log_lines""",
    evolve="""$evolve_count""",
)

print(json.dumps({"additionalContext": context}))
PYEOF
