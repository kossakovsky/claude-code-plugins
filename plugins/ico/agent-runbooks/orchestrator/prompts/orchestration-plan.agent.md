You are designing an execution plan for Zombie Resource Cost Optimization. Use this exact phase structure. Do not add, remove, or rename phases.

## Phase A: Discover & Screen

- **Skill**: zombie-metrics-collector
- **Dispatch**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-metrics-collector skill
- **Input**: intent_detection.json, scan_plan.json, run_dir
- **Task**: Discover all resources in scope. For each resource, collect 3 idle detection signals:

  **Signal 1 -- CPU daily average**: > 20% (14 days, 5-min intervals) -> ACTIVE
  **Signal 2 -- Network I/O**: > 2 GB/day in+out (14-day avg or 60s /proc/net/dev rate sample, exclude lo) -> ACTIVE
  **Signal 3 -- Human login**: any human login in 30 days -> ACTIVE

  ANY one signal hit -> resource is ACTIVE -> exclude.
  ALL three pass -> zombie candidate.
  The zombie-metrics-collector applies these same thresholds from its skill definition.

  **Do NOT check**: process list (ps aux), disk usage (df/du), crontab contents, system uptime, installed packages (dpkg/rpm), open ports (ss -tnp). These are for Phase D deep scan.

- **Output**: layer_b_candidates.json, layer_a_candidates.json, scan_episodes.json

## Phase B: Score & Rank

- **Skill**: zombie-resource-screener
- **Dispatch**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-resource-screener skill
- **Input**: layer_b_candidates.json, scan_plan.json, run_dir
- **Task**: Multi-dimension scoring per zombie-resource-screener runbook. Compute zombie_score, map suspect_level, compute priority. Score by estimated_monthly_cost descending.
- **Output**: suspect_assessment.json, zombie_suspect_{resource_id}.json

## Phase C: Review Gate (BLOCKING)

- **Task**: Present Phase B results sorted by cost descending. Show resource_id, suspect_level, zombie_score, priority, cost, key signals. User confirms which resources proceed.
- **Gate**: BLOCKING -- WAIT for user response before dispatching next phase.
- **Output**: phase1_review_decision.json

## Phase D: Deep Scan

- **Skill**: zombie-deep-scanner
- **Dispatch**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-deep-scanner skill
- **Input**: phase1_review_decision.json, run_dir, ssh_key_path
- **Task**: For each approved resource, launch one agent (max 8 concurrent). Collect technical info (processes, ports, crontab, systemd timers, disk, packages, local DB), business info (application, system, owner, recent changes, related resources), cost info (cloud bill actual or spec estimate).
- **Output**: deep_scan_{resource_id}.json per resource

## Phase E: Report

- **Task**: Read deep scan results. Generate a Markdown report with all resources using the Write tool (one section per resource with sub-sections: traffic, services, tasks, storage, ownership). Present to user. ASK: which resources should proceed to isolation planning? (multi-select). WAIT for user response. BLOCKING.
- **Gate**: BLOCKING -- WAIT for user response.
- **Output**: isolation_selection.json

## Phase F: Isolation Plan

- **Skill**: zombie-isolation-planner
- **Dispatch**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-isolation-planner skill
- **Input**: isolation_selection.json, suspect_assessment.json, deep_scan_{id}.json, run_dir
- **Task**: Generate per-resource isolation strategy with rollback, batch planning by blast radius, observation period config. Only plan for resources in isolation_selection.json.
- **Output**: isolation_batch_plan.json, isolation_plan_{id}.json

## Phase G: Isolation Review Gate (BLOCKING)

- **Task**: Compile isolation plan as markdown via the Write tool. User approves.
- **Gate**: BLOCKING -- WAIT for user response.
- **Output**: phase2_review_decision.json

## Phase H: Isolate & Observe

- **Skill**: zombie-isolation-executor
- **Dispatch**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-isolation-executor skill
- **Input**: isolation_batch_plan.json, isolation_plan_{id}.json, phase2_review_decision.json, run_dir
- **Task**: Execute isolation batches sequentially. Monitor observation period. P0/P1 anomalies trigger auto-rollback.
- **Output**: observation_{id}.json, observation_batch_summary.json

## Phase I: Decide & Execute

- **Skill**: zombie-decision-handler
- **Dispatch**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-decision-handler skill
- **Input**: deep_scan_{id}.json, observation_{id}.json, observation_batch_summary.json, run_dir
- **Task**: Merge results. Present decision report sorted by cost. User decides DELETE/KEEP_EXEMPT/EXTEND per resource. Write confirm/phase5_decision.json with delete_resources array for each resource marked DELETE. Do NOT dispatch backup-creator or resource-cleaner -- wait for Phase J gate.
- **Output**: confirm/phase5_decision.json, decision/user_decisions.json

## Phase J: Delete Review Gate (BLOCKING)

- **Task**: Read phase5_decision.json. For each resource marked DELETE, compile delete plan with backup status, deletion method, cost savings. Present via Write tool. User approves deletion.
- **Gate**: BLOCKING -- WAIT for user response before dispatching deletions.
- **Output**: phase_j_delete_approval.json

## Phase K: Execute Deletion

- **Task**: Read phase_j_delete_approval.json. For approved resources, dispatch zombie-backup-creator via Agent tool, then zombie-resource-cleaner via Agent tool. Track deletion results.
- **Dispatch backup-creator**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-backup-creator skill
- **Dispatch resource-cleaner**: Use the Agent tool (subagent_type=general-purpose) to load the zombie-resource-cleaner skill
- **Output**: delete/deletion_report.json

## Phase L: Deliver

- **Task**: Generate markdown dashboard via Write tool -- total scanned, deleted count, cost savings, per-resource decisions. Present to user.
