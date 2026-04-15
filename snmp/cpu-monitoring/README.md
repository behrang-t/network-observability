# SNMP CPU Monitoring Pipeline

A Docker-based SNMPv3 monitoring mini-project for Cisco IOS XE devices.

This project started as a small runtime-only monitoring stack and was later **refactored into a three-phase workflow**:

1. **Device bootstrap** – prepare target routers for SNMPv3 polling
2. **Runtime monitoring** – collect CPU data, evaluate alert state, and send email notifications
3. **Evidence collection** – preserve logs, snapshots, state files, and test email screenshots from a successful run

The result is a small but realistic monitoring pipeline that demonstrates:

- SNMPv3 polling with Python
- service separation between collection and alerting
- Docker Compose orchestration
- Linux-based runtime execution on Ubuntu
- validation-driven troubleshooting with `snmpwalk`
- evidence-backed execution using Mailpit and curated runtime artifacts

---

## Architecture

### Phase 1 — Device bootstrap

The first phase prepares the target routers for SNMPv3 polling.

This phase is **intentionally kept outside** the main Docker Compose runtime so that device provisioning and runtime monitoring remain separate concerns.

Bootstrap is implemented with a small Netmiko-based helper/script workflow that:

- connects to the target devices over SSH
- pushes the required SNMPv3 configuration
- verifies the resulting SNMP user/group configuration
- stores bootstrap logs for later review

This separation keeps the monitoring stack focused on runtime behavior while still making the full workflow repeatable.

### Phase 2 — Runtime monitoring

The runtime stack is orchestrated with Docker Compose and is built around three services:

- **poller**
  - reads the device inventory from `shared/devices.json`
  - polls CPU values from the target devices via SNMPv3
  - appends historical values to `shared/cpu.csv`
  - writes the latest per-device snapshot to `shared/latest/<ip>.json`

- **alerter**
  - reads the latest snapshots from `shared/latest/`
  - applies threshold and cooldown logic
  - stores per-device alarm state in `shared/state/<ip>.json`
  - sends email notifications for:
    - `ALERT`
    - `REMINDER`
    - `RECOVERY`

- **mailpit**
  - acts as a local SMTP sink for testing
  - provides a web UI to validate generated notifications without using a real mail system

### Phase 3 — Evidence collection

A successful end-to-end run produces a curated **evidence pack** that documents both functionality and runtime behavior.

The evidence pack contains:

- Docker Compose service status
- poller logs
- alerter logs
- CPU history CSV output
- latest per-device snapshots
- per-device alert state files
- Mailpit screenshots showing generated emails
- bootstrap logs from Phase 1

---

## Project structure

```text
snmp_project/
├── bootstrap/
│   ├── netmiko_helper.py
│   ├── push_snmpv3.py
│   ├── snmpv3_profile.json
│   ├── vault.example.json
│   ├── requirements.txt
│   └── logs/
├─alerter/
│   ├── Dockerfile
│   ├── alerter.py
│   └── requirements.txt
├  ─poller/
│   ├── Dockerfile
│   ├── poller.py
│   └── requirements.txt
├── shared/
│   └── devices.json
├── evidence_pack/
└── docker-compose.yml
```

---

## Runtime design

This project is intentionally Docker-based.

The runtime pipeline is executed with Docker Compose on **Ubuntu**, where the services are built and run as isolated containers. This provides a clean and repeatable execution environment for the monitoring workflow.

At runtime, the data flow is:

```text
Cisco IOS XE routers -> poller -> shared artifacts -> alerter -> Mailpit
```

More specifically:

1. the **poller** retrieves CPU values from the routers via SNMPv3
2. the poller writes both historical and latest-state outputs
3. the **alerter** consumes the latest snapshots and evaluates alarm state
4. the alerter sends email notifications through **Mailpit**
5. outputs and logs are preserved in the evidence pack

---

## Device inventory

Target devices are defined in `shared/devices.json`.

Each device entry can include:

- `site`
- `ip`
- `cpu_oid`
- optionally `device_type` where applicable for bootstrap tooling

