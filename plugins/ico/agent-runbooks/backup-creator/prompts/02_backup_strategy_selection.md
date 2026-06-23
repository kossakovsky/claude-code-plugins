# Backup Strategy Selection Prompt

You are executing Phase 2 of the zombie-backup-creator runbook: Backup Strategy Dispatch.

## Objective
Select the appropriate backup method for each resource based on entity_type, environment, and cloud provider.
This determines what backup action will be taken in Phase 3.

## Backup Strategy Matrix

Reference: `phase-6-delete.md section 4.2-4.10`

| Entity Type | Backup Method | Prod Retention | Staging Retention | Dev Retention | Cost Est |
|---|---|---|---|---|---|
| CloudVM | Full AMI + data disk snapshots | 30 days | 14 days | 7 days | ~$0.05/day |
| CloudDisk | Snapshot | 30 days | 14 days | 7 days | ~$0.01/day |
| RDS | Final Snapshot | 30 days | 14 days | 7 days | ~$0.10/GB/day |
| Redis | BGSAVE + RDB export to S3/OSS | 30 days | 14 days | 7 days | ~$0.003/GB/day |
| Memcache | Config snapshot + key list export | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sDeployment | YAML manifest + ConfigMaps/Secrets/Service | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sStatefulSet | YAML + PVC metadata + ConfigMaps/Secrets | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sDaemonSet | YAML manifest + ConfigMaps/Secrets | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sCronJob | YAML with suspend state preserved | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sConfigMap | YAML export | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sSecret | YAML export (encrypted storage) | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sService | YAML export | 30 days | 14 days | 7 days | ~$0.001/day |
| K8sPVC | Volume snapshot + PVC metadata | 30 days | 14 days | 7 days | ~$0.001/day |
| LoadBalancer | Configuration snapshot (JSON) | 30 days | 14 days | 7 days | ~$0.001/day |
| ElasticIP | IP + binding history snapshot | 30 days | 14 days | 7 days | ~$0.0/day |

## Strategy Selection Logic

For each resource:

```python
def select_strategy(entity_type, environment, backup_retention_override=None):
    # 1. Get base retention for environment
    retention_days = {
        "production": 30,
        "staging": 14,
        "dev": 7
    }[environment]

    # 2. Apply override if provided
    if backup_retention_override:
        retention_days = backup_retention_override

    # 3. Look up backup method from matrix
    strategy = BACKUP_STRATEGY_MATRIX[entity_type]

    # 4. Calculate backup window
    backup_window_end = now() + timedelta(days=retention_days)

    # 5. Calculate cost estimate
    cost_daily = strategy["cost_estimate_daily"]
    cost_total = cost_daily * retention_days

    # 6. Generate recovery hints based on entity_type
    recovery_hints = generate_recovery_hints(entity_type)

    return {
        "entity_type": entity_type,
        "backup_method": strategy["method"],
        "retention_days": retention_days,
        "backup_window_end": backup_window_end,
        "cost_estimate_daily": cost_daily,
        "cost_estimate_total": cost_total,
        "recovery_hints": recovery_hints
    }
```

## Recovery Hints Generation

For each backup method, pre-generate recovery hints that will be included in the report:

**CloudVM (AMI restore)**:
```
Method: restore_from_image
Instructions: Use ec2.run_instances(ImageId=ami-xxx) with same VPC/subnet/SG
Estimated time: 15 minutes
Prerequisites:
  - Target VPC accessible
  - IAM role has EC2 permissions
  - Security group allows required access
```

**RDS (Final Snapshot restore)**:
```
Method: restore_from_final_snapshot
Instructions: Use aws rds restore-db-instance-from-db-snapshot --db-instance-identifier new-xxx --db-snapshot-identifier snap-xxx
Estimated time: 30 minutes
Prerequisites:
  - Database parameter group available
  - Security group configured
  - Subnet group available
```

**Redis (RDB restore)**:
```
Method: restore_from_rdb
Instructions: Create new Redis instance, load RDB file via redis-cli or AWS ElastiCache restore
Estimated time: 20 minutes
Prerequisites:
  - RDB file accessible from S3/OSS
  - New Redis instance created
  - Configuration parameters applied
```

**K8s Workload (YAML apply)**:
```
Method: kubectl_apply
Instructions: kubectl apply -f backup-{namespace}-{kind}-{name}.yaml
Estimated time: 5 minutes
Prerequisites:
  - Cluster accessible
  - kubectl context correct
  - YAML file in version control or S3
```

## Output Format

Produce JSON array of strategies (one per resource):

```json
[
  {
    "resource_id": "i-prod-001",
    "entity_type": "CloudVM",
    "backup_strategy": {
      "entity_type": "CloudVM",
      "backup_method": "image_and_snapshots",
      "retention_days": 30,
      "backup_window_end": "2026-07-05T10:00:00Z",
      "cost_estimate_daily": 0.05,
      "cost_estimate_total": 1.50,
      "recovery_hints": {
        "method": "restore_from_image",
        "instructions": "Use ec2.run_instances(ImageId=ami-xxx) with same VPC/subnet/SG",
        "estimated_time_minutes": 15,
        "pre_requisites": ["Target VPC accessible", "IAM role has EC2 permissions"]
      }
    }
  },
  {
    "resource_id": "db-prod-001",
    "entity_type": "RDS",
    "backup_strategy": {
      "entity_type": "RDS",
      "backup_method": "final_snapshot",
      "retention_days": 30,
      "backup_window_end": "2026-07-05T10:00:00Z",
      "cost_estimate_daily": 0.10,
      "cost_estimate_total": 3.00,
      "recovery_hints": {
        "method": "restore_from_final_snapshot",
        "instructions": "aws rds restore-db-instance-from-db-snapshot --db-instance-identifier new-xxx --db-snapshot-identifier snap-xxx",
        "estimated_time_minutes": 30,
        "pre_requisites": ["Database parameter group available", "Security group configured"]
      }
    }
  }
]
```

## Output File Location
Write to: `{run_dir}/delete/backup_strategies.json`

## Validation
- All resources should have a matching strategy
- If entity_type is unknown, mark as "unsupported_resource_type" and escalate
- All retention_days must be between 1 and 90
