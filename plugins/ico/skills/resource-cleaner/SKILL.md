---
name: resource-cleaner
description: >-
  Phase 6 Delete - Zombie resource deletion execution. Orchestrates a 6-step deletion process: pre-flight re-evaluation -> verify backup-creator backups -> deletion execution -> deletion verification -> metadata update -> audit + cost report. Supports batch deletion (10 per batch, 5-minute intervals), cascading cleanup across resource types, special elastic IP DNS check, complete audit trail and cost savings analysis. Backups are performed upfront by zombie-backup-creator; resource-cleaner only verifies that backups exist.
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Workspace root directory for file passing between steps |
| phase5_decision_file | string | Yes | Path to Phase 5 confirmation decision JSON (from zombie-decision-handler) |
| resource_ids | array | Yes | List of resource IDs to delete |
| batch_size_max | integer | No | Max resources per deletion batch |
| batch_interval_sec | integer | No | Interval between batches (seconds) |
| deletion_parallelism | integer | No | Max concurrent deletion operations per batch |
| enable_eip_dns_check | boolean | No | Enable DNS record check before elastic IP deletion |
| dry_run | boolean | No | Dry-run mode (validate logic but do not execute actual deletion) |

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
    "load_phase5_decision": "pending",
    "preflight_check_cooling_period": "pending",
    "preflight_check_decision_status": "pending",
    "preflight_check_resource_existence": "pending",
    "preflight_check_isolation_state": "pending",
    "preflight_check_no_new_traffic": "pending",
    "preflight_check_dependencies": "pending",
    "preflight_check_owner": "pending",
    "preflight_aggregate_result": "pending",
    "verify_backup_creator_output": "pending",
    "build_dependency_graph": "pending",
    "topological_sort_resources": "pending",
    "create_batch_plan": "pending",
    "execute_batch_deletions": "pending",
    "verify_deletion_completion": "pending",
    "check_orphaned_objects": "pending",
    "check_billing_charges": "pending",
    "update_cmdb": "pending",
    "update_monitoring": "pending",
    "collect_all_events": "pending",
    "build_audit_trail": "pending",
    "calculate_cost_savings": "pending",
    "generate_batch_summary": "pending",
    "merge_reports": "pending",
    "generate_notifications": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: load_phase5_decision

**Type:** inline
**Description:** Load Phase 5 confirmation decision and validate format

## Execution
Follow these instructions:

Read the Phase 5 confirmation decision from {run_dir}/{phase5_decision_file}.

Validate that it is valid JSON and contains:
- Top level: decision_id, decision_timestamp, total_resources, resources (non-empty array)
- Per resource: resource_id, observation_result, resource_type, entity_type
- Per resource: environment, cloud_provider, resource_metadata, estimated_monthly_cost

Note: observation_result is the authoritative gating field -- resources with
observation_result="passed" have completed the isolation observation period
and are safe to delete.

Output to {run_dir}/delete/phase5_decision_loaded.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"load_phase5_decision"`
- Set `steps.load_phase5_decision` to `"completed"`
### Step 2: preflight_check_cooling_period

**Type:** inline
**Description:** Verify observation period has completed (isolation observation IS the cooling period)

## Input Files
- `delete/phase5_decision_loaded.json` (from Step load_phase5_decision, schema: schemas/phase5_confirmation.schema.json)

## Execution
Follow these instructions:

Read {run_dir}/delete/phase5_decision_loaded.json to get resource IDs.

The isolation observation period from Phase 2 serves as the cooling period.
Each resource must have passed observation before deletion can proceed.

For each resource in {resource_ids}:
  - Verify observation_result is "passed" in the phase5 decision.
  - If observation_result is "failed" or "uncertain": output BLOCKED reason.
  - If observation_result is "passed": output passed status.

Note: There is no separate cooling_period_tracker.json in the new flow.
The Phase 2 isolation observation IS the cooling period. Resources that
passed observation are safe to delete.

Output to {run_dir}/delete/preflight_cooling_period.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_check_cooling_period"`
- Set `steps.preflight_check_cooling_period` to `"completed"`
### Step 3: preflight_check_decision_status

