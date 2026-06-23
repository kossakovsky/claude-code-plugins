---
name: backup-creator
description: >-
  Phase 6 Delete: Create differentiated backups per resource type before deletion.
  
  This runbook implements the forced backup strategy from phase-6-delete.md section 4:
  - Pre-backup validation (resource exists, isolation intact, cloud API accessible)
  - Backup strategy dispatch (10+ resource types x environments)
  - Backup creation with 3-retry + exponential backoff
  - Backup verification (metadata validation, restore hints)
  - Backup protection (tagging, lifecycle rules)
  - Escalation to manual if all retries fail
  - Report generation per resource
  
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Working directory absolute path for input/output files |
| decision_id | string | Yes | Phase 5 confirmation decision ID (e.g., confirm-20260605-001) |
| phase5_decision_file | string | Yes | Path to Phase 5 decision file (confirm/phase5_decision.json from zombie-decision-handler), containing resources array with resource_id, entity_type, environment, cloud_provider, resource_metadata |
| ssh_key_path | string | No | SSH key path for cloud API calls and remote execution |
| task_id | string | Yes | Task ID for progress tracking in backup_episodes.json |
| max_concurrent_backups | integer | No | Maximum concurrent backup operations (avoid cloud API throttling) |
| backup_retention_days_override | integer | No | Override default retention days (prod:30, staging:14, dev:7) |

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
    "validate_input": "pending",
    "pre_backup_validation": "pending",
    "select_backup_strategy": "pending",
    "backup_creation_batch": "pending",
    "backup_verification": "pending",
    "backup_protection": "pending",
    "generate_reports": "pending",
    "handle_escalations": "pending",
    "finalize": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: validate_input

**Type:** inline
**Description:** Validate input parameters and read resource list

## Execution
Follow these instructions:

Your task is to validate input parameters and read the list of resources to be backed up.

