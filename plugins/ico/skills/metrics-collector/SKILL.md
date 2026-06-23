---
name: metrics-collector
description: >-
  Phase 1 Suspect: Discover cloud resources and apply idle detection signals to identify zombie candidates.
  Prefer cloud monitoring API (CloudWatch/Prometheus/Datadog) for historical metrics. SSH fallback: see prompts/signals-compute.md for in-VM collection rules.
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Working directory absolute path for input/output files |
| ssh_key_path | string | No | SSH key path for cloud tags queries and reachability checks |
| task_id | string | Yes | Task ID for progress tracking in scan_episodes.json |

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
    "layer_a1_discovery": "pending",
    "layer_a2_exclusion": "pending",
    "layer_b1_metrics": "pending",
    "layer_b2_exclusion": "pending",
    "finalize_output": "pending",
    "review_signals": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: layer_a1_discovery

**Type:** inline
**Description:** Layer A.1: Discover all resources via cloud CLI and API tools per entity_type

## Execution
Follow these instructions:

Read {run_dir}/intent_detection.json and {run_dir}/connection_config.json.
Discover all cloud resources in scope. For each resource, extract:
resource_id, resource_name, entity_type, resource_type, environment,
tags, provisioned_at, private_ip, status, spec, cost.
For compute resources, also detect virt_type (lxc/kvm/bare-metal/unknown).
Estimate monthly cost from spec: vCPU × $20 + RAM_GB × $3 + disk_GB × $0.10.

Write {run_dir}/layer_a_raw_resources.json.
Update {run_dir}/scan_episodes.json with scan_status="phase1_layer_a1_completed".


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"layer_a1_discovery"`
- Set `steps.layer_a1_discovery` to `"completed"`
### Step 2: layer_a2_exclusion

**Type:** inline
**Description:** Layer A.2: Apply coarse exclusion rules to Layer A candidates

## Execution
Follow these instructions:

Apply coarse exclusion rules to filter out obviously non-candidate resources.

**Input**: {run_dir}/layer_a_raw_resources.json

**Exclusion rules** (deterministic):
1. New resources: provisioned_at within N days -> exclude, reason="new_resource".
   N depends on environment: dev=1 day, staging=3 days, prod=7 days.
   If environment is unknown, default to 7 days.
2. Non-ready status: status in [terminated, deleting, creating] -> exclude, reason="not_ready"
3. DR/backup tags: tags contain purpose=disaster-recovery or purpose=backup -> exclude, reason="dr_backup_tag"
4. Recent CI/CD deployment: if the workload has been deployed via the user's CI/CD tool within N days -> exclude, reason="active_cicd". N depends on environment: dev=7, staging=30, prod=90. If no CI/CD tool is configured, skip this rule. For K8s workloads without CI/CD access, check ReplicaSet creation timestamps as a proxy.

**LLM semantic check** (supplemental, for resources not already excluded):
- Check if resource name contains dr-, backup-, standby- prefix
- Check if tags contain role=standby, usage=backup
- If matched, mark as "potential_dr_backup" but still include in candidates


Write the output to the specified output file.

## Output
- **Schema:** schemas/layer-a-candidates.schema.json
  - **File:** layer_a_candidates.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"layer_a2_exclusion"`
- Set `steps.layer_a2_exclusion` to `"completed"`
### Step 3: layer_b1_metrics

**Type:** inline
**Description:** Layer B.1: Collect idle/zombie detection signals per resource type

## Execution
Follow these instructions:

Collect idle/zombie detection signals for each resource in {run_dir}/layer_a_candidates.json.

For signal definitions and per-resource-type thresholds, read prompts/signals-*.md.

Collect idle detection signals for each Layer A candidate based on its resource_type.

**Input**: {run_dir}/layer_a_candidates.json

**Signal rules by resource type** (read the reference file for detailed thresholds and edge cases):
| resource_type | Reference file |
|--------------|---------------|
| compute | `$PLUGINS/ico/skills/metrics-collector/prompts/signals-compute.md` |
| database, cache | `$PLUGINS/ico/skills/metrics-collector/prompts/signals-database.md` |
| storage | `$PLUGINS/ico/skills/metrics-collector/prompts/signals-storage.md` |
| network | `$PLUGINS/ico/skills/metrics-collector/prompts/signals-network.md` |
| k8s_workload | `$PLUGINS/ico/skills/metrics-collector/prompts/signals-k8s-workload.md` |
| k8s_service, k8s_orphan | `$PLUGINS/ico/skills/metrics-collector/prompts/signals-k8s-service.md` |
| object_storage | `$PLUGINS/ico/skills/metrics-collector/prompts/signals-object-storage.md` |
| domain | no signals available; mark unmeasurable, skip to manual review |

**CRITICAL — Threshold source**: All signal thresholds, units, and collection methods come ONLY from the `$PLUGINS/ico/skills/metrics-collector/prompts/signals-{type}.md` reference files. DO NOT use thresholds from scan_plan.json, intent_detection.json, or any other file. DO NOT add extra signals (memory, disk_io, connections) beyond what the reference file defines. Collect ONLY the signals listed in the table above.

