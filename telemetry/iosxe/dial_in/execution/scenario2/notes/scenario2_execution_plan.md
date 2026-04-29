# Scenario 2 Execution Plan

## Goal
Validate a temporary NETCONF-based dial-in telemetry subscription on Cat9000v for interface statistics.

## Target
- Device: Cat9000v
- Interface focus: GigabitEthernet0/0
- Payload file: `../payloads/interface_stats_dynamic_subscription.xml`

## Steps

1. Prepare the execution folders
   - `payloads/`
   - `notes/`
   - `evidence/`

2. Lock the exact execution target
   - device: `Cat9000v`
   - interface focus: `GigabitEthernet0/0`
   - target path: `/interfaces-ios-xe-oper:interfaces/interface`
   - period: `1000` centiseconds (`10s`)

3. Verify device-side prerequisites
   - confirm `netconf-yang` is enabled
   - confirm TCP/830 reachability from the client host

4. Prepare the local execution environment
   - select Python `3.13.7`
   - create and activate `.venv-dialin`
   - install required packages:
     - `ncclient`
     - `lxml`

5. Create and validate the XML payload
   - create `interface_stats_dynamic_subscription.xml`
   - ensure the payload contains only the `establish-subscription` element
   - validate the XML structure before execution

6. Prepare the NETCONF runner
   - set target host
   - set username/password
   - confirm payload and evidence paths are correct

7. Execute the NETCONF workflow
   - open the NETCONF session
   - send the subscription RPC
   - receive and save the RPC reply
   - extract and print the dynamic subscription ID
   - observe and save incoming notifications during the collection window

8. Capture the console execution log
   - run:
     ```bash
     python run_scenario2_netconf.py | tee ../evidence/scenario2_run.txt
     ```

9. Capture client-side evidence
   - save:
     - `scenario2_run.txt`
     - `scenario2_rpc_reply.xml`
     - `scenario2_notifications.xml`

10. Verify the dynamic subscription on the device while the session is alive
   - check that the subscription is present
   - verify that it is `Dynamic`
   - verify that it is `Valid`
   - record the device-side verification output

11. Close the NETCONF session and verify cleanup
   - let the session terminate normally
   - confirm the dynamic subscription no longer remains active
   - save cleanup verification evidence

12. Write a short close-out note
   - summarize:
     - whether the dynamic subscription worked
     - whether data was received
     - whether the temporary/session-bound behavior was confirmed

## Evidence
- `../evidence/scenario2_rpc_reply.xml`
- `../evidence/scenario2_notifications.xml`
- `../evidence/scenario2_run.txt`
- `../evidence/scenario2_device_dynamic_subscription.txt`
- `../evidence/scenario2_cleanup_verification.txt`
- `scenario2_closeout.md`