The project supports per-device CPU OID selection so that runtime polling can be adapted to the behavior of the specific target platform.

---

## Bootstrap phase details

The bootstrap phase was added as part of the refactor from a runtime-only stack to a fuller three-phase workflow.

It serves two purposes:

1. prepare the routers for SNMPv3 polling
2. make the setup step repeatable and auditable

The bootstrap tooling uses a small Netmiko-based approach instead of embedding provisioning inside Docker Compose. This keeps the runtime stack clean while still allowing repeatable preparation of lab devices.

Verification outputs from bootstrap are retained as evidence and copied into the final evidence pack.

---

## Validation and troubleshooting

### SNMP OID validation with `snmpwalk`

Before the final runtime test, SNMP OIDs were validated with `snmpwalk` against the target IOS XE routers.

This validation step was important because the originally expected CPU OID behavior was not sufficient for the target lab scenario. A working CPU OID was confirmed interactively and then applied to the runtime device inventory.

This ensured that the poller used a platform-validated OID instead of relying only on assumptions in code.

### Runtime dependency discovery

During runtime validation, an SNMPv3 privacy/encryption issue was exposed from inside the poller container.

Troubleshooting showed that the poller image was missing the crypto support required for the selected SNMPv3 privacy mode. This led to a correction in `snmpcheck/requirements.txt`, after which the container image was rebuilt and the runtime test was repeated successfully.

This is one of the most valuable outcomes of the project: the final implementation is not just theoretically correct, but **validated through containerized runtime troubleshooting**.

---

## Alerting behavior

The alerting service evaluates each device snapshot and maintains per-device state.

The policy supports the following transitions:

- **ALERT** – triggered when CPU rises above the threshold and no alarm is currently active
- **REMINDER** – triggered again after the cooldown interval if the alarm condition remains active
- **RECOVERY** – triggered when CPU falls back below the threshold after an active alarm
- **UNKNOWN** – used when polling does not return a valid CPU value; in this state the service logs the condition without sending email

This design allows the alerting logic to remain stateful and avoids simple stateless “threshold hit” behavior, also avoids alert storms and prevents repeated spam without 
cooldown.

---

## Evidence pack

The `evidence_pack/` directory contains curated outputs from a successful end-to-end test run.

The evidence pack was intentionally separated from transient runtime directories so that the project can preserve meaningful execution artifacts without committing noisy live-state directories.

Typical contents include:

- `docker compose ps` output
- exported poller logs
- exported alerter logs
- CPU CSV history
- latest snapshot samples
- alert state samples
- Mailpit screenshots for:
  - inbox view
  - alert email
  - reminder email
  - recovery email
- bootstrap logs

---

## Lab environment

This project was validated in a lab built around:

- **Cisco IOS XE routers** as SNMPv3 targets
- **Ubuntu** as the runtime host for Docker Compose
- **Mailpit** as the test SMTP platform

This matters because the project is not only a code exercise. It also demonstrates Linux-oriented execution skills around:

- Docker Compose lifecycle management
- runtime log collection
- filesystem-based artifact handling
- evidence preservation from a real test run

---

## Why this project matters

This mini-project demonstrates more than just SNMP polling.

It shows the ability to:

- separate provisioning from runtime behavior
- structure a monitoring pipeline into distinct services
- validate behavior with real devices
- troubleshoot runtime container issues methodically
- preserve an evidence-backed execution trail

For portfolio purposes, the project is especially useful because it provides a concrete baseline that can later be compared with a model-driven telemetry implementation.

---

## Future direction

This SNMP-based monitoring pipeline is intended to serve as a practical baseline for a future migration toward model-driven telemetry.

That next step would preserve the same high-level monitoring logic while replacing the SNMP polling collection layer with a more modern telemetry-based data pipeline.

---

## Summary

This project is a **refactored, Docker-based SNMPv3 monitoring workflow** with:

- an automated **bootstrap phase**
- a containerized **runtime monitoring phase**
- and a curated **evidence collection phase**

It combines Python, Docker Compose, Ubuntu runtime execution, SNMP validation, alert-state handling, test email delivery, and practical troubleshooting into a compact but realistic lab project.
