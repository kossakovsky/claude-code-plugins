# Deliver Final Report Agent Prompt

Your job: generate a cost optimization report as Markdown and deliver it to the user.

## Input

Read:
- `{run_dir}/decision/merged_view.json` - all candidate resource profiles
- `{run_dir}/decision/user_decisions.json` - user decisions
- `{run_dir}/decision/execution_results.json` - execution outcomes

## Generate Final Report

Use the Write tool to create a well-formatted Markdown cost optimization report.

The report should cover:

### Summary Cards
- Total resources scanned
- Confirmed for deletion (count + monthly cost savings)
- Kept as exempt (count)
- Extended observation (count)
- Total monthly cost savings
- Projected yearly cost savings

### Per-Resource Table
For every candidate resource, show:
- Resource name, type, environment
- Monthly cost
- Observation result
- User decision
- Execution status (deleted / exempt / pending)
- Cost saved (if deleted)

### Recommendations
Suggested next steps:
- Review exempt resources at their expiry dates
- Schedule follow-up observation review for extended resources
- Run next zombie scan cycle (recommended cadence)
- Any resources needing manual follow-up

## Deliver

Present the report directly in the chat as Markdown. Also write a machine-readable summary to `{run_dir}/decision/final_summary.json`. The output schema is defined in `schemas/final-summary.schema.json`.
