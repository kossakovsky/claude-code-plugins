# Storage Idle Detection Signals

**Applies to**: EBS volumes, GCP persistent disks, Azure managed disks, local SSDs
**Industry alignment**: GCP Idle Disk Recommender, AWS CloudWatch EBS metrics, Azure Advisor VM Idle Disk

## Data Sources

Cloud monitoring API (CloudWatch / Azure Monitor / GCP Recommender API). SSH-in-VM `iostat` or `lsblk` only for attached volumes without monitoring history; fully detached volumes require cloud inventory API.

## Signals

| # | Signal | Threshold | Data Source |
|---|--------|-----------|-------------|
| 1 | Attachment status | Detached from all instances for 7+ days -> ZOMBIE | Cloud inventory API / `lsblk` |
| 2 | VolumeReadOps + VolumeWriteOps | < 1 IOPS (14-day P95) -> IDLE | CloudWatch / Azure Monitor / GCP disk metrics |
| 3 | VolumeReadBytes + VolumeWriteBytes | < 1 KB/s (14-day average) -> IDLE | Cloud monitoring API |
| 4 | VolumeIdleTime (AWS) | > 95% idle over 14 days -> IDLE | disk idle time (e.g. CloudWatch `VolumeIdleTime`) |
| 5 | BurstBalance (AWS gp2) | Always 100% with near-zero IOPS -> IDLE | burst balance (e.g. AWS gp2 BurstBalance) |
| 6 | QueueLength | Always 0 with no throughput -> confirms IDLE | disk queue length (e.g. CloudWatch `VolumeQueueLength`) |
| 7 | Lifecycle of attached instance | Instance state != running for 7+ days -> ZOMBIE | Cloud inventory API |

**GCP-specific**: Use `google.compute.disk.IdleResourceRecommender` which aggregates the above signals internally. Recommended action confidence >= "MEDIUM" is actionable.

**Combination rule**: Signal #1 alone (detached) is sufficient for ZOMBIE classification. For attached volumes, at least 3 of signals #2-#6 must agree for IDLE; a single signal with real I/O overrides IDLE.

## Edge Cases

| Scenario | Treatment |
|----------|-----------|
| Boot/root volumes | Only classify as IDLE if the instance itself is IDLE or ZOMBIE |
| Swap volumes | Ignore I/O signals — swap can be hot even on idle instances. Use attachment + instance lifecycle only |
| Volumes with active snapshots | NOT idle — snapshot creation generates read I/O on source |
| Volumes from snapshot chains | Check ancestor snapshots: if chain is part of a DR or backup pipeline, mark as active |
| Recently created volumes (< 14 days) | Insufficient data window — mark as UNKNOWN rather than IDLE |
| multi-attach volumes (e.g. EBS io1/io2) | Check I/O from ALL attached instances before classifying |

## Detached vs Idle vs Zombie

**Detached**: Not connected to any instance. Zombie after 7+ days detached.
**Idle**: Attached but shows no I/O activity (covered by signals #2-#6).
**Zombie**: Detached and stale OR attached to a stopped/terminated instance for 7+ days.
