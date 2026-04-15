
#!/usr/bin/env python3
"""
SNMP CPU Alerter (long-running)

Reads snapshots from:
  /app/shared/latest/<ip>.json
    {"timestamp_utc": "...", "ip": "...", "cpu_percent": <int|null>}

Writes per-device state to:
  /app/shared/state/<ip>.json   (atomic write)

Policy:
- cpu_percent is null => status=UNKNOWN (log only, no email)
- cpu_percent >= THRESHOLD => HIGH
    - if alarm_active was False => ALERT email, set alarm_active=True
    - if alarm_active True and cooldown passed => REMINDER email
- cpu_percent < THRESHOLD => OK
    - if alarm_active True => RECOVERY email, set alarm_active=False
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

# ----------------------------
# Config
# ----------------------------
LATEST_DIR   = os.environ.get("LATEST_DIR", "/app/shared/latest")
STATE_DIR    = os.environ.get("STATE_DIR", "/app/shared/state")

INTERVAL_SEC = int(os.environ.get("ALERTER_INTERVAL_SEC", "40"))
THRESHOLD    = int(os.environ.get("THRESHOLD", "80"))
COOLDOWN_SEC = int(os.environ.get("COOLDOWN_SEC", str(60 * 60)))  # 1 hour

SMTP_HOST = os.environ.get("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
MAIL_FROM = os.environ.get("MAIL_FROM", "snmp@lab.local")
MAIL_TO   = os.environ.get("MAIL_TO", "ops@lab.local")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("alerter")

# ----------------------------
# Helpers
# ----------------------------
def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)

def read_json(path: Path) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None

def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")  
    # e.g. x.json -> x.json.tmp
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)

def send_email(subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    import smtplib
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as s:
        s.send_message(msg)

def compute_status(cpu: int | None) -> str:
    if cpu is None:
        return "UNKNOWN"
    return "HIGH" if cpu >= THRESHOLD else "OK"

def safe_name(s: str) -> str:
    return s.replace(":", "_").replace("/", "_")

# ----------------------------
# Core per snapshot
# ----------------------------
def process_snapshot(snapshot_path: Path) -> None:
    snap = read_json(snapshot_path)
    if not snap:
        log.info("unreadable snapshot: %s", snapshot_path)
        return

    ip = snap.get("ip")
    if not ip:
        log.info("snapshot missing ip: %s", snapshot_path)
        return
    ip = str(ip)

    snap_ts_utc = str(snap.get("timestamp_utc") or "")
    raw_cpu = snap.get("cpu_percent", None)

    try:
        cpu = None if raw_cpu is None else int(raw_cpu)
    except Exception:
        cpu = None

    status = compute_status(cpu)

    st_path = Path(STATE_DIR) / f"{safe_name(ip)}.json"
    st = read_json(st_path) or {}

    alarm_active = bool(st.get("alarm_active", False))
    last_alert_ts = st.get("last_alert_ts")
    if not isinstance(last_alert_ts, str):
        last_alert_ts = None

    now_utc = utc_iso()
    now_dt = parse_iso(now_utc)

    elapsed_sec = None
    if last_alert_ts:
        try:
            elapsed_sec = (now_dt - parse_iso(last_alert_ts)).total_seconds()
        except Exception:
            elapsed_sec = None

    action: str | None = None

    # ----- decision logic -----
    if status == "UNKNOWN":
        # log only; do NOT change alarm_active
        action = None

    elif status == "HIGH":
        if not alarm_active:
            action = "ALERT"
            alarm_active = True
            last_alert_ts = now_utc
        else:
            if last_alert_ts is None or elapsed_sec is None or elapsed_sec >= COOLDOWN_SEC:
                action = "REMINDER"
                last_alert_ts = now_utc

    elif status == "OK":
        if alarm_active:
            action = "RECOVERY"
            alarm_active = False
            last_alert_ts = now_utc

    # write state always
    new_state = {
        "ip": ip,
        "status": status,
        "alarm_active": alarm_active,
        "last_alert_ts": last_alert_ts,
        "updated_ts": now_utc,
    }
    atomic_write_json(st_path, new_state)

    if status == "UNKNOWN":
        log.info("ip=%s status=UNKNOWN (cpu_percent is null) snap=%s", ip, snap_ts_utc)
        return

    if action is None:
        return

    cpu_txt = "UNKNOWN" if cpu is None else str(cpu)
    subject = f"[SNMP CPU] {action} ip={ip} cpu={cpu_txt} thr={THRESHOLD}"
    body = "\n".join([
        f"Action: {action}",
        f"IP: {ip}",
        f"Snapshot time (UTC): {snap_ts_utc}",
        f"CPU (%): {cpu_txt}",
        f"Threshold (%): {THRESHOLD}",
        f"Cooldown (sec): {COOLDOWN_SEC}",
    ])

    try:
        send_email(subject, body)
        log.info("ip=%s email sent (%s) cpu=%s snap=%s", ip, action, cpu_txt, snap_ts_utc)
    except Exception as e:
        log.info("ip=%s email FAILED (%s) err=%s snap=%s", ip, action, e, snap_ts_utc)

# ----------------------------
# Main loop
# ----------------------------
async def main() -> None:
    latest_dir = Path(LATEST_DIR)
    Path(STATE_DIR).mkdir(parents=True, exist_ok=True)

    while True:
        for snap_file in sorted(latest_dir.glob("*.json")):
            process_snapshot(snap_file)

        await asyncio.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    asyncio.run(main())
