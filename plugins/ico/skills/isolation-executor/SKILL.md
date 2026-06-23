---
name: isolation-executor
description: >-
  Executes batch isolation operations per Phase 3 plan, monitors observation period with 3-dimensional anomaly attribution, triggers auto-rollback on P0/P1 anomalies, and generates structured observation reports (passed/failed/uncertain). Implements "Proof by Silence" principle: if nothing breaks during observation, resource is confirmed as zombie and advances to deletion phase.
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Workspace root directory for file passing between agents |
| ssh_key_path | string | No | SSH key path for cloud provider access |
| batch_plan | string | Yes | Path to analysis/isolation_batch_plan.json (batch order, dependencies) |
| isolation_plans | string | Yes | Path to analysis/isolation_plan_{resource_id}.json files (glob pattern) |
| environment | string | Yes | Environment tier for observation period matrix lookup |

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
    "phase_a_pre_isolation_setup": "pending",
    "phase_a_batch_isolation": "pending",
    "phase_b_observation_monitoring": "pending",
    "phase_c_anomaly_attribution": "pending",
    "phase_d_generate_observation_report": "pending",
    "phase_e_observation_batch_summary": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: phase_a_pre_isolation_setup

**Type:** inline
**Description:** Initialize observation directories and load isolation plans

## Execution
Follow these instructions:

Initialize Phase 4 execution environment:

1. Create directory structure:
   - {run_dir}/observe/ - for observation reports
   - {run_dir}/observe/snapshots/ - for pre-isolation state snapshots
   - {run_dir}/observe/logs/ - for execution logs

2. Load and validate inputs:
   - Read {run_dir}/analysis/isolation_batch_plan.json
   - Load all {run_dir}/analysis/isolation_plan_{resource_id}.json files
   - Validate schema conformance

3. Determine observation period matrix:
   - Read environment: {{ environment }}
   - For each resource, determine observation_period_days:
     * dev/test: 3 days (extend to 90 if quarterly task detected)
     * staging: 7 days (extend to 35 if monthly task detected)
     * production: 30 days (extend to 365 if annual task detected)
   - Calculate observation_end = isolation_executed_at + observation_period_days

4. Write {run_dir}/observe/execution_plan.json with:
   - batch_count: number of batches
   - total_resources: count of all resources
   - observation_periods: {resource_id: {start, end, days}}
   - execution_started_at: ISO8601 timestamp

This file is required for subsequent steps.


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_a_pre_isolation_setup"`
- Set `steps.phase_a_pre_isolation_setup` to `"completed"`
### Step 2: phase_a_batch_isolation

**Type:** agent
**Description:** Execute isolation for ALL batches sequentially

## Input Files
- `observe/execution_plan.json` (from Step phase_a_pre_isolation_setup, schema: schemas/execution-plan.schema.json)
- `analysis/isolation_plan_{resource_id}.json`

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

IMPORTANT: The batch plan (isolation_batch_plan.json) can contain N batches.
You MUST iterate over ALL batches 1..N sequentially.

1. Read batch_count from {run_dir}/analysis/isolation_batch_plan.json
   or {run_dir}/observe/execution_plan.json.

2. For batch_num in 1..batch_count (SEQUENTIAL, one batch at a time):
   a. Identify all resources in batch batch_num from isolation_batch_plan.json.
   b. Execute isolation for ALL resources in this batch (can run in PARALLEL
      within the batch, but must complete before starting next batch).
   c. Follow the per-resource isolation procedure below for each resource.
   d. Wait for every resource in this batch to finish (success or failure)
      before advancing to batch_num + 1.

3. After ALL batches complete, collect all isolation_executed_{resource_id}.json
   files and proceed to phase_b_observation_monitoring.

Per-resource isolation procedure:

For each resource:

1. Pre-isolation snapshot:
   - Capture current state (VM: iptables rules, RDS: SG rules, Redis: config, K8s: replicas, etc.)
   - Save to {run_dir}/observe/snapshots/{resource_id}_pre_isolation.json
   - Include: timestamp, resource_type, isolation_method, current_state

2. Execute isolation steps:
   - Read isolation_plan_{resource_id}.json
   - Execute each isolation_step in sequence
   - For each step: SSH exec / cloud API call / kubectl command (per resource type)
   - Log each step: command, exit_code, stdout, stderr, timestamp

3. Verify isolation took effect:
   - Re-check state to confirm isolation is active
   - For iptables: verify rule exists in `iptables -L -n`
   - For RDS SG: verify inbound rules count = 0
   - For Redis: verify old password fails, new password works
   - For K8s: verify replicas = 0 or selector matches no pods
   - If verification fails: attempt immediate rollback, mark resource as failed

