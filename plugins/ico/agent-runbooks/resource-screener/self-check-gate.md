# Self-Check Gate Reference

## Overview

Phase 1 must pass 10 blocking rules (self-check gate) before generating `suspect_assessment.json`. Any rule failure halts the process, prevents output file writing, and requires fixes before re-running.

These rules target:
1. Preventing common LLM hallucinations (fabricated values, forbidden field residue)
2. Ensuring data quality and consistency
3. Enforcing business rules (e.g., conservative thresholds for production environments)

---

## 10 Blocking Rules

### sc-001: High-suspect candidates must have sufficient CONFIRMED evidence

**Rule**: Each `suspect_level == "high"` candidate must have at least 3 items marked `[CONFIRMED]`. If the resource type has <= 3 total dimensions, at least 2 `[CONFIRMED]` items are required.

```python
for candidate in suspects:
    if candidate["suspect_level"] == "high":
        confirmed_count = sum(
            1 for e in candidate.get("evidence", [])
            if "[CONFIRMED]" in e.get("marker", "")
        )
        num_dims = len(candidate.get("evidence", []))
        min_required = 2 if num_dims <= 3 else 3

        if confirmed_count < min_required:
            failures.append({
                "rule": "sc-001",
                "resource_id": candidate["resource_id"],
                "message": f"High suspect with {confirmed_count} CONFIRMED evidence (need {min_required})"
            })
```

---

### sc-002: blast_radius must not contain numeric fields

**Rule**: Each `blast_radius` object must not contain any numeric scoring fields (e.g., `blast_radius_score`, `impact_level`, `dependency_count`). Only natural language description (`summary`) and relationship lists (`depends_on`, `dependencies`) are allowed.

```python
for candidate in suspects:
    blast = candidate.get("blast_radius", {})
    if isinstance(blast, dict):
        numeric_patterns = ["score", "count", "level", "rating"]
        numeric_fields = [
            k for k in blast.keys()
            if any(p in k.lower() for p in numeric_patterns)
        ]
        if numeric_fields:
            failures.append({
                "rule": "sc-002",
                "resource_id": candidate["resource_id"],
                "message": f"blast_radius has numeric fields: {numeric_fields}"
            })
```

---

### sc-003: Each candidate must have investigation_brief

**Rule**: Each candidate's `investigation_brief` must be a non-empty string, recommended 15-300 characters (2-3 sentences).

```python
for candidate in suspects:
    brief = candidate.get("investigation_brief", "").strip()
    if not brief or len(brief) < 10:
        failures.append({
            "rule": "sc-003",
            "resource_id": candidate["resource_id"],
            "message": f"Missing or empty investigation_brief"
        })
```

---

### sc-004: Production high-suspect candidates must have zombie_score >= 0.90

**Rule**: For `environment == "prod"` and `suspect_level == "high"` candidates, `zombie_score >= 0.90` is required. This enforces the production conservative threshold, preventing low-score resources from being misclassified as high suspicion due to cost_weight or owner_bonus boosts.

```python
for candidate in suspects:
    if (candidate.get("environment") == "prod" and
        candidate["suspect_level"] == "high" and
        candidate["zombie_score"] < 0.90):
        failures.append({
            "rule": "sc-004",
            "resource_id": candidate["resource_id"],
            "message": f"Prod high suspect with score {candidate['zombie_score']} < 0.90"
        })
```

---

### sc-005: candidates[] must be sorted by priority descending

**Rule**: In `suspect_assessment.json`, `candidates[]` must be strictly sorted by `priority` in descending order.

```python
priorities = [c["priority"] for c in assessment_data["candidates"]]
if priorities != sorted(priorities, reverse=True):
    failures.append({
        "rule": "sc-005",
        "message": "candidates not sorted by priority descending"
    })
```

---

### sc-006: Forbidden deprecated fields must not appear

**Rule**: The following field names must not appear in output (deprecated from old design):
- `safe_to_delete`
- `verdict`
- `confidence` (use `zombie_score` instead)
- `recommendation`

```python
forbidden_fields = ["safe_to_delete", "verdict", "confidence", "recommendation"]
for candidate in suspects:
    found = [f for f in forbidden_fields if f in candidate]
    if found:
        failures.append({
            "rule": "sc-006",
            "resource_id": candidate["resource_id"],
            "message": f"Forbidden fields: {found}"
        })
```

---

### sc-007: Each candidate must have complete suggested_verification

