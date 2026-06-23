---
name: decision-handler
description: >-
  Final phase of the zombie resource cleanup workflow. Presents all Phase 2
  findings (deep scan + observation) to the user for final human decision,
  executes confirmed deletions, and delivers a cost savings report.
  
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Workspace root directory for file passing between agents |
| task_id | string | Yes | Task ID for progress tracking |
| ssh_key_path | string | No | SSH key path for cloud provider access |

## Execution Flow

### Task Context

Before starting execution, initialize `task_context.json`:

```json
{
  "task_id": "<task_id from input>",
  "current_step": 0,
  "current_step_id": null,
  "status": "running",
  "steps": {
    "load_and_merge": "pending",
    "generate_decision_report": "pending",
    "write_phase5_decision": "pending",
    "execute_decisions": "pending",
    "deliver_final_report": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: load_and_merge

**Type:** agent
**Description:** Load all Phase 2 outputs and merge into a unified per-resource view.
Sorted by cost descending for prioritization.


## Input Files
- `analysis/deep_scan_{resource_id}.json`
- `observe/observation_{resource_id}.json`
- `observe/observation_batch_summary.json`

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Load and merge all Phase 2 outputs into a single unified view.

## Inputs to read

1. **Deep scan profiles** - glob `{run_dir}/analysis/deep_scan_*.json`
   Each file contains detailed technical profile for one candidate resource:
   - resource_id, resource_type, entity_type, cloud_provider
   - spec (CPU/memory/disk), actual_utilization
   - running_processes, open_ports, installed_packages
   - owner_detail, team_lead_id
   - business_context (application, system, scheduled_tasks)
   - cost (monthly, yearly - either from cloud billing or estimated)
   - tags, environment

2. **Observation reports** - glob `{run_dir}/observe/observation_*.json`
   Each file contains isolation observation results:
   - resource_id
   - isolation_method, isolation_start/end dates
   - observation_result: passed / failed / uncertain
   - alert_count, complaint_count
   - anomaly_events (if any), rollback_triggered
   - observation_period_days

3. **Observation batch summary** - `{run_dir}/observe/observation_batch_summary.json`
   High-level summary of all observations (results histogram, rollback count).

## Merge logic

For each unique resource_id found across deep scan files:
  - If both deep_scan + observation exist: merge full profile
  - If only deep_scan exists (observation not yet done): mark observation_result = "pending"
  - If only observation exists (deep scan missing): include with available data, mark spec = "incomplete"

## Recommendation logic

For each resource, generate an AI recommendation:
  - **DELETE**: observation_result = "passed" (no alerts, no complaints, no rollback)
  - **KEEP**: observation_result = "failed" OR resource has active business use
  - **EXTEND_OBSERVATION**: observation_result = "uncertain" (some alerts but inconclusive)

This is a preliminary recommendation - the human makes the final call.

Sort resources by cost.monthly descending (most expensive first).

## Self-validation

Before writing the output, verify:
  - total_candidates matches resources array length
  - All resources have required fields: resource_id, resource_type, cloud_provider, cost, observation, recommendation, recommendation_reason
  - total_monthly_cost equals sum of all resources monthly cost
  - observation_summary counts equal total_candidates
  - Resources sorted by cost.monthly descending

If any validation fails, fix the issue and re-validate.


**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/deep-scan.schema.json`
   - Schema: `schemas/observation-input.schema.json`
   - Schema: `schemas/observation-batch-summary-input.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `decision/merged_view.json`

## Output
- **Schema:** schemas/merged-view.schema.json
  - **File:** decision/merged_view.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"load_and_merge"`
- Set `steps.load_and_merge` to `"completed"`
### Step 2: generate_decision_report

**Type:** agent
**Description:** Present merged findings to the user and collect per-resource decisions.
Use the Write tool to produce a Markdown report in the chat.


## Input Files
- `decision/merged_view.json` (from Step load_and_merge, schema: schemas/merged-view.schema.json)

## Execution
Launch an independent agent with the following prompt file:

**Prompt file:** `$PLUGINS/ico/skills/decision-handler/prompts/generate-decision-report.agent.md`
**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/merged-view.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `decision/user_decisions.json`

## Output
- **Schema:** schemas/user-decisions.schema.json
  - **File:** decision/user_decisions.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"generate_decision_report"`
- Set `steps.generate_decision_report` to `"completed"`
### Step 3: write_phase5_decision

**Type:** inline
**Description:** Produce the handoff file that backup-creator and resource-cleaner
read as their primary input.


## Input Files
- `decision/merged_view.json` (from Step load_and_merge, schema: schemas/merged-view.schema.json)
- `decision/user_decisions.json` (from Step generate_decision_report, schema: schemas/user-decisions.schema.json)

## Execution
Follow these instructions:

Read `{run_dir}/decision/merged_view.json` and
`{run_dir}/decision/user_decisions.json`.

Filter merged resources to only those with a user decision of "delete",
then write the handoff file that downstream agents consume.

decision_id format: `confirm-{YYYYMMDD}-{3-digit sequence}` (e.g. confirm-20260609-001).
Populate each resource entry from merged_view.json fields.
resource_metadata should include spec, actual_utilization, owner_detail,
business_context, and tags from the merged view.

Self-validate before writing:
  - decision_id matches pattern confirm-YYYYMMDD-NNN
  - total_resources equals resources array length
  - All resources have required fields
  - resource_metadata is present and non-empty for each resource


Write the output to the specified output file.

## Output
- **Schema:** schemas/phase5-decision.schema.json
  - **File:** confirm/phase5_decision.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"write_phase5_decision"`
- Set `steps.write_phase5_decision` to `"completed"`
### Step 4: execute_decisions

**Type:** agent
**Description:** Execute the user's decisions: dispatch backup+delete for confirmed
resources, tag exempt resources, and notify for extended observation.


## Input Files
- `decision/user_decisions.json` (from Step generate_decision_report, schema: schemas/user-decisions.schema.json)
- `confirm/phase5_decision.json` (from Step write_phase5_decision, schema: schemas/phase5-decision.schema.json)

## Execution
Launch an independent agent with the following prompt file:

**Prompt file:** `$PLUGINS/ico/skills/decision-handler/prompts/execute-decisions.agent.md`
**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/user-decisions.schema.json`
   - Schema: `schemas/phase5-decision.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `decision/execution_results.json`

## Output
- **Schema:** schemas/execution-results.schema.json
  - **File:** decision/execution_results.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"execute_decisions"`
- Set `steps.execute_decisions` to `"completed"`
### Step 5: deliver_final_report

**Type:** agent
**Description:** Generate and deliver the final cost optimization report as Markdown
using the Write tool. Also write a machine-readable summary.


## Input Files
- `decision/merged_view.json` (from Step load_and_merge, schema: schemas/merged-view.schema.json)
- `decision/user_decisions.json` (from Step generate_decision_report, schema: schemas/user-decisions.schema.json)
- `decision/execution_results.json` (from Step execute_decisions, schema: schemas/execution-results.schema.json)

## Execution
Launch an independent agent with the following prompt file:

**Prompt file:** `$PLUGINS/ico/skills/decision-handler/prompts/deliver-final-report.agent.md`
**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/merged-view.schema.json`
   - Schema: `schemas/user-decisions.schema.json`
   - Schema: `schemas/execution-results.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `decision/final_summary.json`

## Output
- **Schema:** schemas/final-summary.schema.json
  - **File:** decision/final_summary.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"deliver_final_report"`
- Set `steps.deliver_final_report` to `"completed"`