4. Record isolation execution:
   - Write {run_dir}/observe/isolation_executed_{resource_id}.json with status and verification

Error handling:
- If isolation step fails: log error, attempt rollback, mark as isolation_failed
- If verification fails: attempt rollback, mark as failed
- If rollback fails: P0 escalation, notify user, do NOT proceed to observation
- Partial batch failure: successfully isolated resources proceed to observation
- If an entire batch fails: do NOT skip remaining batches; continue to next batch
- Batch timeout: if a batch takes > 30min, log warning but continue to next batch

Proceed to observation only if isolation_executed_{resource_id}.json
has status = "isolated" and verification_passed = true.


**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/execution-plan.schema.json`
   - Schema: `schemas/isolation-plan.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `observe/isolation_executed_{resource_id}.json`

## Output
- **Schema:** schemas/isolation-execution-result.schema.json
  - **File:** observe/isolation_executed_{resource_id}.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_a_batch_isolation"`
- Set `steps.phase_a_batch_isolation` to `"completed"`
### Step 3: phase_b_observation_monitoring

**Type:** agent
**Description:** Monitor observation period, collect signals, detect anomalies, trigger rollback

## Input Files
- `observe/isolation_executed_{resource_id}.json` (from Step phase_a_batch_isolation, schema: schemas/isolation-execution-result.schema.json)
- `analysis/isolation_plan_{resource_id}.json`

## Execution
Launch an independent agent with the following prompt file:

**Dispatch instruction:**

For each resource that successfully completed isolation (status = "isolated"),
run observation monitoring in parallel.

Observation period: from isolation_executed_at to observation_end (per resource)

For each resource, run observation loop:

1. Initialize observation state:
   - observation_id: obs-{uuid}
   - observation_start: isolation_executed_at
   - observation_end: isolation_executed_at + observation_period_days
   - signals: [] (list of collected signals)
   - rollback_triggered: false

2. Monitoring loop (poll every 5 minutes until observation_end):
   a. Collect metrics (5min window): Error rate, latency, CPU, memory, disk usage
   b. Fetch alerts: Query alert system for alerts touching blast_radius.affected_services
   c. Fetch complaints (poll q1h): Check IM channels and email/tickets
   d. Check auto-rollback triggers from isolation_plan.auto_rollback_triggers
      - If P0/P1: trigger rollback immediately
      - If P2: pause observation, mark uncertain

3. P0/P1 Rollback execution (if triggered):
   Retry strategy: max 3 attempts with exponential backoff (5s, 10s, 20s)

   For each rollback attempt:
   a. Execute rollback_plan from isolation_plan_{resource_id}.json
   b. Verify rollback took effect
   c. Health check: wait for affected_services to recover (timeout 300s)
   d. If verification AND health pass: stop rollback, mark as completed
   e. If attempt < 3 and failed: wait backoff delay, retry
   f. If attempt == 3 and failed: P0 escalation, mark rollback_failed, pause batch

4. P2 Pause observation (if triggered):
   - Pause observation clock, mark uncertain, notify user

5. Continue monitoring until observation_end

6. Collect all signals into the monitoring result


**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/isolation-execution-result.schema.json`
   - Schema: `schemas/isolation-plan.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `observe/observation_monitoring_{resource_id}.json`

## Output
- **Schema:** schemas/observation-monitoring-result.schema.json
  - **File:** observe/observation_monitoring_{resource_id}.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_b_observation_monitoring"`
- Set `steps.phase_b_observation_monitoring` to `"completed"`
### Step 4: phase_c_anomaly_attribution

**Type:** inline
**Description:** Perform 3D anomaly attribution (temporal/topological/directional)

## Input Files
- `observe/observation_monitoring_{resource_id}.json` (from Step phase_b_observation_monitoring, schema: schemas/observation-monitoring-result.schema.json)
- `analysis/isolation_plan_{resource_id}.json`

## Execution
Follow these instructions:

For each resource with rollback triggered, perform 3-dimensional anomaly
attribution to confirm causality.

Read:
- {run_dir}/observe/observation_monitoring_{resource_id}.json
- {run_dir}/analysis/isolation_plan_{resource_id}.json
- Dependency graph from Phase 2 forensics

For each anomaly signal (alert or complaint):

1. Temporal Association:
   gap_minutes = (anomaly_timestamp - isolation_executed_at) / 60
   - <= 120 min: score = 1.0 (high)
   - <= 360 min: score = 0.7 (moderate)
   - <= 1440 min: score = 0.4 (weak)
   - > 1440 min: score = 0.0 (negligible)

