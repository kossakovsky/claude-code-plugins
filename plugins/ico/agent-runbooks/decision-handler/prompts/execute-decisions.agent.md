# Execute Decisions Agent Prompt

Your job: dispatch backup+delete for confirmed resources, tag exempt resources, and log extended observation requests.

## Input

Read:
- `{run_dir}/decision/user_decisions.json` - user decisions per resource
- `{run_dir}/confirm/phase5_decision.json` - filtered list of resources to delete

## For Each DELETE Decision

1. Collect resource_ids from the DELETE decisions into an array.

2. Dispatch the backup-creator using the Agent tool (subagent_type=general-purpose) to create final backups.
   Required params:
   - run_dir: `{run_dir}`
   - decision_id: value from phase5_decision.json (e.g. "confirm-20260609-001")
   - phase5_decision_file: `confirm/phase5_decision.json`
   - task_id: `{task_id}`
   - ssh_key_path: `{ssh_key_path}` (if available)

   Wait for backup-creator to complete and verify.

3. After backup confirmed, dispatch the resource-cleaner using the Agent tool (subagent_type=general-purpose) to execute the actual deletion.
   Required params:
   - run_dir: `{run_dir}`
   - phase5_decision_file: `confirm/phase5_decision.json`
   - resource_ids: [array of resource IDs to delete]

   Optional params (with defaults):
   - batch_size_max: 10
   - batch_interval_sec: 300
   - deletion_parallelism: 3
   - enable_eip_dns_check: true
   - dry_run: false

If backup-creator or resource-cleaner fails for a resource, record the error but continue with remaining DELETE resources.

## For Each KEEP_EXEMPT Decision

Tag the resource with exempt metadata:
- Write `{run_dir}/decision/exempt/exempt_{resource_id}.json` containing:
  - resource_id, exempt_duration, exempt_until (calculated from now + duration), reason
- If ssh_key_path is available, also tag the cloud resource directly
  (cloud provider tag: `zombie:exempt=true`, `zombie:exempt_until=<date>`)

## For Each EXTEND_OBSERVATION Decision

Notify the user that extended observation is needed. Log the extension request:
- Write `{run_dir}/decision/extend/extend_{resource_id}.json` containing:
  - resource_id, extend_days, new_observation_end, reason

## Output

Write `{run_dir}/decision/execution_results.json`. The output schema is defined in `schemas/execution-results.schema.json`.
