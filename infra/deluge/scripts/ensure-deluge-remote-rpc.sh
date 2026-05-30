#!/usr/bin/with-contenv bash
# Ensure Deluge RPC accepts connections from other containers (e.g. plex-orchestrator → gluetun:58846).
set -euo pipefail

python3 <<'PY'
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

CORE_FILE = Path("/config/core.conf")
MARKER = Path("/config/.deluge-remote-rpc-configured")
RPC_PORT = 58846


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


def rpc_port_open(host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, RPC_PORT), timeout=2):
            return True
    except OSError:
        return False


def wait_for_rpc(seconds: int = 60) -> bool:
    for _ in range(seconds):
        if rpc_port_open():
            return True
        time.sleep(1)
    return False


if not CORE_FILE.is_file():
    warn(f"{CORE_FILE} missing; cannot enable remote RPC")
    raise SystemExit(1)

header, body = parse_deluge_json(CORE_FILE)
if MARKER.is_file() and body.get("allow_remote"):
    if rpc_port_open():
        raise SystemExit(0)
    warn("Remote RPC marker present but daemon not responding; re-applying bootstrap")

changed = False
if not body.get("allow_remote"):
    body["allow_remote"] = True
    changed = True
    write_deluge_json(CORE_FILE, header, body)
    print("[deluge-init] core.conf: allow_remote=true")

if changed and Path("/run/service/svc-deluged").is_dir():
    subprocess.run(["s6-svc", "-d", "/run/service/svc-deluged"], check=False)
    time.sleep(2)
    subprocess.run(["s6-svc", "-u", "/run/service/svc-deluged"], check=False)
    print("[deluge-init] Restarted Deluge daemon once to apply allow_remote")

if not wait_for_rpc():
    warn(f"Deluge RPC not responding on 127.0.0.1:{RPC_PORT}")
    raise SystemExit(1)

MARKER.write_text("enabled\n", encoding="utf-8")
print(
    f"[deluge-init] Deluge RPC ready (allow_remote=true, port {RPC_PORT}); "
    "orchestrator can use gluetun:58846"
)
PY
