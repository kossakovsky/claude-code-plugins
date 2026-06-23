---
name: orchestrator
description: >-
  Cloud infrastructure cost optimization lifecycle -- identifies idle and underutilized resources, orchestrates safe isolation and observation, and manages the approve-decommission workflow to reduce cloud spend. Trigger phrases: "cost optimization", "infra cost", "zombie resources", "idle resources", "reduce cloud cost", "cloud waste".
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Workspace root directory |
| ssh_key_path | string | No | SSH key path for cloud API calls |
| task_id | string | Yes | Task ID for progress tracking |

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
    "confirm_scope": "pending",
    "confirm_connection": "pending",
    "confirm_monitoring": "pending",
    "generate_intent": "pending",
    "generate_plan": "pending",
    "collect_metrics": "pending",
    "screen_resources": "pending",
    "review_gate": "pending",
    "deep_scan": "pending",
    "phase_e_report": "pending",
    "phase_e_select": "pending",
    "phase_f_isolation": "pending",
    "isolation_review_gate": "pending",
    "execute_isolation": "pending",
    "decision": "pending",
    "phase_j_delete_review": "pending",
    "final_report": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: confirm_scope

**Type:** inline
**Description:** Confirm scan scope with user

## Execution
Follow these instructions:

Ask the user what to scan. One question at a time.
1. What environment? (prod/staging/dev/all)
2. Any resource types to include or exclude?
Prefer multiple choice. Skip if user already specified.


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"confirm_scope"`
- Set `steps.confirm_scope` to `"completed"`
### Step 2: confirm_connection

**Type:** inline
**Description:** Collect concrete connection details

## Execution
Follow the instructions in the prompt file `$PLUGINS/ico/skills/orchestrator/prompts/confirm-connection.prompt.md`.

Write the output to the specified output file.

## Output
- **Schema:** schemas/connection-config.schema.json
  - **File:** connection_config.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"confirm_connection"`
- Set `steps.confirm_connection` to `"completed"`
### Step 3: confirm_monitoring

**Type:** inline
**Description:** Confirm monitoring and CI/CD data sources

## Execution
Follow these instructions:

Ask two questions:

1. "Do you have a monitoring system for historical metrics?"
   Options: Prometheus, Datadog, CloudWatch, Azure Monitor, GCP Monitoring, or none.
   If none — warn that only real-time snapshots will be used.

2. "Do you use a CI/CD or GitOps tool for deployments?"
   Options: ArgoCD, FluxCD, Jenkins, GitLab CI, GitHub Actions, other, or none.
   If they name one, ask how to access it (URL, token, namespace).

Record both in {run_dir}/connection_config.json under `monitoring` and `cicd`.


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"confirm_monitoring"`
- Set `steps.confirm_monitoring` to `"completed"`
### Step 4: generate_intent

**Type:** inline
**Description:** Generate intent_detection.json from user input

## Execution
Follow these instructions:

Write {run_dir}/intent_detection.json:
- entity_types: list of resource types to scan
- scope: {account, region, tag_filters}
- exclusions: list of excluded resource_ids or tags


Write the output to the specified output file.

## Output
- **Schema:** schemas/intent-detection.schema.json
  - **File:** intent_detection.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"generate_intent"`
- Set `steps.generate_intent` to `"completed"`
### Step 5: generate_plan

**Type:** inline
**Description:** Dispatch Plan Agent with the orchestration template, present plan, wait for confirmation

## Execution
Follow these instructions:

1. Read the orchestration plan template: `$PLUGINS/ico/skills/orchestrator/prompts/orchestration-plan.agent.md`
2. Fill in any placeholders with info from intent_detection.json and user discussion
3. Use the Agent tool (subagent_type=general-purpose) with the filled template to produce an execution plan
4. Save the plan output verbatim to {run_dir}/execution_plan.md
5. Present the plan to user using the Write tool as markdown. Show: phase overview table, estimated duration, review checkpoints
6. WAIT for user confirmation before proceeding to execution.


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"generate_plan"`
- Set `steps.generate_plan` to `"completed"`
### Step 6: collect_metrics

**Type:** agent
**Description:** Discover resources and apply 3-signal coarse filter

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Use the Agent tool (subagent_type=general-purpose) to load the ico:metrics-collector skill.
Do NOT add extra commands, signal definitions, or thresholds.

Execute ico:metrics-collector with:
- run_dir: {run_dir}
- ssh_key_path: {ssh_key_path}
- task_id: {task_id}
- connection_config: read {run_dir}/connection_config.json


**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Complete execution

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"collect_metrics"`
- Set `steps.collect_metrics` to `"completed"`
### Step 7: screen_resources