**Type:** inline
**Description:** Verify decision is valid (decision_id + decision_timestamp exist)

## Input Files
- `delete/phase5_decision_loaded.json` (from Step load_phase5_decision, schema: schemas/phase5_confirmation.schema.json)

## Execution
Follow these instructions:

Read {run_dir}/delete/phase5_decision_loaded.json.

phase5_decision.json does NOT contain a decision_status field. Instead, validate:
- decision_id is present and non-empty
- decision_timestamp is a valid ISO8601 timestamp
- total_resources > 0
- resources array is non-empty

If all checks pass: output PASSED
If any check fails: output BLOCKED with reason

Output to {run_dir}/delete/preflight_decision_status.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_check_decision_status"`
- Set `steps.preflight_check_decision_status` to `"completed"`
### Step 4: preflight_check_resource_existence

**Type:** inline
**Description:** Verify resources still exist in cloud (query cloud APIs)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Query cloud API to check if resource exists:
- For CloudVM: describe_instances(resource_id)
- For RDS: describe_db_instances(resource_id)
- For K8s: kubectl get resource resource_id
- etc.

Record: exists (true/false), resource_state (running/stopped/etc)

Output to {run_dir}/delete/preflight_resource_existence.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_check_resource_existence"`
- Set `steps.preflight_check_resource_existence` to `"completed"`
### Step 5: preflight_check_isolation_state

**Type:** inline
**Description:** Verify Phase 3 isolation is still valid (stopped, security group denied, etc)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Check isolation state based on entity_type:
- CloudVM: verify instance is Stopped
- RDS: verify security group has Deny All inbound
- K8s Deployment: verify replicas == 0
- Redis: verify whitelist is empty or denies all

Record: isolation_valid (true/false), current_state

Output to {run_dir}/delete/preflight_isolation_state.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_check_isolation_state"`
- Set `steps.preflight_check_isolation_state` to `"completed"`
### Step 6: preflight_check_no_new_traffic

**Type:** inline
**Description:** Verify no new traffic in last 7 days (check metrics, access logs)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Query monitoring/metrics APIs for last 7 days:
- Traffic volume
- Connection count
- Access log entries
- Request count

If any metric > 0: flag as warning, record data
If all metrics == 0: flag as passed

Output to {run_dir}/delete/preflight_traffic_check.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_check_no_new_traffic"`
- Set `steps.preflight_check_no_new_traffic` to `"completed"`
### Step 7: preflight_check_dependencies

**Type:** inline
**Description:** Verify no new dependencies created

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Query dependency records:
- Find all resources that depend on this resource
- Check if any dependencies were created after Phase 5 decision timestamp
- Record new dependencies

Output to {run_dir}/delete/preflight_dependencies.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_check_dependencies"`
- Set `steps.preflight_check_dependencies` to `"completed"`
### Step 8: preflight_check_owner

**Type:** inline
**Description:** Verify Owner unchanged compared to Phase 2 record

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Read Phase 5 decision resource's owner_detail.user_id
Query current asset system for owner_id

If changed: flag warning, record old vs new
If unchanged: flag passed

Output to {run_dir}/delete/preflight_owner_check.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_check_owner"`
- Set `steps.preflight_check_owner` to `"completed"`
### Step 9: preflight_aggregate_result

**Type:** inline
**Description:** Aggregate all pre-flight checks and determine overall result

## Execution
Follow these instructions:

Read all preflight check results:
- cooling_period
- decision_status
- resource_existence
- isolation_state
- traffic_check
- dependencies
- owner_check

Determine overall result:
- BLOCKED: if any critical check fails (resource_existence shows resource missing, isolation_state invalid, owner_changed)
- BLOCKED: if cooling_period check fails (observation_result is not "passed")
- BLOCKED: if decision_status check fails (decision_id/timestamp missing or invalid)
- WARNING: if traffic detected or new dependencies found
- PASSED: all checks pass

If WARNING: create a review request, record waiting for human approval

