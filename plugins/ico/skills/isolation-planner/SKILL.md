---
name: isolation-planner
description: >-
  Generates human-executable isolation plans for zombie resources identified in Phase 1/2. Creates per-resource isolation strategies with pre-checklists, rollback procedures, and observation configurations, plus a global batch plan sorted by dependency safety. Never auto-executes isolation; all decisions remain with humans.
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Workspace root directory for file passing between agents |
| ssh_key_path | string | No | SSH key path for cloud provider access |
| environment | string | Yes | Target environment for isolation method selection |

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
    "phase3_plan_generation": "pending",
    "phase3_batch_planning": "pending",
    "phase3_review_gate": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: phase3_plan_generation

**Type:** inline
**Description:** Read Phase 1/2 output and generate per-resource isolation plans

## Execution
Follow these instructions:

Read Phase 1/2 output files from {run_dir}/analysis/:
- suspect_assessment.json
- zombie_suspect_{resource_id}.json (per resource, from Phase 1 resource-screener)
- deep_scan_{resource_id}.json (per resource, from Phase 2 deep-scanner)

For each resource with suspect_level in {high, medium}:

1. **Data Extraction**:
   - suspect_level, zombie_score, priority, owner_detail: from zombie_suspect_{resource_id}.json
   - owner name, team: from deep_scan_{resource_id}.json `business.owner`
   - related_resources (blast_radius / dependency graph): from deep_scan_{resource_id}.json `business.related_resources`

2. **Method Selection**: Use the isolation strategy matrix (by resource_type x environment)
   to select the primary isolation method. If preconditions fail, use fallback.

   **Isolation Strategy Matrix**:
   - CloudVM: iptables DROP (all envs) | Fallback: stop_instance
   - CloudRDS: deny_sg_all_inbound (all envs)
   - CloudCache: clear_ip_whitelist (all envs)
   - K8sWorkload: scale_to_zero (all envs)
   - K8sService: unmatchable_selector (all envs)
   - K8sCronJob: suspend (all envs)
   - CloudLoadBalancer: remove_all_backends (all envs)
   - CloudEIP: unbind (all envs)
   - K8sConfig: label_isolated + backup (all envs)
   - ServiceMesh: remove_from_mesh + sidecar_disable (staging/prod) | remove_from_mesh (dev)
   - AppConfig: config_snapshot + deactivate (all envs)

3. **Per-Resource Plan Generation**: For each candidate, create {run_dir}/analysis/isolation_plan_{resource_id}.json with:
   - metadata: resource_id, resource_type, entity_type, environment, suspect_level, zombie_score, priority
   - isolation_strategy: method_id, method_name, description, rationale
   - isolation_steps: [list of human-executable steps with verification commands]
   - pre_checklist: [resource-type-specific pre-checks with MUST_PASS/SHOULD_PASS status]
   - rollback_plan: method_id, method_name, estimated_time, steps
   - observation_config: observation_period_days, metrics_to_monitor, success_criteria, auto_rollback_triggers
   - risk_assessment: critical_dependencies, blast_radius_summary, isolation_side_effects, special_warnings
   - quality_checks: completeness and consistency validation results

4. **Data Validation**: Before generating plans, validate:
   - All candidates have resource_id, resource_type, environment
   - resource_type is in SUPPORTED_TYPES
   - suspect_level is high or medium
   - blast_radius is populated (from deep_scan business.related_resources)
   - owner_detail is populated (from deep_scan business.owner)

