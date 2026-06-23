---
name: deep-scanner
description: >-
  Phase 2 Deep Scanner — performs deep technical and business scanning on
  candidate machines approved by the user. One agent per machine, max 8 concurrent.
  Agent uses whatever tools available (SSH/cloud APIs).
  
user-invocable: true
---

## Input Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| run_dir | string | Yes | Workspace root directory |
| resource_id | string | Yes | Single resource ID to scan |
| ssh_key_path | string | No | SSH key path for remote access |

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
    "deep_scan": "pending",
    "review_deep_scan": "pending"
  },
  "updated_at": "<ISO timestamp>"
}
```

Update this file after each step completes. On error, set step status to `"failed"` and overall `status` to `"failed"`.

### Step 1: deep_scan

**Type:** agent
**Description:** Execute deep scan on target machine

## Execution
Launch an independent agent with the following prompt file:

**Prompt file:** `$PLUGINS/ico/skills/deep-scanner/prompts/deep-scan.agent.md`
**Agent workflow:**

1. Prepare the execution environment

2. Execute the agent with the prompt

3. Write results to:
   - File: `analysis/deep_scan_{resource_id}.json`

## Output
- **Schema:** schemas/deep-scan.schema.json
  - **File:** analysis/deep_scan_{resource_id}.json

### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"deep_scan"`
- Set `steps.deep_scan` to `"completed"`
### Step 2: review_deep_scan

**Type:** inline
**Description:** Validate deep scan output before completing (BLOCKING)

## Execution
Follow these instructions:

Read all deep_scan output files and validate them before completing:

Each deep_scan_*.json MUST have:
- technical.processes[] (non-empty)
- technical.listening_ports[] (non-empty)
- technical.traffic_graph with edges[] array (iftop data collected)
- technical.crontab_entries[] present
- technical.systemd_timers[] present
- technical.disk_partitions[] present
- technical.external_traffic[] present (ss -tn output)
- business.owner with name, team fields
- business.application non-empty

Do NOT include ssh_key_path or any credential paths in output.
Fix any issues before completing. BLOCKING.


### Progress Tracking

After completing this step, update `task_context.json`:
- Set `current_step_id` to `"review_deep_scan"`
- Set `steps.review_deep_scan` to `"completed"`