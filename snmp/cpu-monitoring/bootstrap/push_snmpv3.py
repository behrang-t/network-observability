
#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from netmiko_helper import (
    build_snmpv3_config_cmds,
    load_devices,
    load_profile,
    load_vault,
    push_config_and_verify,
    safe_name,
    write_json,
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

DEVICES_FILE = PROJECT_DIR / "shared" / "devices.json"
PROFILE_FILE = BASE_DIR / "snmpv3_profile.json"
VAULT_FILE = BASE_DIR / "vault.json"
LOGS_DIR = BASE_DIR / "logs"


def main() -> None:
    devices = load_devices(DEVICES_FILE)
    profile = load_profile(PROFILE_FILE)
    vault = load_vault(VAULT_FILE)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    config_cmds = build_snmpv3_config_cmds(
        view_name=profile["view_name"],
        group_name=profile["group_name"],
        snmp_user=profile["snmp_user"],
        snmp_auth_pass=vault["snmp_auth_pass"],
        snmp_priv_pass=vault["snmp_priv_pass"],
    )

    verify_cmds = profile["verify_cmds"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Loaded {len(devices)} devices from: {DEVICES_FILE}")
    print(f"Using profile: {PROFILE_FILE}")
    print(f"Using vault:   {VAULT_FILE}")
    print("\nBootstrap started...\n")

    summary: list[dict[str, str]] = []

    for device in devices:
        ip = device["ip"]
        site = device["site"]
        device_type = device["device_type"]

        print(f"--- Device: {site} ({ip}) ---")

        result = push_config_and_verify(
            ip=ip,
            site=site,
            username=vault["username"],
            password=vault["password"],
            secret=vault["secret"] or None,
            config_cmds=config_cmds,
            verify_cmds=verify_cmds,
            device_type=device_type,
        )

        out_file = LOGS_DIR / (
            f"{timestamp}_{safe_name(site)}_{safe_name(ip)}_snmpv3_bootstrap.json"
        )
        write_json(out_file, result)

        if result["error"]:
            print(f"[FAIL] {ip} -> {result['error']}\n")
            summary.append({"site": site, "ip": ip, "status": "FAIL"})
        else:
            print(f"[OK]   {ip} -> config pushed and verified\n")
            summary.append({"site": site, "ip": ip, "status": "OK"})

    print("=== Summary ===")
    for item in summary:
        print(f"{item['site']:>8}  {item['ip']:<15}  {item['status']}")


if __name__ == "__main__":
    main()