5. **Pre-Checklist Generation**: Create resource-type-specific pre-checks:
   - Universal checks: backup availability, rollback dependencies, no ongoing changes, on-call notification
   - CloudVM: SSH connectivity, iptables availability, rules backed up, not in Auto Scaling group
   - CloudRDS: security group modifiable, no ongoing maintenance, backup available
   - CloudCache: active connections count checked (do not isolate if serving traffic), persistence config verified (RDB/AOF backup status), confirmed not a shared cluster
   - K8sWorkload: HPA status confirmed, replicas recorded, no PDB conflicts
   - K8sService: endpoint count checked, headless service verified, external traffic policy recorded
   - K8sCronJob: active jobs count checked, suspend status verified, concurrency policy recorded
   - Load balancer / Elastic IP: backend configuration recorded, DNS records checked
   - K8sConfig: backup created, no active mounts
   - ServiceMesh: control plane accessibility confirmed, sidecar injection status recorded, traffic policies backed up
   - AppConfig: config backup created, no active deployments using this config

6. **Observation Period Configuration**:
   - dev: 3 days
   - staging: 7 days
   - prod: 30 days
   - Include metrics_to_monitor per resource type
   - Include auto_rollback_triggers with P0/P1/P2 severity levels
   - Include success_criteria for phase transition

7. **Quality Checks**: Validate each plan:
   - method_assigned: isolation_strategy.method_id is not null
   - steps_documented: isolation_steps has >= 3 items with descriptions
   - rollback_complete: rollback_plan.steps has >= 2 items
   - observation_configured: observation_config has metrics + period + triggers
   - dependency_analyzed: risk_assessment.blast_radius_summary is populated

Write each plan to {run_dir}/analysis/isolation_plan_{resource_id}.json


Write the output to the specified output file.

## Output
- **Schema:** schemas/isolation-plan.schema.json
  - **File:** analysis/isolation_plan_{resource_id}.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase3_plan_generation"`
- Set `steps.phase3_plan_generation` to `"completed"`
### Step 2: phase3_batch_planning

**Type:** inline
**Description:** Analyze dependencies and group resources into safe execution batches

## Execution
Follow these instructions:

Read all isolation_plan_{resource_id}.json files and deep_scan_{resource_id}.json files.

**Dependency Graph Construction** (from deep_scan files):
- For each candidate, extract `business.related_resources` from its deep_scan_{resource_id}.json
- Build a directed graph: resource_id -> each related resource in `business.related_resources`
- Cross-reference: if resource A lists B in related_resources, and B is also a candidate, edge A -> B exists

**Batch Grouping Algorithm**:

1. **Detect Strongly Connected Components (SCCs)**: Use Tarjan's algorithm to find circular dependencies
   - Zombie chains (circular dependencies) must be grouped as single atomic batches
   - Each SCC becomes a batch or part of a batch

2. **Build SCC DAG**: Create a directed acyclic graph of SCCs
   - Edge A -> B means SCC(A) must be isolated before SCC(B)

3. **Topological Sort**: Order SCCs by dependency
   - Resources with no upstream dependencies come first
   - Resources with dependencies come after their dependencies

4. **Batch Creation**: For each SCC in topological order:
   - batch_id: sequential number (1, 2, 3, ...)
   - resource_ids: list of resources in batch
   - parallelizable: true if no internal edges, false if sequential ordering needed
   - ordering: if sequential, provide step-by-step ordering with rationale
   - rationale: plain-English explanation of grouping

5. **Batch Categories**:
   - **Independent Leaf Resources**: No dependencies; can parallelize
   - **Sequential Chains**: A -> B -> C; must execute in order
   - **Zombie Chains**: Circular dependencies; treat as atomic group
   - **Manual Review**: [UNKNOWN] dependencies; require human validation

6. **Global Execution Plan**:
   - recommended_sequence: ordered list of batch execution
   - total_estimated_time: sum of batch execution times
   - critical_path: longest single-threaded path
   - parallelization_opportunities: which batches can run in parallel

7. **Safety Validations**:
   - no_critical_dependency_violations: true if no batch isolates a dependency before its dependent
   - all_blast_radius_analyzed: true if all resources have blast_radius
   - zombie_chains_grouped: true if all circular dependencies are in same batch
   - batch_order_safe: true if topological order is respected

