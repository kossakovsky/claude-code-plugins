# Kubernetes Service Idle Detection Signals

**Applies to**: Service, Ingress, ServiceEntry (Istio), k8s_orphan (ConfigMap, Secret, PVC, ServiceAccount)
**Industry alignment**: Karpenter consolidation, VPA Recommender, kubecost orphan detection

## Data Sources

Kubernetes API (endpoints, ingress, pods, deployments, statefulsets, jobs) via kubectl or client-go. Prometheus for request volume history (Ingress controller metrics).

## Signals

| # | Resource | Signal | Zombie Threshold | Data Source |
|---|----------|--------|-----------------|-------------|
| 1 | Service | Active endpoints | 0 endpoints (= no pods match selector) | `/api/v1/namespaces/{ns}/endpoints/{name}` |
| 2 | Service | Associated Ingress | Internal-only Service with 0 endpoints AND 0 referencing Ingresses | K8s API: list Ingress, check spec.rules[].http.paths[].backend.service.name |
| 3 | Ingress | Backend health | All backends return 5xx or 0 backends configured | Ingress controller metrics (nginx-ingress / istio-ingressgateway) |
| 4 | Ingress | Request volume | 0 requests over 14 days | Prometheus: `sum(rate(nginx_ingress_controller_requests{ingress="$name"}[14d]))` |
| 5 | k8s_orphan | Pod references | 0 pods/deployments/statefulsets/jobs reference the resource AND age > 30d | K8s API: full namespace scan of volume mounts, envFrom, secretRef, configMapRef, serviceAccountName |
| 6 | ServiceEntry | Endpoint resolution | 0 resolved endpoints for > 7 days | Istio Pilot metrics or `istioctl proxy-config endpoints` |

## Exclusions: Always Skip

| Resource | Condition | Reason |
|----------|-----------|--------|
| Service | type=ClusterIP + clusterIP=None (headless) | Intentional: StatefulSet discovery, skip zombie check |
| Service | type=ExternalName | External dependency, not managed in-cluster |
| Service | namespace in (kube-system, istio-system, monitoring, cert-manager) | Infrastructure, not workload |
| ServiceEntry | spec.resolution=NONE or STATIC | Intentional external routing |
| k8s_orphan | resource referenced by any CronJob (even suspended) | Retained for scheduled use |
| k8s_orphan | Secret/ConfigMap with `kubernetes.io/` annotation prefix | System-managed |
| PVC | bound to Running pod via StatefulSet volumeClaimTemplate | Auto-provisioned, skip |