2. Topological Association:
   - In blast_radius.affected_services: score = 1.0
   - Within 2 hops: score = 0.6
   - No match: score = 0.0

3. Directional Association:
   - Isolated is upstream, anomaly in downstream: score = 1.0
   - Isolated is downstream, anomaly in upstream: score = 0.0
   - Peer: score = 0.5

Attribution decision:
   - >= 2 dimensions scored > 0: CONFIRMED, high confidence
   - 1 dimension scored > 0: UNCERTAIN, low confidence
   - 0 dimensions scored > 0: DISMISS, no confidence

Write {run_dir}/observe/attribution_{resource_id}.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/attribution-result.schema.json
  - **File:** observe/attribution_{resource_id}.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_c_anomaly_attribution"`
- Set `steps.phase_c_anomaly_attribution` to `"completed"`
### Step 5: phase_d_generate_observation_report

**Type:** inline
**Description:** Generate final observation report per resource

## Input Files
- `observe/isolation_executed_{resource_id}.json`
- `observe/observation_monitoring_{resource_id}.json`
- `observe/attribution_{resource_id}.json`

## Execution
Follow these instructions:

For each resource, generate final observation report.

Read:
- {run_dir}/observe/isolation_executed_{resource_id}.json
- {run_dir}/observe/observation_monitoring_{resource_id}.json
- {run_dir}/observe/attribution_{resource_id}.json (if exists)
- {run_dir}/analysis/isolation_plan_{resource_id}.json

Determine observation_result:
   - rollback completed: result = "failed"
   - rollback failed: result = "failed_rollback_incomplete"
   - observation incomplete or has P2 anomaly: result = "uncertain"
   - otherwise: result = "passed"

Summarize metrics: alert_count, complaint_count, anomaly_dates, max_error_rate.

Write {run_dir}/observe/observation_{resource_id}.json per schema.


Write the output to the specified output file.

## Output
- **Schema:** schemas/observation-report.schema.json
  - **File:** observe/observation_{resource_id}.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_d_generate_observation_report"`
- Set `steps.phase_d_generate_observation_report` to `"completed"`
### Step 6: phase_e_observation_batch_summary

**Type:** inline
**Description:** Aggregate all observation reports into batch summary

## Input Files
- `observe/observation_{resource_id}.json` (from Step phase_d_generate_observation_report, schema: schemas/observation-report.schema.json)

## Execution
Follow these instructions:

Aggregate all observation_{resource_id}.json files into summary.

Read all {run_dir}/observe/observation_{resource_id}.json files.

Calculate aggregate metrics:
   - total_resources, passed, failed, uncertain counts
   - rollback_triggered count
   - total_alerts, total_complaints

Write {run_dir}/observe/observation_batch_summary.json per schema.
This summary is required for the decision phase.


Write the output to the specified output file.

## Output
- **Schema:** schemas/observation-batch-summary.schema.json
  - **File:** observe/observation_batch_summary.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase_e_observation_batch_summary"`
- Set `steps.phase_e_observation_batch_summary` to `"completed"`

## Error Handling

### Isolation execution fails for a resource

Log error, skip observation for that resource, mark as isolation_failed. Continue with remaining resources in batch.

### Isolation verification fails

Attempt immediate rollback. If rollback succeeds, mark as failed. If rollback fails, P0 escalation, notify user, do NOT proceed.

### Observation monitoring encounters metric backend unavailable

Graceful degradation: rely on alert/complaint channels. If critical data missing, mark observation as uncertain.

### P0 anomaly detected during observation

Execute rollback immediately (no attribution needed). Mark observation_result = failed.

### P1 anomaly detected during observation

Perform 3D attribution. If CONFIRMED, execute rollback. If UNCERTAIN, pause observation, notify user.

### P2 anomaly detected during observation

Pause observation clock. Mark observation_result = uncertain. Notify user for manual judgment.

### Rollback execution fails (after max 3 retries with backoff)

P0 Escalation protocol:
1. Mark resource: rollback_status = "rollback_failed"
2. Generate incident report with all attempts, timestamps, errors
3. Immediate notifications to on-call engineer
4. Batch pause: STOP all observation loops for remaining resources
5. Save batch state, wait for manual intervention


### Observation period expires without anomalies

Mark observation_result = passed. Proceed to deletion phase.

### User interrupts observation period

Save current observation state. Can resume from checkpoint. Do not mark as complete until full period elapsed.
