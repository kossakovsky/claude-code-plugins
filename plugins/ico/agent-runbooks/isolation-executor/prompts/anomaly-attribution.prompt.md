# 3D Anomaly Attribution Prompt

You are analyzing anomalies detected during the observation period to determine whether they were caused by the isolation operation.

## Attribution Framework

An anomaly is considered "caused by isolation" if ≥ 2 of 3 dimensions match:

### Dimension 1: Temporal Association

Measure the time gap between isolation and anomaly:

```
gap_minutes = (anomaly_timestamp - isolation_executed_at) / 60

if gap_minutes <= 120:
    temporal_score = 1.0  # High correlation
elif gap_minutes <= 360:
    temporal_score = 0.7  # Moderate correlation
elif gap_minutes <= 1440:
    temporal_score = 0.4  # Weak correlation
else:
    temporal_score = 0.0  # Negligible
```

**Rationale**: Anomalies within 2 hours are highly suspect. Anomalies after 24 hours are likely unrelated (either cascading effects have stabilized or coincidence).

### Dimension 2: Topological Association

Examine the dependency topology:

```
if anomaly_resource in blast_radius.affected_services:
    topological_score = 1.0  # Direct blast radius hit

elif anomaly_resource reachable from isolated_resource within 2 hops:
    topological_score = 0.6  # Indirect dependency

else:
    topological_score = 0.0  # No topological relationship
```

**Rationale**: If the anomaly occurs in a service we explicitly identified as downstream, it's directly related. If it's 2 hops away, there's plausible causation. If unrelated in the dependency graph, unlikely to be caused.

### Dimension 3: Directional Association

Analyze the direction of the isolation and anomaly:

```
if isolated_resource_is_provider AND anomaly_source_is_consumer:
    directional_score = 1.0  # Isolation of provider breaks consumer

elif isolated_resource_is_consumer AND anomaly_source_is_provider:
    directional_score = 0.0  # Isolation of consumer doesn't affect provider

elif isolated_resource_is_peer AND anomaly_source_is_peer:
    directional_score = 0.5  # Horizontal relationship, unclear

else:
    directional_score = 0.0
```

**Rationale**: If we isolated an upstream service (provider), downstream services fail. If we isolated a downstream consumer, upstream services won't be affected.

## Attribution Decision

After computing all three scores:

```
scores = [temporal_score, topological_score, directional_score]
non_zero_count = count of scores > 0

if non_zero_count >= 2:
    attribution_result = "CONFIRMED"
    confidence = "high"
    reason = f"Scores: temporal={temporal_score}, topo={topological_score}, direction={directional_score}"

elif non_zero_count == 1:
    attribution_result = "UNCERTAIN"
    confidence = "low"
    reason = f"Only 1 dimension matched. Scores: {scores}"

else:
    attribution_result = "DISMISS"
    confidence = "none"
    reason = "No dimensional match — likely unrelated incident"
```

## Examples

### Example 1: CONFIRMED Related

```
Isolated: Redis (password change)
Anomaly: "Cache miss rate spiked to 95% at 10:35 AM"
Isolation: 10:30 AM

Temporal: 5 min gap → 1.0 ✓
Topological: Redis is in blast_radius.affected_services → 1.0 ✓
Directional: Redis is provider, app is consumer → 1.0 ✓

Result: CONFIRMED (3/3 dimensions matched)
Action: Rollback immediately
```

### Example 2: UNCERTAIN Unrelated

```
Isolated: VM A (iptables DROP)
Anomaly: "Payment service timeout at 02:30 PM"
Isolation: 10:30 AM

Temporal: 4 hours gap → 0.4
Topological: Payment service not in blast_radius → 0.0
Directional: No relationship → 0.0

Result: UNCERTAIN (only 1 weak dimension)
Action: Pause observation, request manual judgment
```

### Example 3: DISMISS Unrelated

```
Isolated: K8s StatefulSet (scale to 0)
Anomaly: "Network latency spike"
Isolation: 10:30 AM

Temporal: 18 hours gap → 0.0
Topological: No topological match → 0.0
Directional: No relationship → 0.0

Result: DISMISS (0/3 dimensions matched)
Action: Ignore, continue observation
```

## Output Format

Write attribution analysis to `{run_dir}/observe/attribution_{resource_id}.json`:

```json
{
  "resource_id": "...",
  "anomalies_analyzed": [
    {
      "anomaly_id": "...",
      "anomaly_type": "alert|complaint",
      "anomaly_signal": "error rate spike",
      "anomaly_timestamp": "2026-06-08T10:35:00Z",
      "anomaly_resource": "order_service",
      "temporal_score": 1.0,
      "temporal_gap_minutes": 5,
      "topological_score": 1.0,
      "topological_match": "direct_blast_radius",
      "directional_score": 1.0,
      "directional_relationship": "upstream_to_downstream",
      "attribution_result": "CONFIRMED",
      "confidence": "high",
      "average_score": 1.0
    }
  ],
  "overall_attribution": "CONFIRMED",
  "rollback_justified": true
}
```

## Decision Flow

```
For each anomaly:
  Compute temporal_score, topological_score, directional_score
  Count non_zero_scores

If non_zero_scores >= 2:
  → CONFIRMED: anomaly was caused by isolation
  → Execute rollback immediately (P0/P1)

Elif non_zero_scores == 1:
  → UNCERTAIN: insufficient evidence
  → Pause observation, notify user for manual judgment (P2)

Else:
  → DISMISS: unrelated incident
  → Continue observation, don't rollback
```

## Edge Cases

1. **Multiple anomalies** — Analyze each independently. If ANY is CONFIRMED, recommend rollback.
2. **Cascading anomalies** — Anomalies from the same root cause may appear at different times. Group by time window (e.g., within 1h) and analyze as single event.
3. **Intermittent anomalies** — If anomaly appears, disappears, reappears, score each occurrence separately. Pattern of recurrence strengthens temporal correlation.
4. **Silent services** — If a service has no monitoring data, can't perform attribution. Mark as uncertain and request manual review.
