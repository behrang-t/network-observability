from pathlib import Path
import time
from lxml import etree
from ncclient import manager
from ncclient.xml_ import to_ele

HOST = "192.168.2.63"
PORT = 830
USERNAME = "test"
PASSWORD = "test"

# Resolve project-relative paths safely
BASE_DIR = Path(__file__).resolve().parent.parent
PAYLOAD_FILE = BASE_DIR / "payloads" / "interface_stats_dynamic_subscription.xml"
EVIDENCE_DIR = BASE_DIR / "evidence"
OBSERVE_SEC = 90


def save_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    payload = PAYLOAD_FILE.read_text(encoding="utf-8")

    with manager.connect(
        host=HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        timeout=30,
    ) as m:
        reply = m.dispatch(to_ele(payload))

        reply_xml = reply.xml
        save_text(EVIDENCE_DIR / "scenario2_rpc_reply.xml", reply_xml)

        root = etree.fromstring(reply_xml.encode())
        sub_id = root.xpath("string(//*[local-name()='subscription-id'])")
        print(f"Dynamic subscription ID: {sub_id}")

        notifications = []
        start = time.time()

        while time.time() - start < OBSERVE_SEC:
            n = m.take_notification(timeout=5)
            if n is not None:
                notifications.append(n.notification_xml)

        joined = "\n\n".join(notifications)
        save_text(EVIDENCE_DIR / "scenario2_notifications.xml", joined)

        print(f"Saved {len(notifications)} notifications.")
        print("NETCONF session will now close.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        raise