Output to {run_dir}/delete/pre_flight_report.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/preflight_re_evaluation_result.schema.json
  - **File:** delete/pre_flight_report.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"preflight_aggregate_result"`
- Set `steps.preflight_aggregate_result` to `"completed"`
### Step 10: verify_backup_creator_output

**Type:** inline
**Description:** Verify backup-creator has produced valid backups for all resources about to be deleted

## Execution
Follow these instructions:

The zombie-backup-creator runs before resource-cleaner and produces the following
output files in {run_dir}/delete/:

1. backup_summary.json -- aggregate summary with statistics, per-resource status,
   next_steps.ready_for_deletion, next_steps.successful_resources, escalations
2. backup_strategies.json -- per-resource backup strategy (method, retention_days)
3. backup_report_{resource_id}.json -- per-resource detailed backup report

**Verification checklist**:

1. Read {run_dir}/delete/backup_summary.json.
   - Confirm the file exists and is valid JSON.
   - Check statistics.successful_backups > 0.
   - Check next_steps.ready_for_deletion is true.

2. Read {run_dir}/delete/backup_strategies.json.
   - Confirm the file exists and contains a strategy entry for each
     resource_id in {resource_ids}.

3. For each resource_id in {resource_ids}:
   a. Verify a backup_report_{resource_id}.json exists in {run_dir}/delete/
   b. Verify the report's backup_record.status is "success"
   c. Verify backup_record.verification.passed is true
   d. Verify backup_record.protection.tags_applied is true

4. Cross-reference: every resource_id in {resource_ids} MUST have a
   successful backup record in backup_summary.json. If any resource is
   missing a backup or has a failed backup -> HALT DELETION and output error.

5. If escalations exist in backup_summary.json, check whether any escalated
   resources are in {resource_ids}. If so -> HALT DELETION for those
   specific resources, proceed with non-escalated ones if possible.

If can_proceed_with_deletion is false, DO NOT continue to Phase 3.
Output the verification failure and escalate to manual review.

Output to {run_dir}/delete/backup_verification_summary.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/backup_verification_summary.schema.json
  - **File:** delete/backup_verification_summary.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"verify_backup_creator_output"`
- Set `steps.verify_backup_creator_output` to `"completed"`
### Step 11: build_dependency_graph

**Type:** inline
**Description:** Build resource dependency graph (for batch sequencing)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Read Phase 5 decision blast_radius to find dependencies
- If resource A's blast_radius includes resource B
- Add edge: A -> B (A depends on B, so B should be deleted first)

Output to {run_dir}/delete/dependency_graph.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/dependency_graph.schema.json
  - **File:** delete/dependency_graph.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"build_dependency_graph"`
- Set `steps.build_dependency_graph` to `"completed"`
### Step 12: topological_sort_resources

**Type:** inline
**Description:** Perform topological sort on dependency graph

## Input Files
- `delete/dependency_graph.json` (from Step build_dependency_graph, schema: schemas/dependency_graph.schema.json)

## Execution
Follow these instructions:

Read {run_dir}/delete/dependency_graph.json

Perform topological sort: resources with no dependencies first,
then resources whose dependencies are already sorted

Output sorted list to {run_dir}/delete/sorted_resources.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/sorted_resources.schema.json
  - **File:** delete/sorted_resources.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"topological_sort_resources"`
- Set `steps.topological_sort_resources` to `"completed"`
### Step 13: create_batch_plan

**Type:** inline
**Description:** Create batch execution plan (max batch_size_max per batch, 5min intervals)

## Input Files
- `delete/sorted_resources.json` (from Step topological_sort_resources, schema: schemas/sorted_resources.schema.json)

## Execution
Follow these instructions:

Read {run_dir}/delete/sorted_resources.json

Create batches:
- Max {batch_size_max} resources per batch
- Resources in each batch have no inter-dependencies
- Total batches: ceil(total_resources / {batch_size_max})

