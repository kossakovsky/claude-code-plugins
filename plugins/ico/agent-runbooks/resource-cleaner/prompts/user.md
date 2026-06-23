# zombie-resource-cleaner User Prompt Templates

## Execute Single Resource Deletion

```
Execute deletion operation:
- Resource ID: i-1234567890abcdef0
- Resource Type: CloudVM
- Environment: production
- Phase 5 Decision ID: phase5-{uuid}
- Decision maker: owner-user-id

Execute the complete Phase 6 Delete workflow:
1. Pre-flight re-evaluation (verify cooling period, resource state, dependencies)
2. Backup verification (verify backup-creator produced valid backups)
3. Deletion execution (in order: detach traffic -> stop -> delete sub-resources -> delete main resource -> cleanup)
4. Deletion verification (confirm resource deleted, no orphaned objects)
5. Metadata update (CMDB, monitoring system)
6. Audit & cost report (generate complete audit trail and cost savings analysis)

Output:
- delete/pre_flight_report.json
- delete/backup_verification_summary.json
- delete/deletion_record_i-1234567890abcdef0.json
- delete/cost_savings_i-1234567890abcdef0.json
- delete/audit_trail.json
```

## Execute Batch Resource Deletion

```
Execute batch deletion operation:
- Resources to delete: [i-001, i-002, ..., i-025]
- Resource Type: CloudVM
- Environment: production
- Batch size: 10
- Batch interval: 5 minutes
- Max concurrency: 3

Execute the complete Phase 6 Delete workflow, including:
1. Pre-flight re-evaluation (all resources)
2. Backup verification (verify backup-creator output for all resources)
3. Batch deletion execution (3 batches, 10 resources per batch, max 3 concurrent)
4. Deletion verification (all resources)
5. Metadata update (all resources)
6. Audit & cost report (generate batch summary)

Output:
- delete/batch_delete_plan.json
- delete/batch_delete_summary.json
- delete/deletion_report.json
- delete/cost_savings_report.json
- delete/audit_trail.json
```

## Dry Run Mode

```
Execute dry run (no actual deletion):
- Resource ID: i-1234567890abcdef0
- dry_run: true

Execute all validation and planning steps of the Phase 6 Delete workflow but do not perform actual deletion.
Output deletion plan and cost estimates for manual review.
```

## Elastic IP Special Handling

```
Execute elastic IP deletion (requires DNS check):
- Resource ID: elastic-ip-1234567890abcdef0
- Elastic IP Address: 203.0.113.42
- enable_eip_dns_check: true

Before deletion:
1. Check DNS system for A records pointing to this elastic IP
2. Check security/firewall system for IP whitelist references
3. Create 24h pre-deletion notification for DNS and security teams
4. Wait 24h before executing deletion

Output:
- delete/elastic_ip_dns_check_report.json
- delete/elastic_ip_notification_log.json
- delete/deletion_record_elastic-ip-1234567890abcdef0.json
```

## Recovery Window Query

```
Query recovery window information:
- Resource ID: i-1234567890abcdef0
- Environment: production

Output:
- Backup retention period: 30 days
- Recovery window end time: {deletion_date + 30 days}
- Recovery SLA: 2h response, 4h completion
- Recovery method: Create new instance from image, configure same VPC/subnet/security group
- Last-chance notification time: {window_end - 3 days}
```

## Cost Savings Report

```
Generate cost savings report:
- Resource ID: i-1234567890abcdef0
- Created: 2025-01-15
- Deleted: 2026-06-05
- Monthly cost: $250.5

Calculate:
1. Immediate savings (monthly/annual)
2. Lifecycle cost (total cost from creation to deletion)
3. Zombie period waste cost (cost from isolation to deletion)
4. Backup storage cost
5. Net savings (immediate savings - backup cost)

Output: delete/cost_savings_i-1234567890abcdef0.json
```

## Audit Log Query

```
Query deletion audit log:
- Resource ID: i-1234567890abcdef0
- Time range: 2026-06-05 to 2026-06-06

Output complete timeline:
- Pre-flight re-evaluation results
- Backup verification results
- Each step of deletion execution
- Deletion verification results
- Metadata update status
- Cost calculation results

Output: delete/audit_trail.json
```
