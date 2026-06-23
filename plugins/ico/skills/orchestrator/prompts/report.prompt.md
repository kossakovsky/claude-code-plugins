Read ALL {run_dir}/analysis/deep_scan_*.json AND {run_dir}/candidates.json AND {run_dir}/suspect_assessment.json.

**CRITICAL — Do NOT write your own CSS or HTML structure.** Instead, follow these EXACT steps:

1. Read `$PLUGINS/ico/skills/orchestrator/prompts/report-style.css` and copy its ENTIRE content into a `<style>` block
2. Read `$PLUGINS/ico/skills/orchestrator/prompts/service-topology.html` and copy its d3+dagre CDN scripts and renderTopo() function. For each compute resource, inject traffic_graph.edges + host_ip into the template code.

**CRITICAL — Coarse filter verdict is authoritative**: The zombie/active verdict for each resource is determined by the 3-signal coarse filter in `candidates.json` (field: `is_zombie_candidate`). Deep scan data provides DETAIL about the resource — it does NOT re-classify it. A resource with live traffic is still a zombie candidate if it failed the coarse filter. Do NOT override the coarse filter verdict.

**Report structure**: Generate ONE self-contained HTML at {run_dir}/reports/report.html. Use:
- `<div class="header">` with `.header-left` h1 + `.header-right` stat chips
- `<div class="rsrc-tabs">` for resource tabs, `<div class="sub-tabs">` for sub-tabs
- `<div class="content-panel">` wrapping all tab content
- `<table class="data-table">` for all tables
- `<div class="kv-grid">` with `.kv-row` > `.kv-key` + `.kv-val` for key-value pairs
- `<div class="metrics-grid">` with `.metric-card` for metric cards
- `<span class="badge badge-ok|badge-warn|badge-err">` for status badges
- `<span class="badge-type">` for type labels (COMPUTE, CACHE, etc.)
- `<div class="section-head"><span>Title</span><span class="sep"></span></div>` for section headers
- `<div class="usage-bar"><div class="fill low|mid|high"></div></div>` for disk usage bars

Generate ONE report containing all deep-scanned resources. Use Tabs:

- **Tab "Overview"** — Summary dashboard for all resources:
  - Table: resource_id, hostname, resource_type, verdict (read `is_zombie_candidate` from candidates.json — do NOT infer from deep scan), estimated_monthly_cost, key signal summary
  - MetricsDashboard: total scanned, zombie count (from coarse filter), active count (from coarse filter), total monthly cost

- **One Tab per resource** (labeled by hostname or IP). The content of each Tab depends on the resource's `resource_type` field.

## Resource Type → Report Components

### compute (VM/bare-metal)
The deep scan data is under `technical.*` — use these fields:
- **Tab 0 "Traffic"** — Service topology from technical.traffic_graph.edges
- **Tab 1 "Services"** — Table(technical.processes) + Table(technical.listening_ports)
- **Tab 2 "Scheduled Tasks"** — Table(technical.crontab_entries) + Table(technical.systemd_timers)
- **Tab 3 "Storage"** — KVList(technical.disk_partitions) + Callout(technical.disk_usage top 5)
- **Tab 4 "Ownership"** — KVList(business.owner) + MetricsDashboard(business.estimated_monthly_cost, spec)

### When deep scan data is empty
Fall back to Phase A signal summary from candidates.json.
Show the 3-signal status (CPU/Network/Login) as a StatusGrid + cost.

Save the report via Write tool — copy `prompts/report-style.css` into `<style>`, fill in all resource data, write as a SINGLE self-contained HTML at reports/report.html.
One file for ALL resources. Use resource tabs to switch between them.
Record file path in {run_dir}/reports/report_views.json.
