# Scenario 2 Intent

- Scenario: NETCONF-based dial-in telemetry validation
- Device: Cat9000v
- Mechanism: NETCONF session with XML payload
- Focus interface: GigabitEthernet0/0
- Target path: `/interfaces-ios-xe-oper:interfaces/interface`
- Period: `1000` centiseconds (`10s`)
- Payload file: `../payloads/interface_stats_dynamic_subscription.xml`

## Goal
Validate a temporary dynamic telemetry subscription for interface statistics without building a permanent configured dial-out policy on the device.

## Expected outcome
- NETCONF session establishes successfully
- RPC reply returns a dynamic subscription ID
- notifications are received on the NETCONF session
- device shows a valid dynamic subscription while the session is alive
- dynamic subscription disappears after session teardown
