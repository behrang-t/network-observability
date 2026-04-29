# Dial-In Telemetry Design Note

## 1. Context

The primary telemetry pipeline in this repository was intentionally implemented with **configured dial-out subscriptions**. That choice fits the main operational goal of the project:

- persistent monitoring
- collector-first architecture
- evidence-backed validation
- stable day-2 observability

That baseline is already complete in `08_iosxe_telemetry_pipeline/`.

This note captures the complementary role of **dial-in / dynamic telemetry subscriptions**. The purpose here is not to replace the configured dial-out design, but to identify where temporary, session-bound subscriptions remain operationally useful.

---

## 2. Why dial-in still matters

Dynamic subscriptions still have clear value in practical network operations, especially when the operator wants to collect telemetry for a limited time without leaving a persistent telemetry policy behind on the device.

Typical reasons include:

- temporary troubleshooting
- short-lived validation of paths and sample cadence
- observation windows that should not alter the long-term running configuration
- focused collection during an incident or an experiment
- low-footprint testing before promoting a path into the configured dial-out baseline

The key idea is simple:

**dial-out is the right default for persistent monitoring, while dial-in remains a useful operational tool for short-lived, targeted telemetry tasks.**

---

## 3. Dial-out vs dial-in

| Aspect | Dial-out configured telemetry | Dial-in / dynamic telemetry |
|---|---|---|
| Primary use | Persistent monitoring | Temporary troubleshooting or testing |
| Lifetime | Stays on device until removed | Session-bound or explicitly temporary |
| Running-config footprint | Yes | Can be avoided or minimized |
| Collector behavior | Waits for device push | Controller/session creates subscription |
| Operational style | Stable baseline pipeline | Short-lived, targeted, investigative |

This project chose dial-out for the main pipeline because it is a better fit for permanent collection, dashboards, alerting, and hardening.

This note keeps dial-in in scope as a secondary operational pattern.

---

## 4. Scenario 1 — Temporary troubleshooting

### Description
Two edge routers are suspected of having an intermittently problematic uplink. For a short troubleshooting window, interface statistics are collected at a higher cadence than the baseline design, without leaving a permanent telemetry configuration on the device.

### Why dial-in fits
- temporary
- scoped to a troubleshooting window
- avoids leaving a permanent telemetry policy behind
- useful when the operator wants to collect more aggressive data only during an incident

### Typical objective
- collect interface statistics for 20 minutes
- inspect drops, packet counters, or error-related fields
- end the session and let the temporary subscription disappear

### Operational value
This is a strong real-world use case because it minimizes configuration residue while still giving the operator targeted visibility during a live investigation.

---

## 5. Scenario 2 — Short-lived validation / test subscription

### Description
A NETCONF session on IOS XE creates a temporary telemetry subscription with an XML payload in order to validate:

- the sensor path
- the subscription behavior
- the data cadence
- the session-bound receiver path

The goal is not to build a permanent monitoring policy. The goal is to prove that the path and telemetry workflow behave as expected.

### Why dial-in fits
- fast to test
- low commitment
- no requirement to keep a permanent running-config change
- good bridge between YANG/NETCONF theory and operational use

### Why this scenario was selected for execution
Among the three scenarios, this one is the smallest and cleanest footprint to implement while still producing meaningful evidence. It is therefore the best choice for a lightweight execution trace that keeps this design note grounded.

### Execution note
Scenario 2 is implemented under:

```text
dial_in/execution/scenario2/
```

---

## 6. Scenario 3 — Temporary observation without changing the real running configuration

### Description
The operator wants a short observation window for CPU or interface state, but does not want to add a durable monitoring policy to the running configuration of the device.

### Why dial-in fits
- useful for safe observation
- suitable for pre-change or post-change checks
- reduces configuration footprint on the device
- keeps the monitoring action intentionally temporary

### Example use
Observe CPU and interface state for a limited window before deciding whether a path should become part of the permanent dial-out baseline.

---

## 7. Modeling note: YANG `grouping` / `uses`

This project does **not** claim that a complete YANG model was implemented for these dial-in scenarios.

However, from a design perspective, if these use cases were to be represented in a **controller-side model** or a **reusable telemetry profile library**, then YANG `grouping` and `uses` would be a natural fit.

### Why
These scenarios share repeated conceptual elements such as:
- target device list
- receiver settings
- sample cadence
- subscription lifetime
- sensor selection
- validation metadata

A reusable design could define common structures once and instantiate them in different temporary telemetry profiles.

### Example conceptual grouping candidates
- `target-devices`
- `receiver-settings`
- `sampling-policy`
- `temporary-window`
- `interface-stats-sensor`
- `cpu-sensor`
- `bfd-session-sensor`

### Example conceptual profile reuse
- `temporary-interface-troubleshoot-profile`
- `temporary-interface-validation-profile`
- `temporary-bfd-investigation-profile`

In this note, `grouping` / `uses` is treated as a **design pattern for reuse**, not as an already implemented YANG artifact.

---

## 8. Execution footprint — Scenario 2 on Cat9000v

This note intentionally includes a small execution footprint so that it does not remain purely conceptual.

### Selected target
- **Device:** Cat9000v
- **Mechanism:** NETCONF session with XML payload
- **Purpose:** create a temporary telemetry subscription for interface statistics

### Why Cat9000v
The Cat9000v platform was already validated successfully in the configured dial-out telemetry project. Reusing it for the dynamic proof-of-concept keeps the environment small and reduces moving parts.

### Execution goal
Prove a minimal dynamic workflow:
1. establish a NETCONF session
2. send an XML payload that creates a telemetry subscription
3. validate the resulting dynamic subscription on the device
4. verify notification arrival on the same NETCONF session
5. capture evidence

### Expected evidence
- XML payload sample
- NETCONF response or session confirmation
- device-side verification output
- one or more received notifications
- a short execution note describing the result

### Status
Scenario 2 was executed successfully on Cat9000v.

The execution confirmed that:
- a NETCONF session could establish successfully
- the XML payload created a dynamic telemetry subscription
- the device reported a valid dynamic subscription during session lifetime
- NETCONF notifications were received as execution evidence
- the temporary subscription disappeared after session teardown

This kept the dial-in footprint small while still validating the temporary, session-bound telemetry behavior.
