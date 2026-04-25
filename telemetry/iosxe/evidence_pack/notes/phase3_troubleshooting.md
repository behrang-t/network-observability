# Troubleshooting Notes — Phase 3

These notes summarize the main issues encountered during phase-3 execution and how they were resolved or documented.

---

## 1) Telegraf TLS listener failed to start
### Symptom
After enabling TLS in `telegraf.conf`, Telegraf failed with a private-key read error and the listener on port `57000` was not available.

### Root cause
The private key mounted into the container had restrictive file permissions, causing a permission-denied error.

### Fix
Certificate and key permissions were adjusted so the Telegraf container could read them.

### Outcome
Telegraf started successfully with TLS enabled.

---

## 2) CSR1000v TLS receiver stayed in `Connecting`
### Symptom
On CSR1000v:
- telemetry subscription remained `Valid`
- TLS receiver stayed in `Connecting`
- no TLS telemetry updates arrived

### Root cause
CLI and logs showed:
- `%PKI-2-NON_AUTHORITATIVE_CLOCK`
- device clock was set, but there was **no authoritative time source**

Without an authoritative time source, PKI functions could not initialize properly.

### Evidence used
The following outputs were collected and stored:
- `show telemetry ietf subscription 101 detail`
- `show telemetry ietf subscription 101 receiver`
- `show crypto pki trustpoints MDT-CA status`
- `show crypto pki certificates MDT-CA`
- `show logging | include PKI|grpc|telemetry|SSL|TLS`
- `show clock detail`

### Resolution decision
No NTP server was added for this lab, because the effort did not justify the value for this project close-out.

### Final project treatment
- **Cat9000v TLS path** was used as the successful validation path
- **CSR1000v TLS issue** was recorded as a documented lab prerequisite limitation with identified root cause

---

## 3) Why raw evidence was preferred in several places
For some checks, raw or table-based evidence was stronger than charts:
- interface on-change validation
- schema discovery
- troubleshooting state changes
- TLS re-validation

This reduced ambiguity and made failure points easier to explain.

---

## Final note
The project was not closed on assumptions.
Each phase was closed only after:
1. the successful state was defined,
2. evidence was collected,
3. and failure points were either fixed or explicitly documented.
