# Dimension Scoring Template Reference

This document defines scripted threshold rules for 9 resource types across multiple scoring dimensions. All thresholds are deterministic; LLMs must not directly output scores.

## 1. Compute Resources (CloudVM / EC2)

### 1.1 cpu_memory (weight 0.30)

**Data source**: Monitoring API (CloudWatch) - 30-day average

| Condition | Score | Reliability |
|-----------|-------|-------------|
| CPU avg < 5% AND memory avg < 10% | 0.95 | 1.0 |
| 5% <= CPU < 20% OR 10% <= memory < 30% | 0.50 | 1.0 |
| CPU >= 20% OR memory >= 30% | 0.0 | 1.0 |
| Data unavailable | 0.0 | 0.0 |

```python
if cpu_mean is None or memory_mean is None:
    return {"score": 0.0, "reliability": 0.0}
elif cpu_mean < 5 and memory_mean < 10:
    return {"score": 0.95, "reliability": 1.0}
elif cpu_mean < 20 and memory_mean < 30:
    return {"score": 0.5, "reliability": 1.0}
else:
    return {"score": 0.0, "reliability": 1.0}
```

### 1.2 network_throughput (weight 0.25)

**Data source**: Monitoring API - 30-day average (in+out total)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Avg ~ 0 (< 1 KB/s) | 0.95 | 1.0 |
| Daily average > 100 KB | 0.0 | 1.0 |
| Data unavailable | 0.0 | 0.0 |

### 1.3 access_activity (weight 0.20)

**Data source**: SSH access logs (Phase 2) - Phase 1 marked unavailable

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day zero business requests | 1.0 | 1.0 |
| Health checks / monitoring only | 0.80 | 0.70 |
| Business requests within 7 days | 0.0 | 1.0 |
| Data unavailable (Phase 1) | 0.0 | 0.0 |

**Health check exclusion patterns**:
- URI contains: `/health`, `/ping`, `/status`, `/readyz`, `/livez`, `/metrics`
- User-Agent contains: `ELB-HealthChecker`, `kube-probe`, `Prometheus`, `node_exporter`

### 1.4 login_history (weight 0.15)

**Data source**: SSH `last` command (Phase 2) - Phase 1 marked unavailable

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 90 days no login | 1.0 | 1.0 |
| 30 days no login | 0.70 | 1.0 |
| Login within 7 days | 0.0 | 1.0 |
| Data unavailable (Phase 1) | 0.0 | 0.0 |

### 1.5 cron_tasks (weight 0.10)

**Data source**: SSH crontab + systemd timers (Phase 2) - Phase 1 marked unavailable

| Condition | Score | Reliability |
|-----------|-------|-------------|
| No crontab AND no systemd timers | 1.0 | 1.0 |
| Tasks with interval >= weekly | 0.0 | 1.0 |
| Data unavailable (Phase 1) | 0.0 | 0.0 |

---

## 2. Storage Resources (EBS / Cloud Disk / Snapshot)

### 2.1 mount_status (weight 0.40)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Unmounted | 0.95 | 1.0 |
| Mounted | 0.0 | 1.0 |
| Unknown status | 0.0 | 0.3 |

### 2.2 io_metrics (weight 0.30)

**Data source**: Disk API - 30-day I/O read/write statistics

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day I/O = 0 | 1.0 | 1.0 |
| 30-day I/O > 0 | 0.0 | 1.0 |
| Data unavailable | 0.0 | 0.0 |

### 2.3 source_instance (weight 0.20) -- Snapshots only

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Source instance deleted | 1.0 | 1.0 |
| Source instance exists | 0.0 | 1.0 |

### 2.4 snapshot_age (weight 0.10)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Snapshot > 180 days + no associations | 0.90 | 0.70 |
| Snapshot < 180 days OR active associations | 0.0 | 1.0 |

---

## 3. Network Resources (NAT / ALB/NLB / EIP)

### 3.1 traffic (weight 0.50)

**Data source**: Monitoring API - 30-day traffic statistics

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Average ~ 0 | 1.0 | 1.0 |
| Daily average > 1 KB | 0.0 | 1.0 |
| Data unavailable | 0.0 | 0.0 |

### 3.2 backend_health (weight 0.35)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| No healthy backends | 1.0 | 1.0 |
| Has healthy backends | 0.0 | 1.0 |

### 3.3 cost_utilization (weight 0.15)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Monthly cost > $100 AND traffic = 0 | 0.95 | 1.0 |
| Cost matches traffic | 0.0 | 1.0 |

**EIP special rules**:
- Unbound to any instance: score = 1.0
- Bound to stopped instance: score = 0.80
- Unbound > 90 days: score = 1.0; > 30 days: score = 0.70

---

## 4. Database Resources (RDS / Aurora / Cloud SQL)

### 4.1 connections (weight 0.35)

**Data source**: RDS monitoring API - 30-day connections (excluding monitoring)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day connections = 0 | 0.95 | 1.0 |
| Connections <= 3 (monitoring only) | 0.70 | 0.70 |
| Connections > 3 | 0.0 | 1.0 |

**Excluded monitoring users**: `monitor`, `healthcheck`, `rdsadmin`, `replication`

### 4.2 qps (weight 0.30)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day QPS = 0 | 1.0 | 1.0 |
| Only `SELECT 1` / health check queries | 0.60 | 0.70 |
| QPS > 0 (business queries) | 0.0 | 1.0 |

