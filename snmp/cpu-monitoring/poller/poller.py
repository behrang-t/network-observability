
#!/usr/bin/env python3
"""
SNMP CPU Poller (long-running)

- Reads devices from /app/shared/devices.json
- Every INTERVAL_SEC seconds, polls CPU OID on all devices concurrently (Semaphore limit)
- Appends a history row to /app/shared/cpu.csv
- Writes an atomic per-device snapshot to /app/shared/latest/<ip>.json

Notes:
- On any SNMP/read failure, cpu_percent is written as null (JSON) / empty (CSV).
- Alerting/cooldown logic is intentionally handled by a separate alerter service.
"""

import asyncio
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    UsmUserData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    get_cmd,
    USM_AUTH_HMAC96_SHA,
    USM_PRIV_CFB128_AES,
)

# ----------------------------
# Config (env-friendly)
# ----------------------------
DEVICES_FILE = os.environ.get("DEVICES_FILE", "/app/shared/devices.json")
CSV_FILE     = os.environ.get("CSV_FILE", "/app/shared/cpu.csv")
LATEST_DIR   = os.environ.get("LATEST_DIR", "/app/shared/latest")

INTERVAL_SEC = int(os.environ.get("INTERVAL_SEC", "30"))
LIMIT        = int(os.environ.get("CONCURRENCY_LIMIT", "50"))

DEFAULT_CPU_OID = os.environ.get("DEFAULT_CPU_OID", "1.3.6.1.4.1.9.2.1.56.0")  # Cisco CPU 5sec

SNMP_USER = os.environ.get("SNMP_USER", "SNMPUser1")
SNMP_AUTH = os.environ.get("SNMP_AUTH", "AUTHPass1")
SNMP_PRIV = os.environ.get("SNMP_PRIV", "PRIVPass1")

SNMP_TIMEOUT = float(os.environ.get("SNMP_TIMEOUT", "2"))
SNMP_RETRIES = int(os.environ.get("SNMP_RETRIES", "1"))

_engine = SnmpEngine()

# ----------------------------
# IO helpers
# ----------------------------
def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def load_devices(path: str) -> list[dict[str, str]]:
    """
    expected JSON: list of objects with:
      - ip (required)
      - cpu_oid (optional)
      - site (optional)
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("devices.json must be a JSON list")
    out = []
    for item in data:
        if isinstance(item, dict) and "ip" in item:
            out.append({
                "ip": str(item["ip"]),
                "cpu_oid": str(item.get("cpu_oid") or DEFAULT_CPU_OID),
                "site": str(item.get("site") or ""),
            })
    if not out:
        raise ValueError("No valid devices in devices.json")
    return out

def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)  # atomic replace

def append_csv_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()

    fieldnames = ["timestamp_utc", "ip", "cpu_percent"]
    cpu = row.get("cpu_percent")

    safe = {
        "timestamp_utc": row["timestamp_utc"],
        "ip": row["ip"],
        "cpu_percent": "" if cpu is None else str(cpu),
    }

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if new_file:
            w.writeheader()
        w.writerow(safe)

# ----------------------------
# SNMP
# ----------------------------
async def snmp_get_cpu_percent(ip: str, oid: str) -> int | None:
    """
    returns:
      int  => cpu percent
      None => any failure or non-int response (=> UNKNOWN in alerter)
    """
    try:
        transport = await UdpTransportTarget.create(
            (ip, 161), timeout=SNMP_TIMEOUT, retries=SNMP_RETRIES
        )
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            _engine,
            UsmUserData(
                userName=SNMP_USER,
                authKey=SNMP_AUTH,
                privKey=SNMP_PRIV,
                authProtocol=USM_AUTH_HMAC96_SHA,
                privProtocol=USM_PRIV_CFB128_AES,
            ),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lookupMib=False,
        )

        if errorIndication:
            return None
        if errorStatus:
            return None

        _, val = varBinds[0]
        text = val.prettyPrint().strip()
        if text.startswith("No Such"):
            return None
        return int(text)
    except Exception:
        return None

async def poll_all(devices: list[dict[str, str]], limit: int) -> list[tuple[str, str, int | None]]:
    sem = asyncio.Semaphore(limit)

    async def bounded(dev: dict[str, str]):
        async with sem:
            ip = dev["ip"]
            oid = dev["cpu_oid"]
            cpu = await snmp_get_cpu_percent(ip, oid)
            return ip, oid, cpu

    tasks = [asyncio.create_task(bounded(d)) for d in devices]
    return await asyncio.gather(*tasks)

# ----------------------------
# Main loop
# ----------------------------
async def main() -> None:
    devices = load_devices(DEVICES_FILE)

    csv_path = Path(CSV_FILE)
    latest_dir = Path(LATEST_DIR)
    latest_dir.mkdir(parents=True, exist_ok=True)

    print(f"[poller] devices={len(devices)} interval={INTERVAL_SEC}s limit={LIMIT}")
    print(f"[poller] csv={csv_path}")
    print(f"[poller] latest_dir={latest_dir}")

    while True:
        ts = utc_iso()

        results = await poll_all(devices, LIMIT)

        for ip, _oid, cpu in results:
            append_csv_row(csv_path, {
                "timestamp_utc": ts,
                "ip": ip,
                "cpu_percent": cpu,
            })

            atomic_write_json(latest_dir / f"{ip}.json", {
                "timestamp_utc": ts,
                "ip": ip,
                "cpu_percent": cpu,   # int or None => JSON null
            })

            if cpu is None:
                print(f"[poller] {ts} ip={ip} cpu=UNKNOWN")
            else:
                print(f"[poller] {ts} ip={ip} cpu={cpu}")

        await asyncio.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    asyncio.run(main())