**Rule**: Each candidate's `suggested_verification` must contain all required fields:
- `verification_type` (api_only / ssh_required / manual_review / owner_inquiry / dependency_analysis)
- `methods` (string array)
- `estimated_effort_hours` (number)
- `escalation_required` (boolean)
- `precautions` (string array)

```python
required_keys = ["verification_type", "methods", "estimated_effort_hours", "escalation_required", "precautions"]
for candidate in suspects:
    verify = candidate.get("suggested_verification", {})
    missing = [k for k in required_keys if k not in verify]
    if missing:
        failures.append({
            "rule": "sc-007",
            "resource_id": candidate["resource_id"],
            "message": f"suggested_verification missing: {missing}"
        })
```

---

### sc-008: Each candidate must have valid owner_status

**Rule**: Each candidate's `owner_status` must be one of: `active_owner`, `orphaned`, `untagged`, `shared`.

```python
valid_statuses = ["active_owner", "orphaned", "untagged", "shared"]
for candidate in suspects:
    status = candidate.get("owner_status", "")
    if status not in valid_statuses:
        failures.append({
            "rule": "sc-008",
            "resource_id": candidate["resource_id"],
            "message": f"Invalid owner_status: '{status}'"
        })
```

---

### sc-009: Suspicion level distribution sanity check

**Rule**:
- `high_suspect` count must not exceed 30% of total candidates
- `medium_suspect` count must not exceed 50% of total candidates

This prevents scoring system drift (e.g., data quality issues causing massive false positives).

```python
summary = assessment_data["summary"]
total = summary["total_candidates"]
if total > 0:
    if summary["high_suspect"] > total * 0.30:
        failures.append({
            "rule": "sc-009",
            "message": f"High suspects {summary['high_suspect']} > 30% of {total}"
        })
    if summary["medium_suspect"] > total * 0.50:
        failures.append({
            "rule": "sc-009",
            "message": f"Medium suspects {summary['medium_suspect']} > 50% of {total}"
        })
```

---

### sc-010: Summary statistics must match actual distribution

**Rule**: The `summary` counts (`high_suspect`, `medium_suspect`, `low_suspect`) must match the actual distribution in `candidates[]`.

```python
actual_high = sum(1 for c in candidates if c["suspect_level"] == "high")
actual_med = sum(1 for c in candidates if c["suspect_level"] == "medium")
actual_low = sum(1 for c in candidates if c["suspect_level"] == "low")

summary = assessment_data["summary"]
if not (summary["high_suspect"] == actual_high and
        summary["medium_suspect"] == actual_med and
        summary["low_suspect"] == actual_low):
    failures.append({
        "rule": "sc-010",
        "message": f"Summary mismatch: summary=({summary['high_suspect']}, {summary['medium_suspect']}, {summary['low_suspect']}), actual=({actual_high}, {actual_med}, {actual_low})"
    })
```

---

## Failure Handling Flow

When any rule fails:

1. **Log detailed error**:
   ```python
   self_check_result = {
       "status": "blocked",
       "failures": [...],
       "failed_count": len(failures),
       "message": f"Self-check gate blocked: {len(failures)} violation(s)"
   }
   ```

2. **Halt output file writes**: Do not write `suspect_assessment.json`, retain partial files for debugging

3. **Return failure status** to upstream, requiring fixes:
   - Fix source data or calculation logic
   - Re-run the runbook
   - Re-check the self-check gate

4. **Optionally log to scan_episodes.json**

---

## Common Trigger Scenarios and Fixes

| Scenario | Root Cause | Fix |
|----------|-----------|-----|
| sc-001 fails: too few CONFIRMED | LLM generated evidence but marked most as SUPPORTED/INFERRED | Require actual data values in evidence, not speculation |
| sc-002 fails: blast_radius has scores | LLM mixed numeric scores into NL description | Explicitly forbid numeric fields in LLM prompt |
| sc-006 fails: deprecated fields | LLM hallucinated `confidence` or `safe_to_delete` fields | Strictly constrain LLM output to schema-defined fields |
| sc-009 fails: too many high suspects | Data quality issue (all monitoring APIs returned 0) | Check upstream Layer B data, may need re-collection |
| sc-010 fails: count mismatch | Summary was generated before all candidates processed | Re-count from `candidates[]` and update `summary` |

---

## Design Principles

The self-check gate embodies Phase 1 Suspect layer core design principles:

1. **Quality first**: Better to fail than output flawed scores
2. **Anti-hallucination**: Enforce checks on common LLM fabrication patterns
3. **Consistency**: Ensure internal data consistency
4. **Auditability**: Clear failure reasons for quick fixes

With these 10 rules, Phase 1 output can be confidently consumed by subsequent phases.
