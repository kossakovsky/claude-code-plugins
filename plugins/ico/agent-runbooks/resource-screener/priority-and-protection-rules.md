# Priority Formula and Protection Rules Reference

## 1. Priority Ranking Formula

### 1.1 Full Formula

```
priority = min(1.0, (zombie_score x env_multiplier x cost_weight) + owner_bonus)
```

### 1.2 Factor Details

#### zombie_score

- Range: 0-1
- Source: Layer D weighted calculation result
- Higher score = stronger zombie suspicion

#### env_multiplier

Adjusts verification cost and priority for different environments. Production has the highest verification cost, so its priority is relatively lower to allow processing high-suspicion resources in lower environments first.

| Environment | Multiplier | Rationale |
|-------------|-----------|-----------|
| dev / development | 1.0 | Lowest verification cost, investigate first |
| staging / stage | 0.80 | Medium verification cost |
| prod / production | 0.60 | Highest verification cost (30-day isolation period, complex rollback), more caution needed |
| pre-prod / unknown | 0.60 | Unknown environments treated conservatively as production |
| test / testing | 1.0 | Same as dev |

#### cost_weight (Cost Weight)

Logarithmic transformation of estimated monthly cost, giving higher-cost resources higher priority while smoothing extreme costs.

**Calculation logic**:
```python
import math

cost = estimated_monthly_cost
if cost <= 0:
    cost_weight = 0.30  # Minimum weight for K8s resources, zero-cost resources
else:
    raw_weight = math.log10(cost + 1) / 3
    cost_weight = min(max(raw_weight, 0.30), 1.0)  # Clamp to [0.30, 1.0]
```

**Examples**:
| Monthly Cost | Calculation | cost_weight |
|--------------|-------------|-------------|
| $0 | log10(1)/3 = 0 -> floor 0.30 | 0.30 |
| $10 | log10(11)/3 ~ 0.35 | 0.35 |
| $100 | log10(101)/3 ~ 0.67 | 0.67 |
| $500 | log10(501)/3 ~ 0.90 | 0.90 |
| $1000 | log10(1001)/3 ~ 1.00 | 1.0 (cap) |
| $10000 | log10(10001)/3 ~ 1.33 -> cap 1.0 | 1.0 |

**Lower bound 0.30 rationale**: Prevents K8s resources (typically no monthly billing) and unbound EIPs from having priority=0, ensuring they still appear in candidate lists when suspicion is high.

#### owner_bonus

Extra bonus for resources without clear ownership, raising their processing priority (no owner coordination needed).

| Ownership Status | Bonus | Rationale |
|-----------------|-------|-----------|
| `untagged` | +0.10 | No ownership labels, highest urgency, easiest to process |
| `orphaned` | +0.05 | Creator left or team disbanded, no maintenance, second priority |
| `active_owner` | 0.0 | Has active owner, no adjustment |
| `shared` | 0.0 | Multi-owner, no adjustment |

### 1.3 Ranking Examples

**Example 1: Dev environment, high suspicion, medium cost, untagged**
```
Environment: dev, zombie_score=0.90, monthly=$500, owner_status=untagged
env_multiplier = 1.0
cost_weight = log10(501)/3 ~ 0.90
owner_bonus = 0.10
priority = (0.90 x 1.0 x 0.90) + 0.10 = 0.81 + 0.10 = 0.91
```

**Example 2: Production, medium suspicion, high cost, active owner**
```
Environment: prod, zombie_score=0.85, monthly=$2000, owner_status=active_owner
env_multiplier = 0.60
cost_weight = log10(2001)/3 ~ 1.00 (cap at 1.0)
owner_bonus = 0.0
priority = (0.85 x 0.60 x 1.0) + 0.0 = 0.51
```

**Example 3: K8s ConfigMap, low suspicion, zero cost, untagged**
```
Environment: dev, zombie_score=0.75, monthly=$0, owner_status=untagged
env_multiplier = 1.0
cost_weight = 0.30 (zero cost minimum)
owner_bonus = 0.10
priority = (0.75 x 1.0 x 0.30) + 0.10 = 0.225 + 0.10 = 0.325
```

Comparing three examples, Example 1 (high suspicion + medium cost + untagged dev resource) has the highest priority, consistent with the "easy first, hard later" investigation strategy.

### 1.4 Sorting Verification

In `suspect_assessment.json` `candidates[]`:
- Must be sorted by priority in descending order
- This is checked by self-check gate rule sc-005

---

## 2. Protection Rules (One-Vote Veto)

### 2.1 Protection Rule Concept

Protection rules use a **one-vote veto** mechanism: if any single protection rule triggers, `suspect_level` is forced to `low`, **regardless of the zombie_score calculation**.

This prevents false positives -- some resources may look like zombies but have clear known purposes (e.g., disaster recovery backups, archived data) and should not be marked as high suspicion.

### 2.2 Implemented Protection Rules

#### Rule 1: DR/Backup Protection (Exact Tag Match)

**Trigger condition**:
```
tags.purpose == "disaster-recovery" OR tags.purpose == "backup"
```