Write result to {run_dir}/analysis/isolation_batch_plan.json with:
  metadata: generated_at, environment, total_candidates, high_priority_count, medium_priority_count, total_batches
  batches: [array of batch objects]
  global_execution_plan: sequence, timing, critical path
  dependency_graph_summary: total resources, edges, SCCs, circular groups
  safety_validations: all checks passed/failed


Write the output to the specified output file.

## Output
- **Schema:** schemas/isolation-batch-plan.schema.json
  - **File:** analysis/isolation_batch_plan.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase3_batch_planning"`
- Set `steps.phase3_batch_planning` to `"completed"`
### Step 3: phase3_review_gate

**Type:** inline
**Description:** Present isolation plans to user for approval before Phase 4 execution

## Input Files
- `analysis/isolation_batch_plan.json` (from Step phase3_batch_planning, schema: schemas/isolation-batch-plan.schema.json)

## Execution
Follow these instructions:

Read {run_dir}/analysis/isolation_batch_plan.json.

**Pre-Review Validation**:
- Verify all isolation_plan_{resource_id}.json files exist for all candidates
- Check isolation_batch_plan.json has complete batch definitions
- Confirm all quality checks passed or are documented as warnings

Present to user:

1. **Summary**:
   - Total resources to isolate: {total_candidates}
   - High priority: {high_priority_count} | Medium: {medium_priority_count}
   - Total batches: {total_batches}
   - Estimated total time: {total_estimated_time}

2. **Batch Plan**:
   - For each batch: batch_id, description, resource_ids, parallelizable, estimated_execution_time
   - Dependency ordering: which batches must run sequentially, which can parallelize
   - Critical path: longest single-threaded path

3. **Per-Resource Details** (top 5 by priority):
   - resource_id, resource_type, environment, suspect_level, zombie_score
   - isolation_method, observation_period_days, rollback_estimated_time
   - blast_radius_summary: affected_services_count, critical_path_detected
   - special_warnings: any resource-specific risks

ASK user:
- Approve all isolation plans? Or review per-resource?
- Any resources to skip or adjust isolation method?
- Confirm observation period duration per environment?
- Any concerns about batch ordering or parallelization?

WAIT for user response. This is a BLOCKING GATE.
DO NOT execute any isolation without explicit user approval.

After user responds, write {run_dir}/analysis/user_approval_decision.json:
  metadata:
    decision_timestamp: ISO8601 timestamp
    approval_status: approved/rejected/partial_approval
  approved_resources: [list of resource_ids approved for isolation]
  skipped_resources: [{resource_id, reason}]
  adjusted_observation_periods: {resource_id: new_days}
  batch_plan_approved: true/false
  user_notes: string

Only proceed to Phase 4 if batch_plan_approved == true and approved_resources is non-empty.


Write the output to the specified output file.

## Output
- **Schema:** schemas/user-approval-decision.schema.json
  - **File:** analysis/user_approval_decision.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"phase3_review_gate"`
- Set `steps.phase3_review_gate` to `"completed"`

## Error Handling

### Phase 3 finds 0 high/medium candidates

Normal termination: no resources require isolation. Present summary and exit.

### Isolation method not found for resource type

Mark resource as method_missing, flag for manual isolation, skip in batch plan.

### Dependency topology incomplete ([UNKNOWN] entries)

Isolate resource in separate manual-review batch, require human validation before execution.

### Circular dependency detected (zombie chain)

Group all resources in cycle as single atomic batch for synchronized observation and rollback.

### Pre-checklist validation fails for resource

Mark resource with failed_preconditions, include in plan with warning, require manual review before execution.

### Quality check blocks plan

Return plan for revision. Max 3 revision rounds. If still failing, escalate to admin.

### User rejects isolation plan at review gate

Save user decision to user_approval_decision.json. Skip Phase 4 for rejected resources. Proceed with approved resources only.

### Rollback time estimate > 30 minutes

Flag as warning in quality check. Proceed if user approves, but require extended observation period.

### Critical dependency detected in blast_radius

Flag in risk_assessment.critical_dependencies with HIGH risk_level. Include mitigation steps in plan.