### 4.3 storage_growth (weight 0.20)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day growth = 0 | 0.80 | 1.0 |
| 30-day growth > 0 | 0.0 | 1.0 |

### 4.4 backup_access (weight 0.15)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| No restore operations + no active read replicas | 0.90 | 0.70 |
| Has restore operations or active read replicas | 0.0 | 1.0 |

---

## 5. Cache Resources (Redis / Memcached / ElastiCache)

### 5.1 connections (weight 0.35)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day connections = 0 | 1.0 | 1.0 |
| Only sentinel/monitor connections | 0.60 | 0.70 |
| Connections > 0 (business) | 0.0 | 1.0 |

### 5.2 ops_per_sec (weight 0.35)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day ops/s = 0 | 1.0 | 1.0 |
| Only PING/INFO/CONFIG commands | 0.70 | 0.70 |
| ops/s > 0 (business commands) | 0.0 | 1.0 |

### 5.3 memory_usage (weight 0.15)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Used memory = 0 + no growth | 0.90 | 1.0 |
| Used memory > 0 | 0.0 | 1.0 |

### 5.4 key_count (weight 0.15)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Key count = 0 | 1.0 | 1.0 |
| 30-day key count unchanged | 0.60 | 0.70 |
| Key count increasing | 0.0 | 1.0 |

---

## 6. K8s Workload (Deployment / StatefulSet / DaemonSet)

### 6.1 replica_status (weight 0.30)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Replicas = 0 for > 30 days | 1.0 | 1.0 |
| All pods CrashLoopBackOff > 7 days | 0.80 | 1.0 |
| Has healthy running replicas | 0.0 | 1.0 |

### 6.2 traffic_in (weight 0.30)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day traffic = 0 | 0.95 | 1.0 |
| Only probe traffic | 0.70 | 0.70 |
| Business traffic present | 0.0 | 1.0 |
| No service mesh | 0.0 | 0.30 |

### 6.3 last_deploy (weight 0.20)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Last image update > 365 days | 0.90 | 1.0 |
| Last image update > 180 days | 0.70 | 1.0 |
| Recently deployed | 0.0 | 1.0 |

### 6.4 hpa_activity (weight 0.10)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day no scaling events | 0.70 | 0.70 |
| Has scaling events | 0.0 | 1.0 |
| No HPA | 0.0 | 0.0 |

### 6.5 owner_reference (weight 0.10)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| No team label | 0.70 | 0.70 |
| Team disbanded | 0.90 | 0.70 |
| Team still active | 0.0 | 1.0 |

---

## 7. K8s Service

### 7.1 endpoints (weight 0.40)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Endpoints empty (no ready backend) | 1.0 | 1.0 |
| Has ready backends | 0.0 | 1.0 |

### 7.2 traffic (weight 0.35)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day zero traffic | 1.0 | 1.0 |
| Has traffic | 0.0 | 1.0 |
| No mesh data | 0.0 | 0.30 |

### 7.3 selector_match (weight 0.25)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Selector matches 0 pods | 1.0 | 1.0 |
| Selector only matches zombie candidate pods | 0.80 | 0.70 |
| Selector matches active pods | 0.0 | 1.0 |

---

## 8. K8s Orphan Resources (ConfigMap / Secret / PVC)

### 8.1 mount_reference (weight 0.50)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| No Pod/Deployment references | 0.95 | 1.0 |
| Has references | 0.0 | 1.0 |

### 8.2 env_reference (weight 0.30)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Not referenced by any container env/envFrom | 0.90 | 1.0 |
| Has environment variable references | 0.0 | 1.0 |

### 8.3 age_no_update (weight 0.20)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| > 180 days no modification + no references | 0.90 | 0.70 |
| Recently modified or has references | 0.0 | 1.0 |

**PVC special rules**:
- Status Released/Available (not Bound): score = 0.95
- Bound but mount pod is zombie candidate: score = 0.70 (zombie chain)

---

## 9. Domain Resources

### 9.1 registration_status (weight 0.45)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| Expired | 1.0 | 1.0 |
| Active within validity period | 0.0 | 1.0 |

### 9.2 dns_records (weight 0.35)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| No A/CNAME records | 1.0 | 1.0 |
| Has DNS records | 0.0 | 1.0 |

### 9.3 http_traffic (weight 0.20)

| Condition | Score | Reliability |
|-----------|-------|-------------|
| 30-day HTTP requests = 0 | 0.95 | 1.0 |
| Has HTTP traffic | 0.0 | 1.0 |

**Protection rules**:
- Newly registered domains (< 7 days): force skip (Layer A exclusion)
- Expiring soon (< 30 days) but has HTTP traffic: suspect_level cap at medium

---

## Reliability Coefficient Rules

| Scenario | Coefficient | Notes |
|----------|------------|-------|
| Full data, direct API query | 1.0 | Normal scoring participation |
| Partial data (< 50% time points) | 0.70 | Reduced weight contribution |
| Insufficient permissions | 0.30 | Greatly reduced weight |
| Query timeout or complete failure | 0.0 | Skip this dimension |

---

## Data Integrity Thresholds

- **Valid dimensions < 2**: Force suspect_level = low, zombie_score = 0.0
- **cpu_memory unavailable** (compute only): zombie_score cap = 0.60
- **Single time-point snapshot**: Dimension reliability reduced to 0.30