**Match example**:
```json
{
  "resource_name": "prod-db-instance",
  "tags": {
    "purpose": "disaster-recovery",
    "environment": "prod"
  }
}
```

**Result**: suspect_level forced to `low`

#### Rule 2: DR/Backup Protection (Semantic Naming Pattern)

**Trigger condition**: Resource name contains any of these prefixes (case-insensitive):
- `dr-` (disaster recovery)
- `backup-`
- `standby-`

Or tags contain:
- `role=standby`
- `usage=backup`

**Result**: suspect_level forced to `low`

**LLM judgment note**: Semantic naming patterns are heuristic and may produce false matches. When using semantic rules, output:
```json
{
  "protection_rules_checked": {
    "DR/backup_protection_semantic": true,
    "semantic_confidence": "high"
  }
}
```

### 2.3 Protection Rules Output Format

Each resource's `protection_rules_checked` object should list all checked rules and their results:

```json
{
  "protection_rules_checked": {
    "DR/backup_protection_tag": false,
    "DR/backup_protection_semantic": false
  }
}
```

If any rule is `true`, suspect_level is forced to `low`.

### 2.4 Pre-excluded by Layer A Coarse Screening

The following conditions are handled at **Layer A coarse screening** and should not reach Layer D:
- New resources (< 7 days) -- Layer A directly excludes
- Terminated/deleting/creating status -- Layer A directly excludes
- Newly registered domains (< 7 days) -- Layer A directly excludes

### 2.5 Future Protection Rules (Phase 2)

The following rules are reserved for future implementation when Phase 2 SSH data and dependency topology are available:

| Rule Name | Trigger Condition | Rationale |
|-----------|-------------------|-----------|
| `has_active_schedule` | crontab has tasks with interval >= weekly | Active scheduled tasks indicate resource is in use |
| `critical_dependency` | Depended on by other active resources | Deletion causes cascading failures |
| `recent_manual_access` | Human login/operation within 7 days | Recently maintained, not a zombie |
| `active_monitoring_alert` | Alert rules bound with history of triggers | Active monitoring indicates resource is watched |

---

## 3. Interaction with suspect_level Mapping

### 3.1 Mapping Flow

```
1. Compute zombie_score (weighted aggregation of all dimensions)
    |
2. Check protection rules (one-vote veto)
    |
    if any protection rule == true:
      suspect_level = "low"  -- forced, skip step 3
    else:
      continue to step 3
    |
3. Basic threshold mapping (with environment adjustment)
    if zombie_score >= (0.80 + env_adjustment):
      suspect_level = "high"
    elif zombie_score >= 0.55:
      suspect_level = "medium"
    else:
      suspect_level = "low"
```

### 3.2 Scripted Mapping Example

```python
def determine_suspect_level(zombie_score, environment, protection_rules):
    # Step 2: Protection rule check (one-vote veto)
    if any(protection_rules.values()):
        return "low"

    # Step 3: Environment-adjusted threshold mapping
    env_adjustments = {
        "prod": 0.10,
        "staging": 0.0,
        "dev": -0.05,
        "unknown": 0.10
    }
    adjustment = env_adjustments.get(environment, 0.10)
    high_threshold = 0.80 + adjustment

    if zombie_score >= high_threshold:
        return "high"
    elif zombie_score >= 0.55:
        return "medium"
    else:
        return "low"
```

---

## 4. Common Scenarios

### Scenario 1: High suspicion DB backup with DR tag

```
resource: rds-prod-backup-2026
zombie_score: 0.95 (zero connections, zero QPS)
tags: {"purpose": "disaster-recovery"}
protection_rules_checked: {"DR/backup_protection_tag": true}
-> suspect_level = "low"  -- protection rule forced
-> priority: low rank (usually not in top 30% of candidate list)
```

### Scenario 2: Name contains backup- but is actually a regular resource

```
resource: my-backup-script-vm
zombie_score: 0.88
owner_status: "active_owner"
protection_rules_checked: {"DR/backup_protection_semantic": true}  -- heuristic match
-> Requires LLM secondary judgment
-> If LLM confirms it is a real backup: suspect_level = "low"
-> If LLM confirms it is a false match: can re-evaluate suspect_level
```

### Scenario 3: Dev environment high suspicion untagged K8s ConfigMap

```
resource: old-config-map-v1
environment: "dev"
zombie_score: 0.85
estimated_monthly_cost: 0
owner_status: "untagged"
priority = (0.85 x 1.0 x 0.30) + 0.10 = 0.355
-> Medium rank in candidate list (cost is 0, but strong suspicion + no owner)
```

---

## 5. Data Quality Marking

Record dimension data completeness in each resource's `data_quality` field for Phase 2 collection optimization:

```json
{
  "data_quality": {
    "valid_dimensions": ["cpu_memory", "network_throughput"],
    "unreliable_dimensions": ["access_activity", "login_history", "cron_tasks"],
    "overall_confidence": 0.55,
    "notes": "SSH-dependent dimensions unavailable in Phase 1; will be enriched in Phase 2"
  }
}
```