Output to {run_dir}/delete/batch_delete_plan.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/batch_deletion_plan.schema.json
  - **File:** delete/batch_delete_plan.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"create_batch_plan"`
- Set `steps.create_batch_plan` to `"completed"`
### Step 14: execute_batch_deletions

**Type:** inline
**Description:** Execute deletion batches sequentially, resources in batch in parallel

## Input Files
- `delete/batch_delete_plan.json` (from Step create_batch_plan, schema: schemas/batch_deletion_plan.schema.json)

## Execution
Follow these instructions:

Read {run_dir}/delete/batch_delete_plan.json and Phase 5 decision.

For each batch (sequentially):
  For each resource in batch (up to {deletion_parallelism} in parallel):
    Execute 6-step deletion:

    1. Detach traffic
       - Remove from load balancer backends
       - Clear DNS records
       - Verify K8s endpoints empty
       - Unbind elastic IP (release separately)

    2. Stop services
       - Stop VM instance
       - K8s: scale replicas to 0
       - Redis: clear whitelist

    3. Delete sub-resources
       - RDS: delete read replicas first
       - K8s: delete HPA, Service (if cohabited)
       - Delete data disks, ENI

    4. Delete main resource
       - DELETE instance / DB / workload / etc
       - Special for elastic IP: check DNS records before release (if {enable_eip_dns_check})

    5. Cleanup associated objects
       - Delete security group rules (if instance-specific)
       - Delete auto-snapshot policies
       - Delete monitoring alerts

    6. [if dry_run] Skip actual deletion, just record plan

    Record each step: timestamp, result (success/failure)

  After batch: wait {batch_interval_sec} seconds before next batch

Output per-resource deletion records to {run_dir}/delete/deletion_record_{resource_id}.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"execute_batch_deletions"`
- Set `steps.execute_batch_deletions` to `"completed"`
### Step 15: verify_deletion_completion

**Type:** inline
**Description:** Verify resources deleted (3x cloud API queries with 5s interval)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Query cloud API 3 times (5 second intervals):
- describe_instances(resource_id) or equivalent
- Expected: NOT_FOUND / 404 error
- If resource still exists: escalate

Output to {run_dir}/delete/deletion_verification.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/deletion_verification.schema.json
  - **File:** delete/deletion_verification.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"verify_deletion_completion"`
- Set `steps.verify_deletion_completion` to `"completed"`
### Step 16: check_orphaned_objects

**Type:** inline
**Description:** Check for orphaned sub-resources (snapshots, security groups, ENI, etc)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Search for orphaned objects:
- Snapshots related to deleted VM
- Security group rules pointing to deleted VM
- Network interfaces (ENI) orphaned
- Configuration parameters orphaned

Output to {run_dir}/delete/orphaned_objects_check.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"check_orphaned_objects"`
- Set `steps.check_orphaned_objects` to `"completed"`
### Step 17: check_billing_charges

**Type:** inline
**Description:** Check cloud billing (no new charges after deletion_timestamp)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Query cloud platform billing APIs:
- Check charges in last 24 hours
- Expected: no new charges after deletion timestamp

Output to {run_dir}/delete/billing_check.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"check_billing_charges"`
- Set `steps.check_billing_charges` to `"completed"`
### Step 18: update_cmdb

**Type:** inline
**Description:** Mark resources as deleted in CMDB/asset system

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Update CMDB:
- Set status = "deleted"
- Set deleted_at = current_timestamp
- Set deleted_by = "zombie-resource-cleaner"

Output to {run_dir}/delete/cmdb_updates.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"update_cmdb"`
- Set `steps.update_cmdb` to `"completed"`
### Step 19: update_monitoring

**Type:** inline
**Description:** Delete monitoring rules and collection configs

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Update monitoring system:
- Delete alert rules for resource_id
- Delete metric collection configs
- Archive dashboard references

Output to {run_dir}/delete/monitoring_updates.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"update_monitoring"`
- Set `steps.update_monitoring` to `"completed"`
### Step 20: collect_all_events

**Type:** inline
**Description:** Collect all execution events from pre-flight through metadata update

## Execution
Follow these instructions:

Read all phase output files:
- preflight checks
- backup verification records
- deletion records
- verification results
- metadata updates

Collect timeline of events with timestamps


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"collect_all_events"`
- Set `steps.collect_all_events` to `"completed"`
### Step 21: build_audit_trail

