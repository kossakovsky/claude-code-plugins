# Pre-Backup Validation Prompt

You are executing Phase 1 of the zombie-backup-creator runbook: Pre-Backup Validation.

## Objective
Validate that each resource is ready for backup before attempting creation. This is the safety checkpoint that ensures:
- Resource still exists (not deleted externally)
- Phase 3 isolation is still in effect
- Cloud APIs are accessible
- Storage quota is available

## Input
- Resource list with metadata
- Cloud provider credentials (via SSH key path)
- Phase 3 isolation records

## Validation Checks

### 1. Resource Existence Check
For each resource, verify it still exists in the cloud platform:

**CloudVM (VM)**:
```
Call: describe_instances(InstanceIds=[resource_id])
Check: InstanceState != terminated, deleting, stopping
Action on fail: Skip this resource, mark as "resource_not_found"
```

**RDS**:
```
Call: describe_db_instances(DBInstanceIdentifier=resource_id)
Check: DBInstanceStatus in [available, backing-up, modifying]
Action on fail: Skip this resource, mark as "resource_not_found"
```

**Redis/Memcache**:
```
Call: describe_cache_clusters(CacheClusterId=resource_id)
Check: CacheClusterStatus != deleting
Action on fail: Skip this resource
```

**K8s Resources**:
```
Call: kubectl get {kind} -n {namespace} {name}
Check: Resource exists
Action on fail: Skip this resource
```

### 2. Isolation State Verification
Confirm Phase 3 isolation is still in effect:

**CloudVM**:
```
Expected: InstanceState == stopped
If running: Mark as "isolation_broken", escalate to re-run Phase 3
```

**RDS**:
```
Expected: DBInstanceStatus == available (but security group denies all inbound)
Verify: Security group has no inbound rules (or all deny)
If open: Mark as "isolation_broken"
```

**Redis**:
```
Expected: Whitelist is empty (no IP addresses allowed)
Verify: AuthorizationList is empty
If not empty: Mark as "isolation_broken"
```

**K8s Workload**:
```
Expected: replicas == 0 (Deployment/StatefulSet/DaemonSet)
Verify: kubectl get {kind} -n {namespace} {name} -o json | jq .spec.replicas
If > 0: Mark as "isolation_broken"
```

### 3. Cloud API Accessibility
Test that cloud credentials are valid:

```
Call: describe_regions() or equivalent basic API
Check: Response successful, no auth errors
Action on fail: Mark as "cloud_api_inaccessible", escalate
```

### 4. Storage Quota Check
Warn if backup storage space is critically low:

```
For S3/OSS: Check available space
If < 10% available: Add warning but continue
If < 1% available: Add critical warning
```

## Output Format

For each resource, produce:
```json
{
  "resource_id": "i-xxx",
  "pre_backup_validation": {
    "timestamp": "2026-06-05T10:00:00Z",
    "status": "passed|warning|failed",
    "checks": [
      {"name": "resource_exists", "passed": true},
      {"name": "isolation_preserved", "passed": true},
      {"name": "api_accessible", "passed": true},
      {"name": "storage_quota", "passed": true}
    ],
    "warnings": [],
    "error": null
  }
}
```

## Escalation Triggers
- Resource not found -> Skip (already deleted?)
- Isolation broken -> Escalate (Phase 3 needs re-execution)
- API inaccessible -> Escalate (credential issue)
- Storage quota critical -> Warning (may fail during backup)

## Success Criteria
All resources pass validation with status="passed" or "warning".
Any "failed" status blocks that resource from proceeding to backup creation.
