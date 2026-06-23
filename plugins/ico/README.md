# ICO — Infra Cost Optimizer

Find idle and underutilized cloud resources, safely isolate and observe them, and decommission the real zombies — reducing cloud spend without breaking production.

## Capabilities

- **Multi-cloud idle detection** — Scan compute instances, Kubernetes workloads, databases, object storage, and network resources across AWS, GCP, Azure, or on-prem via SSH
- **Multi-dimensional scoring** — CPU, network, and login signals for coarse filtering; 4-dimension zombie scoring for prioritization
- **Deep technical profiling** — Concurrent SSH into candidates to capture processes, ports, crontab, disk usage, and real-time traffic topology
- **Safe isolation with auto-rollback** — Type-specific isolation methods (iptables, security groups, scale-to-zero) with observation periods and anomaly detection
- **Human decision gates** — 4 blocking checkpoints before any destructive action
- **Pre-deletion backups** — Per-resource-type backups with encryption

## Usage

```
/ico:orchestrator Scan my cloud for idle resources
```

## License

Apache 2.0