**Type:** agent
**Description:** Score and rank zombie candidates

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Use the Agent tool (subagent_type=general-purpose) to load the ico:resource-screener skill.

Execute ico:resource-screener with:
- run_dir: {run_dir}
- task_id: {task_id}


**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Complete execution

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"screen_resources"`
- Set `steps.screen_resources` to `"completed"`
### Step 8: review_gate

**Type:** inline
**Description:** Present results and wait for user (BLOCKING)

## Execution
Follow these instructions:

Read {run_dir}/analysis/suspect_assessment.json.

Present to user via the Write tool, sorted by estimated_monthly_cost descending:
- Total candidates, high/medium/low counts
- Top candidates: resource_id, suspect_level, zombie_score, cost, key signals

ASK: which resources should enter deep scan?

WAIT for user response. This is BLOCKING.

Write {run_dir}/phase1_review_decision.json:
- resources_for_deep_scan: [resource_ids]
- skip_resources: [resource_ids]


Write the output to the specified output file.

## Output
- **Schema:** schemas/phase1-review-decision.schema.json
  - **File:** phase1_review_decision.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"review_gate"`
- Set `steps.review_gate` to `"completed"`
### Step 9: deep_scan

**Type:** agent
**Description:** Deep scan approved candidates (one per machine, max 8 concurrent)

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Read {run_dir}/phase1_review_decision.json.

Use the Agent tool (subagent_type=general-purpose) to load the ico:deep-scanner skill.
Do NOT add extra commands or collection steps -- the ico:deep-scanner skill defines the complete collection checklist.

Execute ico:deep-scanner for each resource in resources_for_deep_scan:
- run_dir: {run_dir}
- ssh_key_path: {ssh_key_path}
- Launch one agent per resource, max 8 concurrent
- Each writes analysis/deep_scan_{resource_id}.json


**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Complete execution

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"deep_scan"`
- Set `steps.deep_scan` to `"completed"`
### Step 10: phase_e_report

**Type:** agent
**Description:** Generate HTML report from deep scan data

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Read `$PLUGINS/ico/skills/orchestrator/prompts/report.prompt.md`.
Use the Agent tool (subagent_type=general-purpose) and pass the EXACT content of
report.prompt.md as the prompt. Do NOT write your own prompt — send the file content
verbatim. The sub-agent must write {run_dir}/reports/report.html.


**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Complete execution

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_e_report"`
- Set `steps.phase_e_report` to `"completed"`
### Step 11: phase_e_select

**Type:** inline
**Description:** Present deep scan report + ask user which resources to isolate (BLOCKING)

## Execution
Follow these instructions:

Verify `{run_dir}/reports/report.html` exists. If not, go back to phase_e_report.

Open the HTML report and present it. Do NOT summarize deep scan findings yourself —
the report IS the summary. Do NOT change the verdict, suspect_level, or zombie_score
from suspect_assessment.json.

ASK: which resources should proceed to isolation planning?
WAIT for user. BLOCKING.

Write {run_dir}/isolation_selection.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_e_select"`
- Set `steps.phase_e_select` to `"completed"`
### Step 12: phase_f_isolation

**Type:** agent
**Description:** Generate isolation plans

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Use the Agent tool (subagent_type=general-purpose) to load the ico:isolation-planner skill.

Execute ico:isolation-planner with:
- run_dir: {run_dir}
- task_id: {task_id}
- ssh_key_path: {ssh_key_path}


**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Complete execution

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_f_isolation"`
- Set `steps.phase_f_isolation` to `"completed"`
### Step 13: isolation_review_gate

**Type:** inline
**Description:** Present isolation plan, wait for approval (BLOCKING)

## Execution
Follow these instructions:

Read {run_dir}/analysis/isolation_batch_plan.json.

Compile the isolation plan as MARKDOWN via the Write tool. The markdown must include:

## Isolation Plan for [hostname] ([IP])
- **Method**: iptables DROP (description)
- **Rollback**: iptables-restore, estimated < N minutes
- **Pre-checks**: [list from plan]
- **Observation**: N days

## Batch Sequence
| Step | VM | Rationale |
|------|-----|-----------|
| ... | ... | ... |

## Risk Assessment
- [key risks from plan]

ASK: approve isolation plan?

WAIT for user confirmation. BLOCKING.

Write {run_dir}/phase2_review_decision.json.


