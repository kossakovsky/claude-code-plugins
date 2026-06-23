# Database Idle Detection Signals

**Applies to**: RDS, Aurora, Cloud SQL, Redis, Memcached, and other managed databases
**Industry alignment**: GCP Cloud SQL Idle Recommender, AWS Trusted Advisor

## Data Sources

Prefer cloud monitoring API (CloudWatch / Cloud Monitoring). For Redis/Memcached, use `redis-cli INFO` or `memcached stats` when SSH is available.

## Signals

| # | Signal | Threshold | Data Source |
|---|--------|-----------|-------------|
| 1 | Active connections | 0 non-system connections in 7 days -> IDLE | CloudWatch DatabaseConnections / Cloud SQL Insights |
| 2 | CPU utilization | P95 < 1% over 14 days -> IDLE | CloudWatch CPUUtilization / Cloud Monitoring |
| 3 | Query rate (RDS/Aurora/Cloud SQL) | < 1 query/sec average over 14 days -> IDLE | CloudWatch DatabaseConnections + ReadIOPS + WriteIOPS |
| 4 | Command rate (Redis) | `instantaneous_ops_per_sec` = 0 for 14 days -> IDLE | `redis-cli INFO stats` / CloudWatch CacheHits+CacheMisses |
| 5 | Storage growth | < 1% growth in 30 days on non-system DBs -> IDLE | CloudWatch FreeStorageSpace / Cloud Monitoring |
| 6 | Replication lag (read replicas) | 0 read IOPS AND replication lag stable for 14 days -> no query traffic | CloudWatch ReplicaLag + ReadIOPS |

**Connections caveat**: Subtract system connections. For PostgreSQL exclude `rdsadmin`, for MySQL exclude `rdsadmin`/`event_scheduler`, for Redis `connected_clients=1` means only the server itself.

**Redis command rate**: Use `instantaneous_ops_per_sec` from `redis-cli INFO stats` if available; otherwise compute from `commands_processed` diff over 24h. Also check `keyspace_hits` vs `keyspace_misses` ratio — a cache with 100% misses may still be actively used.

## Edge Cases

- **Read replicas with 0 IOPS**: Likely idle — no application routes reads to them. Confirm by checking app connection strings.
- **Memcached with 0 evictions AND 0 get_hits**: Truly idle if both metrics are zero for 14 days; `curr_items=0` alone is insufficient (may have been flushed).
- **Aurora Serverless v2**: Check ACU consumption trend, not just CPU — may scale to 0 ACU when idle (auto-pause).
- **Cloud SQL with proxy**: Connection count via proxy may show > 0 even when idle — check query count, not connection count.
- **Dev/staging databases**: Flag separately from production even if metrics match idle thresholds; they may serve CI/CD jobs on irregular schedules.
- **Redis with persistence**: `commands_processed` grows from BGSAVE alone — exclude background save operations when computing command rate.
