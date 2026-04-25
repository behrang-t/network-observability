# IOS XE Telemetry Pipeline

## Project position in the repository
- **Baseline project:** `07_snmp_cpu_monitoring_pipeline`
- **Next-generation project:** `08_iosxe_telemetry_pipeline`

This project is the next-generation, model-driven monitoring workflow that follows the earlier SNMP-based baseline monitoring workflow.

---

## Current project status
The project is organized into three phases:

- **Phase 1 — Baseline telemetry pipeline** ✅ complete
- **Phase 2 — Alerting** ✅ complete
- **Phase 3 — Hardening (TLS)** ✅ complete for the primary validation path

This README reflects the completion of the full project scope, with one documented lab-specific limitation:

- **Cat9000v:** telemetry pipeline validated successfully with TLS
- **CSR1000v:** baseline telemetry validated successfully; TLS receiver did not complete due to lack of an authoritative time source for PKI initialization, and this was 
documented as a lab prerequisite issue rather than left unexplained

---

## Project goal
Build and validate an **IOS XE model-driven telemetry pipeline** with evidence-backed execution.

The final scope includes:
- collector stack bring-up
- receiver path validation from device to collector
- **CPU periodic telemetry** end-to-end
- **interface state telemetry** with **on-change** updates
- **Grafana alerting** with Mailpit email delivery
- **TLS hardening** of the telemetry transport
- collection of execution evidence for all phases

---

## Architecture
**Mode:** configured dial-out subscription  
**Transport:** gRPC  
**Receiver protocol on device:** `grpc-tcp` in baseline, then `grpc-tls` in hardening  
**Encoding:** `encode-kvgpb`  
**Collector plugin:** `inputs.cisco_telemetry_mdt`

### Data flow
`IOS XE device -> Telegraf -> InfluxDB -> Grafana -> Mailpit`

### Stack
- **Telegraf** = telemetry receiver / collector
- **InfluxDB 2** = storage
- **Grafana** = visualization and alerting
- **Mailpit** = test SMTP target for alert validation

### Platform used
- **Cat9000v**
- **CSR1000v**
- **Ubuntu collector host**

---

## Design decisions

### CPU stream
- periodic telemetry
- one-minute CPU path used for stable visualization
- used to establish the first end-to-end green path
- later reused for alerting and TLS re-validation

### Interface stream
- on-change telemetry
- interface subtree path was validated first
- event behavior was verified with `shutdown / no shutdown`
- evidence was collected from InfluxDB raw/query output rather than relying only on charts

### Receiver design
- **Cat9000v:** validated with a named receiver profile
  - `RCVR-TELEGRAF-GRPC`
- **CSR1000v:** validated with a subscription-level receiver configuration where platform behavior differed in lab use

### TLS hardening approach
- baseline telemetry was first validated over non-TLS transport
- TLS was then enabled on the collector and on the device side
- Cat9000v completed TLS validation successfully
- CSR1000v entered a documented TLS limitation state tied to PKI time-source requirements

---

## Phase summary

### Phase 1 — Baseline telemetry pipeline
Validated:
- collector stack bring-up
- receiver path validation
- CPU periodic telemetry end-to-end
- interface on-change telemetry end-to-end
- evidence collection

Successful outputs:
- Docker Compose stack operational
- Telegraf listener active on expected receiver port
- InfluxDB health endpoint reachable
- Grafana datasource validated
- device receivers connected
- configured telemetry subscriptions valid
- CPU telemetry visible in InfluxDB and Grafana
- interface on-change updates visible in InfluxDB after interface state changes

### Phase 2 — Alerting
Validated:
- CPU alert rule in Grafana
- interface down alert rule in Grafana
- SMTP path to Mailpit
- alert evidence collection

Successful outputs:
- Grafana contact point working
- Mailpit email delivery verified
- CPU alert fired and delivered
- interface down alert fired and delivered
- screenshots collected for rule configuration and delivered alerts

### Phase 3 — Hardening (TLS)
Validated:
- local lab CA generation
- server certificate for Telegraf collector
- TLS-enabled telemetry receiver path
- telemetry re-validation after enabling TLS

Successful outputs:
- Cat9000v telemetry validated successfully over `grpc-tls`
- CPU periodic telemetry still visible after TLS enablement
- interface on-change telemetry still visible after TLS enablement
- TLS evidence collected for collector and device side

Documented limitation:
- CSR1000v TLS receiver remained in `Connecting` state
- root cause identified through CLI and logs:
  - **PKI could not initialize fully because the device had no authoritative time source**
- baseline non-TLS telemetry on CSR1000v remained valid
- the issue was documented in evidence rather than hidden

---

## Directory layout
```text
08_iosxe_telemetry_pipeline/
├── collector/
│   ├── telegraf/
│   │   ├── telegraf.conf
│   │   └── certs/
│   ├── influxdb/
│   │   └── init/
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/
├── device_configs/
│   └── iosxe/
│       ├── cpu_periodic.txt
│       ├── interface_on_change.txt
│       ├── receiver_profile_tls.txt
│       └── notes/
├── evidence_pack/
│   ├── logs/
│   ├── sample_metrics/
│   └── screenshots/
├── docker-compose.yml
└── README.md
```

---

## Evidence-backed execution
The project was closed only after evidence was collected for:
- collector health
- device receiver and subscription state
- telemetry data visibility
- alert delivery
- TLS re-validation

### Evidence directory
```text
examples/06_netauto_ecosystem/08_iosxe_telemetry_pipeline/evidence_pack/
```

### Typical evidence captured

#### Collector logs
- Compose service status
- InfluxDB health output
- Telegraf live and captured logs
- phase-specific alerting / TLS logs

#### Device CLI evidence
- CPU periodic subscription verification output
- interface on-change subscription verification output
- TLS receiver and subscription verification output
- CSR1000v TLS limitation evidence with PKI / clock context

#### Screenshots
- InfluxDB datasource and bucket validation
- CPU periodic visibility in InfluxDB and Grafana
- before/after evidence for interface on-change behavior
- Grafana alerting configuration and Mailpit deliveries
- TLS validation screenshots

---

## Runtime notes

### Docker volumes
- `influxdb2-data` persists InfluxDB data
- `grafana-data` persists Grafana state

### Telegraf output path
Telegraf writes to InfluxDB v2 using the standard `outputs.influxdb_v2` output plugin.

### Grafana usage
Grafana was used for:
- datasource validation
- CPU visualization
- alert rule creation
- email delivery validation through Mailpit

For interface on-change verification, **InfluxDB raw/query evidence** remained the strongest proof of state transitions.

---

## Completion criteria
The project is considered complete because all of the following were achieved:

- collector stack is operational
- device receivers are connected for the validated baseline paths
- CPU periodic telemetry is visible end-to-end
- interface on-change updates are visible after state change events
- alerting works through Grafana and Mailpit
- TLS hardening is validated successfully on the primary platform path
- remaining platform-specific TLS limitation is documented with identified root cause
- execution evidence has been collected and stored

---

## Summary
This project established a **working IOS XE model-driven telemetry pipeline** using:
- configured dial-out subscriptions
- gRPC transport
- Telegraf as the collector
- InfluxDB as storage
- Grafana for visualization and alerting
- Mailpit for test email delivery
- TLS hardening for the validated primary platform path

The pipeline is evidence-backed across baseline telemetry, alerting, and hardening.  
Cat9000v completed the full validation path, while CSR1000v TLS behavior was reduced to a clearly documented lab prerequisite issue rather than an unresolved ambiguity.