Write the output to the specified output file.

## Output
- **Schema:** schemas/phase2-review-decision.schema.json
  - **File:** phase2_review_decision.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"isolation_review_gate"`
- Set `steps.isolation_review_gate` to `"completed"`
### Step 14: execute_isolation

**Type:** agent
**Description:** Execute isolation and observation

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Read {run_dir}/phase2_review_decision.json. If not approved, stop.

Use the Agent tool (subagent_type=general-purpose) to load the ico:isolation-executor skill.

Execute ico:isolation-executor with:
- run_dir: {run_dir}
- ssh_key_path: {ssh_key_path}
- environment: from scan_plan
- batch_plan: analysis/isolation_batch_plan.json
- isolation_plans: analysis/isolation_plan_*.json


**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Complete execution

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"execute_isolation"`
- Set `steps.execute_isolation` to `"completed"`
### Step 15: decision

**Type:** agent
**Description:** Present decision report and collect user decisions

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

Use the Agent tool (subagent_type=general-purpose) to load the ico:decision-handler skill.

Execute ico:decision-handler with:
- run_dir: {run_dir}
- task_id: {task_id}
- ssh_key_path: {ssh_key_path}
- Merge deep_scan + observation results, present report, collect user decisions
- Write confirm/phase5_decision.json with delete_resources array for each resource marked DELETE
- Write backup reports for DELETE resources to delete/backup_*.json
- Do NOT dispatch backup-creator or resource-cleaner -- wait for Phase J delete review gate


**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Complete execution

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"decision"`
- Set `steps.decision` to `"completed"`
### Step 16: phase_j_delete_review

**Type:** inline
**Description:** Present delete plan to user for final approval (BLOCKING)

## Execution
Follow these instructions:

Read {run_dir}/confirm/phase5_decision.json.

For each resource marked DELETE, read its backup report and deletion plan.

Compile a DELETE PLAN as markdown via the Write tool. Include:
- Per resource: resource_id, hostname, estimated_monthly_cost savings
- Backup strategy used, backup verification status
- Deletion method, rollback window
- Total cost savings if all approved

ASK: approve deletion plan?

WAIT for user response. BLOCKING.

Write {run_dir}/phase_j_delete_approval.json:
- approved_resources: [resource_ids]
- rejected_resources: [resource_ids]


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_j_delete_review"`
- Set `steps.phase_j_delete_review` to `"completed"`
### Step 17: final_report

**Type:** inline
**Description:** Deliver final report

## Execution
Follow these instructions:

Read {run_dir}/delete/deletion_report.json and cost_savings_report.json.
Also read ALL {run_dir}/analysis/deep_scan_*.json for deep-scanned resources.

Phase 1 -- Per-machine reports:
For EACH deep-scanned resource, generate a Markdown section with 5 Tabs:

**Tab 0 "Traffic"** -- Service Topology:
- One node for the VM (id=resource_id, label=hostname, type=service, status=healthy)
- For each edge in traffic_graph.edges, create peer nodes:
  - Process known -> label="IP:port process_name", type=src_service_type
  - Only port known -> label="IP:port", type=service
  - Client IP only -> label="IP (client)", type=gateway
  - Unmapped -> label="IP:port", type=service, status=degraded
- Edge: from=src node id, to=dst node id, label="{rate_kbps} Kb/s", throughput="{rate_kbps} Kb/s"
- Edge status: "healthy" for business, null for infra, "warning" for unmapped

**Tab 1 "Services"** -- with:
- Table: processes[] (PID, user, CPU%, MEM%, command), filter out systemd/sshd/kthread
- List: listening_ports[] as items {name: "{port} {process}", status: "ok"}
- Callout if local_databases non-empty: "Local databases: ..."

**Tab 2 "Scheduled Tasks"** -- with:
- Table: crontab_entries[] (user, schedule, command)
- Table: systemd_timers[] (unit, next, schedule)

**Tab 3 "Storage"** -- with:
- List: disk_partitions[] {key: mount, value: "used/size (use%)"}
- Callout if disk_usage has results with top-5 large directories

**Tab 4 "Ownership"** -- with:
- List: business.owner, business.team, business.environment, etc.
- Table: estimated_monthly_cost, spec.cpu_cores, spec.memory_gb, spec.disk_gb

Phase 2 -- Summary:
Compile final summary: scanned count, deleted count, cost savings, kept/exempt.
Deliver via the Write tool with a summary dashboard. Include recommended next steps.


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"final_report"`
- Set `steps.final_report` to `"completed"`