**Execution**:
1. For each candidate, determine resource_type
2. Read the corresponding reference file for signal definitions, thresholds, and data sources
3. Collect signals using available cloud CLI tools (cloud monitoring API preferred over in-VM /proc)
4. For each signal, record: value, threshold, threshold_unit, is_active (value exceeds threshold → true), reliability, data_source
5. Downstream consumers read `is_active` and `threshold` directly — do NOT make them guess or derive from signal values

**Rules**:
- Data collection fails → reliability=0.0, data_source="failed"
- ALL signals fail → "unmeasurable", do NOT classify as zombie
- Batch timeout → retry once; still failing → reliability=0.0 for that signal


Write the output to the specified output file.

## Output
- **Schema:** schemas/layer-b-candidates.schema.json
  - **File:** layer_b_raw_signals.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"layer_b1_metrics"`
- Set `steps.layer_b1_metrics` to `"completed"`
### Step 4: layer_b2_exclusion

**Type:** inline
**Description:** Layer B.2: Apply per-type signal rules to identify zombie candidates

## Execution
Follow these instructions:

Apply idle detection rules per resource_type to determine zombie candidates.

**Input**: {run_dir}/layer_b_raw_signals.json

**The Rule** (same for all resource types):
- ANY signal exceeds its threshold (defined in prompts/signals-{type}.md) → ACTIVE → exclude
- ALL signals below threshold → CANDIDATE (potential zombie)
- ALL signals reliability=0.0 → UNMEASURABLE → separate array, do NOT classify

**Edge cases**:
- Signal reliability=0.0 for some but not all signals: treat failed ones as "below threshold". Mark low_confidence_signals=true
- Borderline values: check threshold range in the reference file. Mark low_confidence_signals=true
- resource_type with no reference file (e.g. domain): mark unmeasurable, skip


Write the output to the specified output file.

## Output
- **Schema:** schemas/layer-b-candidates.schema.json
  - **File:** layer_b_candidates.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"layer_b2_exclusion"`
- Set `steps.layer_b2_exclusion` to `"completed"`
### Step 5: finalize_output

**Type:** inline
**Description:** Finalize output, collect candidate context info, and update progress

## Execution
Follow these instructions:

Finalize output, collect candidate context, and update tracking.

**Verification**: Verify {run_dir}/layer_a_candidates.json and {run_dir}/layer_b_candidates.json exist and are valid JSON.

**Candidate context**: For each candidate, collect and append as `context_info` block:
1. Owner: from resource tags / cloud audit logs / IaC git blame / cloud tags
2. Blast radius: what depends on this resource, what would break if deleted
3. Reachability: for compute, check SSH/API access and record reachable status

**Update**: Set scan_episodes.json → scan_status: "phase1_discovery_complete", completed_at.

**Log summary**: Layer A/B counts, filter rates, excluded_reasons, tool failures, skipped types.

Edge case: 0 candidates → scan_status "phase1_discovery_complete_zero_candidates" or "_all_active".


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"finalize_output"`
- Set `steps.finalize_output` to `"completed"`
### Step 6: review_signals

**Type:** inline
**Description:** Validate Phase A output before passing to screener (BLOCKING)

## Execution
Follow these instructions:

Read these output files and validate them before completing this skill:

layer_b_raw_signals.json — every signal MUST have: value, threshold, threshold_unit, is_active, reliability, data_source
layer_b_candidates.json — all required schema fields present: candidates[], total counts, filter_rate

If any field is missing or any value is a placeholder ("N/A", "NONE", "0.00 MB" without real data), mark that resource as unmeasurable.
Fix any issues before completing. BLOCKING.


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"review_signals"`
- Set `steps.review_signals` to `"completed"`

## Error Handling

### zero_candidates_after_layer_a

candidates_count == 0 after Layer A.2 → log warning, write empty candidates, skip Layer B, scan_status=phase1_discovery_complete_zero_candidates

### zero_candidates_after_layer_b

layer_b_candidates_count == 0 after Layer B.2 → normal for healthy infra, write empty candidates, scan_status=phase1_discovery_complete_all_active

### tool_unavailable

cloud CLI tool fails for one entity_type → skip it, record in skipped_entity_types[], continue. All fail → abort.

### single_signal_collection_failure

1-3 signals fail (at least 1 has real data) → reliability=0.0 + data_source=failed. During B.2 exclusion: treat as below threshold, mark low_confidence_signals=true.

### all_signals_failed

ALL signals placeholder or failed → UNMEASURABLE. Write to unmeasurable_hosts[], do NOT classify as zombie. > 30% unmeasurable → abort (collection method broken).

### batch_timeout_in_layer_b

Batch query timeout → retry once with smaller batch. Still failing → all affected resources reliability=0.0 for that signal, continue.
