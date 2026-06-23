# Generate Decision Report Agent Prompt

Your job: present all Phase 2 findings to the user via a clear Markdown report and collect per-resource decisions.

## Input

Read the merged view from `{run_dir}/decision/merged_view.json`. This file contains every candidate resource with its deep scan profile, observation result, cost data, and AI preliminary recommendation.

## Present to User

Use the Write tool to produce a well-formatted Markdown report showing every candidate resource.

For each resource, show:
- Resource name/ID, type, cloud provider
- Spec + actual utilization (highlight idleness)
- Monthly cost
- Owner + business context
- Observation result (days isolated, alerts, complaints)
- AI recommendation (delete / keep / extend_observation) with reason

## Collect User Decisions

The user must decide for each resource:

| Decision | Meaning | Required fields |
|----------|---------|-----------------|
| **DELETE** | Confirm deletion | (none) |
| **KEEP_EXEMPT** | Keep resource, exempt from cleanup | exempt_duration (e.g., "30d", "90d", "permanent") |
| **EXTEND_OBSERVATION** | Extend isolation for more data | extend_days (e.g., 7, 14, 30) |

## Output

Write `{run_dir}/decision/user_decisions.json` containing all user decisions. The output schema is defined in `schemas/user-decisions.schema.json`.
