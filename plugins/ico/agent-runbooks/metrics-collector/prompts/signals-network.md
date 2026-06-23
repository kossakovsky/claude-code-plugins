# Network Resource Idle Detection Signals

**Applies to**: EIPs, Load Balancers (ALB/NLB/CLB), NAT Gateways, VPN Gateways
**Industry alignment**: AWS idle EIP detection + Trusted Advisor LB recommendations, GCP Idle Address Recommender (compute.address.IdleResourceRecommender), Azure idle public IP advisor

## Data Sources

Cloud monitoring API (CloudWatch / VPC Flow Logs / Azure Monitor / GCP Recommender API). Each resource sub-type queries its own namespace and metrics.

## Signals

| # | Resource | Signal | Zombie Threshold | Data Source |
|---|----------|--------|------------------|-------------|
| 1 | Elastic IP | AssociationStatus | Not associated with any ENI or instance | AWS EC2 DescribeAddresses / cloud provider API |
| 2 | Elastic IP | InheritCompute | Associated instance is zombie -> inherit INACTIVE | Cross-reference compute signal (signals-compute.md) |
| 3 | ALB/CLB | RequestCount | Zero over 14 days | CloudWatch AWS/ApplicationELB or AWS/ELB, Sum over 14d |
| 4 | ALB/CLB | HealthyHostCount | Zero healthy targets for 7+ days | CloudWatch, Average over 7d |
| 5 | NLB | ActiveFlowCount | Zero over 14 days | CloudWatch AWS/NetworkELB, Sum over 14d |
| 6 | NLB | HealthyHostCount | Zero healthy targets for 7+ days | CloudWatch, Average over 7d |
| 7 | NAT Gateway | ActiveConnectionCount | < 10 average over 14 days | CloudWatch AWS/NATGateway, Average over 14d |
| 8 | NAT Gateway | BytesOutToInternet | < 1 MB/day over 14 days | CloudWatch, Sum BytesOutToInternet / 14 |
| 9 | VPN | TunnelState | DOWN for > 7 continuous days | CloudWatch AWS/VPN, TunnelState metric |
| 10 | VPC Peering | ActiveFlowLogs | Zero accepted traffic entries in 14 days | VPC Flow Logs on both sides, Sum packetsAccepted |

## Inherited Zombie

When a resource references another resource, inherit idle/deleted status:

| Parent | Child | Rule |
|--------|-------|------|
| Compute instance | Associated ElasticIP | Compute idle -> ElasticIP idle (unless ElasticIP has other associations) |
| Target group | LoadBalancer | All targets unhealthy -> LB idle |

## Edge Cases

- **Partially healthy LB**: If some target groups have healthy hosts but others don't, the LB is NOT idle — it still serves live traffic on the healthy groups.
- **NAT Gateway with only DNS traffic**: ActiveConnectionCount may be non-zero but BytesOutToInternet is trivial — classify as idle if total bytes < 1 MB/day.
- **VPN tunnel flapping**: If TunnelState alternates UP/DOWN within 7 days, do NOT classify as idle — intermittent connectivity is not zombie, it is flaky.
- **ElasticIP on stopped instance**: Instance may be temporarily stopped for maintenance. Check stop duration — idle only if instance stopped > 30 days.
