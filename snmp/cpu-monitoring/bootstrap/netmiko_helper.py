
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
    ReadTimeout,
)

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_name(value: str) -> str:
    return value.replace(":", "_").replace("/", "_").replace(" ", "_")


def load_json_file(path: str | Path) -> Any:
    file_path = Path(path)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_devices(devices_file: str | Path) -> list[dict[str, str]]:
    data = load_json_file(devices_file)

    if not isinstance(data, list):
        raise ValueError("devices.json must be a JSON list")

    devices: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue

        ip = str(item.get("ip", "")).strip()
        if not ip:
            continue

        devices.append(
            {
                "ip": ip,
                "site": str(item.get("site", "")).strip() or "UNKNOWN",
                "device_type": str(item.get("device_type", "cisco_ios")).strip(),
            }
        )

    if not devices:
        raise ValueError("No valid devices found in devices.json")

    return devices


def load_profile(profile_file: str | Path) -> dict[str, Any]:
    data = load_json_file(profile_file)

    if not isinstance(data, dict):
        raise ValueError("snmpv3_profile.json must be a JSON object")

    required_keys = ["view_name", "group_name", "snmp_user", "verify_cmds"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Profile missing required key: {key}")

    if not isinstance(data["verify_cmds"], list) or not all(
        isinstance(x, str) and x.strip() for x in data["verify_cmds"]
    ):
        raise ValueError("verify_cmds must be a non-empty list of command strings")

    return data


def load_vault(vault_file: str | Path) -> dict[str, str]:
    data = load_json_file(vault_file)

    if not isinstance(data, dict):
        raise ValueError("vault.json must be a JSON object")

    required_keys = [
        "username",
        "password",
        "snmp_auth_pass",
        "snmp_priv_pass",
    ]
    for key in required_keys:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Vault missing required secret: {key}")

    secret = data.get("secret", "")
    if secret is None:
        secret = ""
    if not isinstance(secret, str):
        raise ValueError("Vault field 'secret' must be a string")

    return {
        "username": data["username"].strip(),
        "password": data["password"],
        "secret": secret.strip(),
        "snmp_auth_pass": data["snmp_auth_pass"],
        "snmp_priv_pass": data["snmp_priv_pass"],
    }


def build_snmpv3_config_cmds(
    *,
    view_name: str,
    group_name: str,
    snmp_user: str,
    snmp_auth_pass: str,
    snmp_priv_pass: str,
) -> list[str]:
    return [
        f"snmp-server view {view_name} iso included",
        f"snmp-server group {group_name} v3 priv read {view_name}",
        (
            f"snmp-server user {snmp_user} {group_name} v3 "
            f"auth sha {snmp_auth_pass} priv aes 128 {snmp_priv_pass}"
        ),
    ]


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def push_config_and_verify(
    *,
    ip: str,
    site: str,
    username: str,
    password: str,
    secret: str | None,
    config_cmds: list[str],
    verify_cmds: list[str],
    device_type: str = "cisco_ios",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "timestamp_utc": utc_iso(),
        "ip": ip,
        "site": site,
        "device_type": device_type,
        "config_applied": False,
        "save_ok": False,
        "verify_out": {},
        "error": None,
    }

    device: dict[str, Any] = {
        "ip": ip,
        "username": username,
        "password": password,
        "device_type": device_type,
        "fast_cli": False,
    }

    if secret:
        device["secret"] = secret

    conn = None
    try:
        conn = ConnectHandler(**device)

        if not conn.check_enable_mode():
            if secret:
                conn.enable()
            else:
                raise RuntimeError(
                    "Device is not in enable mode and no enable secret was provided."
                )

        # Do not capture cfg_out to avoid leaking secrets into logs.
        conn.send_config_set(config_cmds)
        result["config_applied"] = True

        try:
            conn.save_config()
        except Exception:
            conn.send_command("write memory", read_timeout=30)
        result["save_ok"] = True

        conn.send_command("terminal length 0", read_timeout=30)

        verify_out: dict[str, str] = {}
        for cmd in verify_cmds:
            verify_out[cmd] = conn.send_command(cmd, read_timeout=30)

        result["verify_out"] = verify_out

    except (ReadTimeout, NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        result["error"] = f"{type(e).__name__}: {e}"
    except Exception as e:
        result["error"] = f"UnexpectedError: {e}"
    finally:
        if conn is not None:
            conn.disconnect()

    return result