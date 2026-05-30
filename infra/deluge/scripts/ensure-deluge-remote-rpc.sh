#!/usr/bin/with-contenv bash
# Ensure Deluge RPC accepts connections from other containers (e.g. plex-orchestrator → gluetun:58846).
set -euo pipefail

python3 <<'PY'
import json
import subprocess
import sys
import time
from pathlib import Path

CORE_FILE = Path("/config/core.conf")


def warn(msg: str) -> None:
    print(f"[deluge-init] WARNING: {msg}", file=sys.stderr)


def parse_deluge_json(path: Path) -> tuple[dict, dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    split_at = text.find("}{")
    if split_at == -1:
        body = json.loads(text)
        return {"file": 1, "format": 1}, body
    header = json.loads(text[: split_at + 1])
    body = json.loads(text[split_at + 1 :])
    return header, body


def write_deluge_json(path: Path, header: dict, body: dict) -> None:
    path.write_text(json.dumps(header) + json.dumps(body, indent=4) + "\n", encoding="utf-8")


def rpc_listening_on_all_interfaces() -> bool:
    try:
        out = subprocess.check_output(
            ["ss", "-tln"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return "0.0.0.0:58846" in out or "*:58846" in out


if not CORE_FILE.is_file():
    warn(f"{CORE_FILE} missing; cannot enable remote RPC")
    raise SystemExit(1)

header, body = parse_deluge_json(CORE_FILE)
changed = False
if not body.get("allow_remote"):
    body["allow_remote"] = True
    changed = True

if changed:
    write_deluge_json(CORE_FILE, header, body)
    print("[deluge-init] core.conf: allow_remote=true")

if changed or not rpc_listening_on_all_interfaces():
    if Path("/run/service/svc-deluged").is_dir():
        subprocess.run(["s6-svc", "-d", "/run/service/svc-deluged"], check=False)
        time.sleep(2)
        subprocess.run(["s6-svc", "-u", "/run/service/svc-deluged"], check=False)
        print("[deluge-init] Restarted Deluge daemon for remote RPC")
        for _ in range(30):
            if rpc_listening_on_all_interfaces():
                break
            time.sleep(1)
    else:
        warn("svc-deluged not found; restart Deluge container to apply allow_remote")

if rpc_listening_on_all_interfaces():
    print("[deluge-init] Deluge RPC listening for remote connections on port 58846")
else:
    warn("Deluge RPC still not reachable on 0.0.0.0:58846 after restart")
    raise SystemExit(1)
PY
