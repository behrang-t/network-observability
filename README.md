# Network Observability

Network observability workflows for SNMPv3 polling, IOS XE model-driven telemetry, metrics collection, visualization, alerting, and evidence-backed validation.

## Current implementation

### SNMPv3 CPU Monitoring

`snmp/cpu-monitoring/`

A containerized SNMPv3 monitoring workflow with:

- automated SNMPv3 bootstrap
- concurrent CPU polling
- state tracking
- threshold-based alerting
- Mailpit notification testing
- runtime and execution evidence

### IOS XE Model-Driven Telemetry

`telemetry/iosxe/`

A model-driven telemetry workflow with:

- IOS XE dial-out telemetry
- Telegraf collection
- InfluxDB time-series storage
- Grafana visualization and alerting
- periodic and on-change subscriptions
- TLS validation
- complementary dial-in / NETCONF validation
- evidence-backed troubleshooting and execution records

## Architecture

```text
Network Devices
     │
     ├── SNMPv3
     │     ↓
     │   Poller → State Evaluation → Alerting
     │
     └── Model-Driven Telemetry
           ↓
        Telegraf
           ↓
        InfluxDB
           ↓
         Grafana
           ↓
     Visualization / Alerting
```

## Repository layout

```text
network-observability/
├── snmp/
│   └── cpu-monitoring/
├── telemetry/
│   └── iosxe/
├── .gitignore
└── README.md
```

## Security note

Credentials included in examples are lab-only test values. Runtime credential files and generated TLS private keys are intentionally excluded from version control.

## Roadmap

- [x] SNMPv3 CPU monitoring pipeline
- [x] IOS XE model-driven telemetry pipeline
- [x] Visualization and alerting
- [x] TLS validation
- [ ] Synthetic network probes
- [ ] Log and event correlation
- [ ] Observability automation
