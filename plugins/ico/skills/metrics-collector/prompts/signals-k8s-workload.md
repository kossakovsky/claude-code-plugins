# Kubernetes Workload Idle Detection Signals

**Applies to**: Deployment, StatefulSet, DaemonSet, CronJob, standalone Pods (k8s_workload resource type)
**Industry alignment**: GCP excludes GKE nodes from Idle VM Recommender (separate detection); workload-level metrics from Kubernetes Metrics API / Prometheus

## Data Sources

Kubernetes Metrics API (metrics.k8s.io) or Prometheus for historical CPU/memory. Kubernetes API for replicas, rollout history, service selectors. Pod logs via `kubectl logs` or Loki.

## Signals

| # | Signal | Threshold (Idle) | Data Source |
|---|--------|------------------|-------------|
| 1 | Replicas mismatch | current_replicas=0, or desired_replicas>0 but ready=0 | Kubernetes API (Deployment/StatefulSet status) |
| 2 | CPU usage vs request | actual CPU < 5% of requested CPU for 14 consecutive days | Metrics API / Prometheus |
| 3 | Memory usage vs request | actual memory < 10% of requested memory for 14 consecutive days | Metrics API / Prometheus |
| 4 | Network activity | No incoming traffic to any pod (no Service selecting this workload) | Kubernetes API (Service/Endpoints) + CNI metrics |
| 5 | Pod log activity | No line logged indicating real work (exclude health probes, leader election) in 30 days | kubectl logs / Loki |
| 6 | Rollout freshness | No new ReplicaSet created (no rollout) in N days. N depends on environment: dev=7, staging=30, prod=90, unknown=90 | Kubernetes API (ReplicaSet creation timestamps) |

**CPU/Memory calculation**: aggregate across all pods in the workload, compare P95 against total requested resources. Memory excludes page cache on Linux nodes.

**Log activity exclusions**: kube-probe entries, readiness/liveness check logs, leader election logs, controller-runtime reconcile messages. Only count lines indicating actual business logic execution.

## Edge Cases

| Case | Handling |
|------|----------|
| DaemonSet | Skip entirely -- infrastructure by design, always runs on every node |
| CronJob with zero recent executions | Check lastScheduleTime; if schedule present but no job created in 30 days -> ZOMBIE |
| CronJob with failures | Check last 10 runs; success_rate < 50% -> DEGRADED (not idle) |
| HPA with min_replicas=0 | Expected behavior, annotate as SCALE-TO-ZERO pattern, not idle |
| HPA with min_replicas=1 and 0% CPU | Highly suspicious -- HPA floor pod consuming resources with no work -> ZOMBIE candidate |
| System namespaces | Skip `kube-system`, `monitoring`, `istio-system`, `cert-manager` entirely |
| Job (batch) | Judge by completion status; Completed=Succeeded -> normal; Never scheduled for 30 days -> ZOMBIE |
| Single-replica StatefulSet | Same rules as Deployment; additionally check PVC usage (empty PV with no I/O is extra signal) |