**Type:** inline
**Description:** Build complete audit timeline with per-event schema

## Execution
Follow these instructions:

Build audit timeline with all events:
- pre_flight_started / passed / blocked
- backup_verified / missing / failed
- deletion_started / step_completed / completed / failed
- verification_started / completed
- metadata_updated
- cost_calculated

Each event must conform to the audit_event schema.

Output to {run_dir}/delete/audit_trail.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"build_audit_trail"`
- Set `steps.build_audit_trail` to `"completed"`
### Step 22: calculate_cost_savings

**Type:** inline
**Description:** Calculate cost savings (immediate + lifecycle + net)

## Execution
Follow these instructions:

For each resource_id in {resource_ids}:

Read Phase 5 decision for:
- resource_properties.created_at
- estimated_monthly_cost
- entity_type, environment

Calculate:
1. Immediate savings: monthly_cost + (monthly_cost * 12)
2. Lifecycle cost: (now - created_at days) * (monthly_cost / 30)
3. Zombie period cost: (deletion_time - isolation_time) * (monthly_cost / 30)
4. Backup storage cost: (backup_size_gb * retention_days) * storage_price_per_gb_day
5. Net savings: immediate - backup_storage

Output per-resource to {run_dir}/delete/cost_savings_{resource_id}.json


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"calculate_cost_savings"`
- Set `steps.calculate_cost_savings` to `"completed"`
### Step 23: generate_batch_summary

**Type:** inline
**Description:** Generate batch deletion summary with all resource outcomes

## Execution
Follow these instructions:

Read:
- batch_delete_plan.json
- All deletion_record_{resource_id}.json
- All cost_savings_{resource_id}.json
- audit_trail.json

Generate summary:
- Total planned / deleted / failed / skipped
- Total monthly / annual savings
- Per-resource status and savings
- Audit completeness check

Output to {run_dir}/delete/batch_delete_summary.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/batch_deletion_summary.schema.json
  - **File:** delete/batch_delete_summary.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"generate_batch_summary"`
- Set `steps.generate_batch_summary` to `"completed"`
### Step 24: merge_reports

**Type:** inline
**Description:** Merge per-resource reports into final comprehensive deletion report

## Input Files
- `delete/batch_delete_summary.json` (from Step generate_batch_summary, schema: schemas/batch_deletion_summary.schema.json)

## Execution
Follow these instructions:

Merge:
- All pre_flight reports
- All backup verification records
- All deletion records
- All cost analyses
- Audit trail
- Batch summary

Output comprehensive report to {run_dir}/delete/deletion_report.json
Output cost summary to {run_dir}/delete/cost_savings_report.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/deletion_report.schema.json
  - **File:** delete/deletion_report.json
- **Schema:** schemas/cost_savings_report.schema.json
  - **File:** delete/cost_savings_report.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"merge_reports"`
- Set `steps.merge_reports` to `"completed"`
### Step 25: generate_notifications

**Type:** inline
**Description:** Generate notification content for Phase 5 decider and affected teams

## Input Files
- `delete/deletion_report.json` (from Step merge_reports, schema: schemas/deletion_report.schema.json)
- `delete/cost_savings_report.json` (from Step merge_reports, schema: schemas/cost_savings_report.schema.json)

## Execution
Follow these instructions:

Read:
- batch_delete_summary.json
- cost_savings_report.json
- audit_trail.json

Generate notifications:
1. Summary: X resources deleted, Y cost saved, Z warnings
2. Backup retention: will expire on {date}, last chance notification {date-3d}
3. Recovery window: restores available for {retention_days} days
4. Any failures: list with remediation steps

Output to {run_dir}/delete/notifications.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/notifications.schema.json
  - **File:** delete/notifications.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"generate_notifications"`
- Set `steps.generate_notifications` to `"completed"`