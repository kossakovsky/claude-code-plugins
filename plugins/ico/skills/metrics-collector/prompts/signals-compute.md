# Compute (VM/EC2) Idle Detection Signals

**Applies to**: compute / EC2 / VM / Bare Metal
**Industry alignment**: GCP Idle VM Recommender (2600 B/s), AWS Trusted Advisor (<=10% CPU), Azure Advisor (P95 <3% CPU)

## Data Sources

Prefer cloud monitoring API (CloudWatch / Prometheus / Datadog) for historical data.
Only use `/proc` or in-VM collection as last resort (see SSH-only fallback below).

## Signals

| # | Signal | Threshold | Data Source |
|---|--------|-----------|-------------|
| 1 | CPU daily average | > 20% (14 days, 5-min intervals) -> ACTIVE | CloudWatch / Prometheus / Datadog |
| 2 | Network I/O | > 2 GB/day in+out (14-day average from cloud monitoring, or real-time rate sample from /proc/net/dev via SSH) -> ACTIVE | Cloud monitoring API / VPC Flow Logs / /proc/net/dev rate sample |
| 3 | Recent human login | Any human login within 30 days -> ACTIVE | Bastion audit logs / audit logs / `last` |

**Login detection**: Distinguish humans from automation by session duration (>60s), shell type (bash/zsh vs nologin), interactive TTY. Do NOT hardcode username exclude lists.

## SSH-Only Fallback

When no CloudWatch/Prometheus history is available, SSH into the host:

1. **CPU**: `top -bn1` or `/proc/stat` (note virt_type reliability below)
2. **Network**: Real-time traffic rate from `/proc/net/dev`:
   - Read all interfaces' RX/TX bytes → sleep 60s → read again
   - Rate = (bytes2 - bytes1) / 60s * 86400 → MB/day
   - Exclude lo (loopback). Sum remaining interfaces.
   - Compare against the Network I/O threshold in the signal table above.
3. **Login**: `last` (30 days)

## Placeholder Value Detection (CRITICAL)

When collecting from batch SSH output or raw command results, detect and reject:

| Signal | Placeholder Pattern | Action |
|--------|-------------------|--------|
| CPU | "N/A", empty string, missing field | reliability=0.0 |
| Network | "0.00 MB" + ALL other signals also placeholder ("N/A", "NONE", "0") | reliability=0.0 |
| Login | "NONE" (uppercase, no actual username) or missing | reliability=0.0 |
| Alerts | "0" (bare number) + ALL other signals also placeholder | reliability=0.0 |

**Cross-validation rule**: If 3+ other hosts in the same batch returned real data but this host returned all placeholders -> SSH channel established but command execution failed on target. ALL signals reliability=0.0.

**Safe guard**: If any single signal is a clear placeholder AND no other signal from the same host has real data -> ALL signals reliability=0.0. Do NOT partially accept "mixed" data from a failed collection.

## Virtualization Metric Reliability

| virt_type | CPU | Load | Memory | Disk I/O | Network |
|-----------|-----|------|--------|----------|---------|
| bare-metal | accurate | accurate | accurate | accurate | accurate |
| kvm | accurate (watch steal%) | meaningful but includes host noise | accurate | accurate (virtio) | accurate (virtio) |
| lxc | uses HOST value (wrong) | uses HOST value (wrong) | accurate (LXCFS) | missing/unreliable | uses HOST value (wrong) |
| unknown | treat as unreliable | treat as unreliable | treat as unreliable | treat as unreliable | treat as unreliable |

**Rule**: For all non-bare-metal, prefer cloud monitoring API over in-VM /proc collection.
For KVM: if `top` shows high `%steal`, CPU is unreliable.
For LXC: use cgroup cpu.stat for CPU, skip loadavg and disk I/O.