**Steps**:
1. Verify that the run_dir directory exists and is writable
2. Verify that {run_dir}/{phase5_decision_file} file exists
3. Read phase5_decision_file, extract the resources array (written by decision-handler's write-phase5-decision step), verify each element contains:
   - resource_id (required)
   - resource_type (required): CloudVM/CloudRDS/CloudCache/K8sWorkload/... (resource_type defined in isolation plan)
   - entity_type (required): VM/Database/Cache/K8s/ElasticIP/LoadBalancer/... (cloud provider entity type)
   - environment (required): dev/staging/prod
   - cloud_provider (required): aws/aliyun/k8s
   - resource_metadata (required): JSON object with provider-specific fields
4. Read decision_id from phase5_decision_file (auto-uses the ID assigned by decision-handler)
5. Count resources, group by entity_type
6. Write to {run_dir}/delete/backup_validation_start.json
7. If validation fails, return error status; if passed, continue


Write the output to the specified output file.

## Output
- **Schema:** schemas/backup_validation_start.schema.json
  - **File:** delete/backup_validation_start.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"validate_input"`
- Set `steps.validate_input` to `"completed"`
### Step 2: pre_backup_validation

**Type:** agent
**Description:** Phase 1: Validate each resource before backup attempt (existence, isolation state, API accessibility, storage quota)

## Input Files
- `delete/backup_validation_start.json` (from Step validate_input, schema: schemas/backup_validation_start.schema.json)

## Execution
Launch an independent agent with the following prompt file:

**Prompt file:** `$PLUGINS/ico/skills/backup-creator/prompts/01_pre_backup_validation.md`
**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/backup_validation_start.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `delete/pre_backup_validation.json`

## Output
- **Schema:** schemas/pre_backup_validation.schema.json
  - **File:** delete/pre_backup_validation.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"pre_backup_validation"`
- Set `steps.pre_backup_validation` to `"completed"`
### Step 3: select_backup_strategy

**Type:** agent
**Description:** Phase 2: Select backup method per resource type and environment

## Input Files
- `delete/pre_backup_validation.json` (from Step pre_backup_validation, schema: schemas/pre_backup_validation.schema.json)

## Execution
Launch an independent agent with the following prompt file:

**Prompt file:** `$PLUGINS/ico/skills/backup-creator/prompts/02_backup_strategy_selection.md`
**Agent workflow:**

1. Read input data from:
   - Schema: `schemas/pre_backup_validation.schema.json`

2. Execute the agent with the prompt

3. Write results to:
   - File: `delete/backup_strategies.json`

## Output
- **Schema:** schemas/backup_strategies.schema.json
  - **File:** delete/backup_strategies.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"select_backup_strategy"`
- Set `steps.select_backup_strategy` to `"completed"`
### Step 4: backup_creation_batch

**Type:** inline
**Description:** Phase 3: Create backups with retry logic (max_concurrent_backups parallel, 3 retries each)

## Input Files
- `delete/backup_strategies.json` (from Step select_backup_strategy, schema: schemas/backup_strategies.schema.json)

## Execution
Follow these instructions:

Your task is to execute backup creation with retry logic and concurrency control.

**Architecture**:
- Maintain a work queue, max {max_concurrent_backups} concurrent backup tasks
- Each backup retries up to 3 times with exponential backoff (5s, 10s, 20s)
- Successful backups record backup_id; failed backups record error and push to retry queue or escalate to manual

**For each resource**:

1. **Attempt 1**
   - Call the backup creation function for the corresponding resource type:
     - CloudVM: create_ami() + create_snapshots_for_data_volumes()
     - RDS: create_final_snapshot()
     - Redis: execute_bgsave() + export_rdb_to_s3()
     - K8s: export_yaml_manifest() + upload_to_s3()
     - ... (refer to phase-6-delete.md section 4.2-4.10)
   - Record start time, backup ID (if returned immediately), call parameters
   - Wait for backup completion (poll status, timeout = resource-type dependent)

2. **Failure handling** (first attempt or retry)
   - Catch exceptions, classify as:
     - **Retriable**: Service unavailable, Timeout, Rate limit, Transient error
     - **Non-retriable**: Invalid credential, Resource not found, Quota exceeded (hard limit)
   - Retriable error -> wait backoff time, add to retry queue
   - Non-retriable error -> immediately record as failed, prepare escalation

3. **Attempts 2 and 3**
   - Repeat step 1, record attempt number
   - If 3rd attempt still fails -> record as "escalation_required"

4. **Success indicators**
   - Backup ID returned, backup status is available/completed
   - Backup size > 0 (for RDB, YAML files, etc.)

5. **Concurrency control**:
   - Maintain active backup task count <= {max_concurrent_backups}
   - Manage using queue and async workers

6. **Write progress file** {run_dir}/delete/backup_creation_progress.json with per-resource attempt records, status, backup IDs, and audit events.


Write the output to the specified output file.

## Output
- **Schema:** schemas/backup_creation_progress.schema.json
  - **File:** delete/backup_creation_progress.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"backup_creation_batch"`
- Set `steps.backup_creation_batch` to `"completed"`
### Step 5: backup_verification

**Type:** inline
**Description:** Phase 4: Verify each backup is accessible and restorable

## Input Files
- `delete/backup_creation_progress.json` (from Step backup_creation_batch, schema: schemas/backup_creation_progress.schema.json)

## Execution
Follow these instructions:

Your task is to verify the accessibility and recoverability of each successfully created backup.

**For each successful backup**:

1. **Existence check**
   - CloudVM AMI: describe_images(ImageIds=[ami_id]) -> state must be "available"
   - RDS snapshot: describe_db_snapshots(DBSnapshotIdentifier=...) -> state must be "available"
   - Redis RDB: Check S3 object exists, size > 0
   - K8s YAML: Check S3 object exists, size > 0

2. **Readability check**
   - Can read backup metadata (IAM permissions correct)
   - For Redis RDB, verify JSON config snapshot format is valid
   - For K8s YAML, run kubectl apply --dry-run=client to verify syntax

3. **Completeness check** (resource-type dependent)
   - CloudVM: All data disk snapshots are complete
   - RDS: Snapshot size > 0, includes database parameters
   - K8s: YAML includes all related ConfigMap/Secret/Service

4. **Recovery hints generation**
   - Based on resource type and backup method, generate recovery steps with method, instructions, estimated_time_minutes, and pre_requisites

5. **Failure handling**
   - If verification fails, mark as "backup_verification_failed"
   - Trigger manual escalation: cannot confirm backup is recoverable, needs manual confirmation

6. **Write verification results** {run_dir}/delete/backup_verification.json with per-resource checks, recovery hints, and status.


Write the output to the specified output file.

## Output
- **Schema:** schemas/backup_verification.schema.json
  - **File:** delete/backup_verification.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"backup_verification"`
- Set `steps.backup_verification` to `"completed"`
### Step 6: backup_protection

**Type:** inline
**Description:** Phase 5: Apply protection tags and lifecycle rules to backups

## Input Files
- `delete/backup_verification.json` (from Step backup_verification, schema: schemas/backup_verification.schema.json)

## Execution
Follow these instructions:

Your task is to apply protection measures to all successfully verified backups.

**For each successfully verified backup**:

1. **Apply tags** (all resource types)
   - CloudVM AMI and Snapshots:
     - Tag: `zombie-backup=true`
     - Tag: `decision_id={decision_id}`
     - Tag: `resource_id={resource_id}`
     - Tag: `backup_date={date}`
     - Tag: `retention_days={retention_days}`
   - RDS Snapshot: Same as above (if tag supported)
   - S3/OSS objects:
     - Metadata: `zombie-backup=true`, `decision_id=...`
     - S3 Tag: Same as above

2. **Set lifecycle rules** (S3/OSS)
   - For objects with prefix `backup-*`:
     - Expiration Rule: Days={retention_days}, Filter: Tag `zombie-backup=true`, Action: Delete object + delete all versions

3. **Enable encryption** (handled by resource type category)
   - **K8s Secret backup (mandatory encryption)**:
     - Must use KMS to encrypt Secret data
     - Check: if resource_type == "k8s_secret" or entity_type == "K8sSecret"
       - Must provide KMS key ARN or Key ID
       - Use KMS to encrypt exported YAML files (unencrypted export not allowed)
       - Verify encryption flag is recorded in S3/OSS object metadata as `kms_encrypted=true`
       - If KMS key is missing, mark as FAILED, refuse to save unencrypted Secret
     - Encryption algorithm: AES-256-GCM or AES-256-CBC (via KMS)
   - **Other resource backups** (recommended encryption):
     - CloudVM: Enable SSE-S3 or SSE-KMS (optional)
     - RDS: Confirm snapshot is encrypted (if original instance encrypted)
     - S3/OSS: Enable default encryption policy (optional)
     - K8s ConfigMap/PVC: If containing sensitive data, recommend enabling KMS (optional)

4. **Access control**
   - **K8s Secret backup (mandatory access restriction)**:
     - Only allow recovery scripts and auditors to read
     - S3: Set BucketPolicy to Deny all GetObject except for recovery scripts
     - OSS: Set Bucket ACL to Deny public access
   - **Other resource backups** (optional):
     - Restrict backup access permissions (only recovery scripts can read)
     - Prevent accidental deletion (IAM deny DeleteObject)

5. **Write protection results** {run_dir}/delete/backup_protection.json with per-resource actions, status, and K8s secret protection details.


Write the output to the specified output file.

## Output
- **Schema:** schemas/backup_protection.schema.json
  - **File:** delete/backup_protection.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"backup_protection"`
- Set `steps.backup_protection` to `"completed"`
### Step 7: generate_reports

**Type:** inline
**Description:** Phase 6: Generate per-resource backup reports and aggregate summary

## Input Files
- `delete/backup_creation_progress.json` (from Step backup_creation_batch, schema: schemas/backup_creation_progress.schema.json)
- `delete/backup_protection.json` (from Step backup_protection, schema: schemas/backup_protection.schema.json)

## Execution
Follow these instructions:

Your task is to generate detailed backup reports and a summary.

**Generate per-resource reports** {run_dir}/delete/backup_report_{resource_id}.json for each resource, combining data from all prior phases: pre_backup_validation, backup_strategy, backup_record (status, backup_id, type, size, duration, attempts, verification, protection), failure_record (if failed after retries), and audit_log.

**Generate summary report** {run_dir}/delete/backup_summary.json with:
- statistics: total, successful, failed, escalations, success_rate
- by_resource_type and by_environment breakdowns
- backup_storage_costs: total size, daily cost, retention, total cost
- escalations list with resource_id, reason, action_required
- next_steps: ready_for_deletion flag, escalated resources requiring manual action, recommendation


Write the output to the specified output file.

## Output
- **Schema:** schemas/backup_report_output.json
  - **File:** delete/backup_report_{resource_id}.json
- **Schema:** schemas/backup_summary.schema.json
  - **File:** delete/backup_summary.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"generate_reports"`
- Set `steps.generate_reports` to `"completed"`
### Step 8: handle_escalations

**Type:** inline
**Description:** Phase 7: Process escalations and send notifications

## Input Files
- `delete/backup_summary.json` (from Step generate_reports, schema: schemas/backup_summary.schema.json)

## Execution
Follow these instructions:

Your task is to process all escalations and notify relevant personnel.

**For each escalated resource**:

1. **Generate escalation payload** {run_dir}/delete/escalations.json with escalation_id, resource_id, resource_type, decision_id, reason, error, recommended_action, escalated_at, escalated_to, required_response, and notification tracking.

2. **Send notification** to the Phase 5 decision maker:
   - Escalation type: ZOMBIE_BACKUP_FAILED
   - Recipient: Phase 5 decision maker (from decision_id record)
   - Content: escalated resource list, failure reasons, recommended actions

3. **Update progress** {run_dir}/delete/backup_episodes.json:
   - Mark escalation status
   - Record notification send time

4. **Output results** with escalation_processing summary (total, notifications sent, timestamp, status).


Write the output to the specified output file.

## Output
- **Schema:** schemas/escalations.schema.json
  - **File:** delete/escalations.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"handle_escalations"`
- Set `steps.handle_escalations` to `"completed"`
### Step 9: finalize

**Type:** inline
**Description:** Phase 8: Finalize and update task context

## Input Files
- `delete/backup_summary.json` (from Step generate_reports, schema: schemas/backup_summary.schema.json)
- `delete/escalations.json` (from Step handle_escalations, schema: schemas/escalations.schema.json)

## Execution
Follow these instructions:

Your task is to finalize the backup process and update task status.

**Steps**:

1. **Aggregate all reports**
   - Read {run_dir}/delete/backup_report_*.json
   - Count successful/failed/escalated

2. **Update progress file** {run_dir}/delete/backup_episodes.json with task_id, phase=phase_6_backup, status, completed_at, statistics, and result summary.

3. **Generate final report** {run_dir}/delete/backup_final_report.json with phase_6_backup_result: status, total, successful, escalations, output_files, next_phase, proceed_with_deletion flag, and decision_id.

4. **Return status** indicating success/partial_success/failed with counts, output file manifest, and whether deletion can proceed.


Write the output to the specified output file.

## Output
- **Schema:** schemas/backup_episodes.schema.json
  - **File:** delete/backup_episodes.json
- **Schema:** schemas/backup_final_report.schema.json
  - **File:** delete/backup_final_report.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"finalize"`
- Set `steps.finalize` to `"completed"`