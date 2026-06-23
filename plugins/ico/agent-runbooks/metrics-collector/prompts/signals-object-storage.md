# Object Storage Idle Detection Signals

**Applies to**: S3 buckets, GCS buckets, Azure Blob containers, MinIO buckets (object_storage resource type)
**Industry alignment**: AWS S3 Storage Lens, CloudWatch BucketSizeBytes/NumberOfObjects/request metrics; GCS usage statistics; MinIO `mc admin info`. No major cloud provider offers an official "idle bucket" recommender.

## Data Sources

Cloud monitoring API (S3 CloudWatch request metrics + daily storage metrics, GCS usage logs, Azure Storage metrics, MinIO `mc admin prometheus`). S3 Storage Lens when available for access-pattern analytics, but default CloudWatch metrics are sufficient for basic idle detection.

## Signals

| # | Signal | Threshold | Data Source |
|---|--------|-----------|-------------|
| 1 | Last PUT/POST/CopyObject timestamp | No object creation or modification in 90+ days -> ZOMBIE | CloudWatch request metrics / GCS access logs |
| 2 | GET/HEAD request count | < 1 GET/HEAD per day (30-day average) -> IDLE | CloudWatch `GetRequests` / GCS `ReadRequests` |
| 3 | BucketSizeBytes | 0 bytes or < 1 KB (30-day average) -> ZOMBIE | CloudWatch `BucketSizeBytes` (daily metric) |
| 4 | NumberOfObjects | 0 objects -> ZOMBIE; no change in 90 days -> IDLE | CloudWatch `NumberOfObjects` (daily metric) |
| 5 | Lifecycle policy presence | Has a lifecycle rule that deletes or transitions ALL objects -> may signal active management, override IDLE | Bucket configuration / `GetBucketLifecycle` |
| 6 | Access logging enabled | Logs show zero access events over 90 days -> confirms IDLE | audit log data events / GCS access logs |

**Combination rule**: Signal #3 (zero size) alone is sufficient for ZOMBIE if the bucket existed > 30 days (exclude newly created). For populated buckets, signals #1 + #2 must both fire; signal #5 can override IDLE if lifecycle actively deletes or transitions objects. Signal #6 is a confirming signal, not standalone.

## Edge Cases

| Scenario | Treatment |
|----------|-----------|
| Logging/audit buckets | Data arrives externally (external push (load balancer logs, audit logs)). Zero GETs is normal — classify by PUT activity only. IDLE only if 0 PUTs AND 0 objects in 90 days |
| Static website hosting | Check CDN access logs, not bucket-level GETs. If S3 website endpoint is enabled but no CDN log activity exists, consider IDLE |
| Replication source buckets | Active replications generate `ReplicateObject` operations — check replication metrics, not just direct GET/PUT from users |
| Replication destination buckets | Inbound replication writes are invisible to source metrics. Check `ReplicateObject` events on the destination side rather than user-originated writes |
| Cross-region replication | Same as replication above, but check both source and destination region metrics separately |
| Glacier/Deep Archive buckets | Objects intentionally cold — low GET count is NOT an idle signal. Must check restore requests and inventory retrievals for activity |
| Versioned buckets with delete markers | Many delete markers + no real objects is a cleanup in progress, not idle. Check whether delete markers are recent (< 90 days) |
| Recently created buckets (< 30 days) | Insufficient data window — mark as UNKNOWN rather than ZOMBIE |
| MinIO internal buckets | `.minio.sys` and similar system buckets are never idle — skip detection entirely |
| Buckets used by serverless triggers | object event notifications to serverless functions/queues mean activity happens off-bucket. Check trigger invocation logs, not just bucket metrics |
