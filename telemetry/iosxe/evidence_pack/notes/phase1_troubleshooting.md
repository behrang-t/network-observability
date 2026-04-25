# Troubleshooting Notes — Phase 1

## 1) Grafana datasource failed with `127.0.0.1:8086`
### Symptom
Grafana reported connection refused when the datasource URL was set to `http://127.0.0.1:8086`.

### Cause
Grafana runs inside its own container. Inside that container, `127.0.0.1` refers to the Grafana container itself, not the InfluxDB service.

### Fix
Use the Docker Compose service name instead:
- `http://influxdb:8086`

Also use:
- **Query language:** Flux
- **Organization:** `lab`
- **Bucket:** `iosxe_telemetry`
- **Token:** the same token initialized for InfluxDB

---

## 2) Flux graph query failed with `unsupported input type for mean aggregate: string`
### Symptom
A Flux query on interface state data failed when `aggregateWindow(..., fn: mean)` was applied.

### Cause
Fields such as `admin_status` or `oper_status` are string/state values, not numeric values.

### Fix
Do not use `mean` for string fields.
Use one of these instead:
- raw/table view
- `last()`
- state-oriented visualization

---

## 3) First interface on-change XPath candidate was invalid
### Symptom
The first on-change subscription candidate returned `Invalid XPath filter` on the device.

### Cause
The candidate XPath was not valid for the specific platform/image under test.

### Fix
Do not insist on a failing path.
Use evidence-backed path discovery:
1. validate the candidate path with a periodic subscription first
2. once valid, change the same subscription to `on-change`
3. verify with real interface events (`shutdown / no shutdown`)

---

## 4) InfluxDB schema helper queries are not chart queries
### Symptom
Queries such as `schema.measurements()` or `schema.tagValues()` appeared to fail when used in graph-style visualization.

### Cause
These are metadata/schema queries and return table-style results rather than time-series graph data.

### Fix
Use them in the InfluxDB Data Explorer and inspect them in raw/table form.
Do not expect them to render as a line chart.

---

## 5) Telegraf logs may stay quiet even when telemetry is flowing
### Symptom
`docker compose logs -f telegraf` did not show continuous metric-by-metric updates.

### Cause
Telegraf does not necessarily print each telemetry sample in normal mode.
A quiet log does not automatically mean telemetry failure.

### Fix
Treat these as the real proof sources:
- receiver state on the device = Connected
- data visible in InfluxDB bucket
- successful queries against the expected measurement/field

---

## 6) Receiver binding behavior differed between tested IOS XE platforms
### Symptom
The same receiver design did not behave identically across all tested IOS XE platforms.
A globally named receiver worked on some platforms, while on others the telemetry flow was only stable when the receiver was bound directly under the subscription.

### Cause
Receiver binding behavior differed between the tested platform / image combinations in the lab.

### Fix
Keep a common receiver naming convention, but validate the binding method per platform.

---

## Working rule used in this phase
For every issue, the decision rule was:
1. identify the failure point
2. collect direct evidence from the closest component
3. fix the smallest possible layer
4. re-validate end-to-end
