#!/usr/bin/with-contenv bash
# Enable remote RPC, quarantine download path, Execute plugin, and torrent-complete hook.
set -euo pipefail

python3 <<'PY'
import json
import os
import sys
import time
from pathlib import Path

QUARANTINE = os.environ.get("CONTAINER_DELUGE_QUARANTINE_PATH", "/downloads/quarantine").strip()
CORE_FILE = Path("/config/core.conf")
EXECUTE_FILE = Path("/config/execute.conf")
EXECUTE_MARKER = Path("/config/.deluge-execute-hook-configured")
HOOK_COMMAND = "/scripts/on-torrent-complete.sh"
EXECUTE_PLUGIN = "Execute"


def warn(msg: str) -> None:
    print(f"[deluge-init] WARNING: {msg}", file=sys.stderr)


def wait_for(path: Path, attempts: int = 30, delay: float = 2.0) -> bool:
    for _ in range(attempts):
        if path.is_file():
            return True
        time.sleep(delay)
    return False


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


def ensure_execute_hook() -> None:
    header = {"file": 1, "format": 1}
    body = {"commands": []}

    if EXECUTE_FILE.is_file():
        try:
            header, body = parse_deluge_json(EXECUTE_FILE)
        except json.JSONDecodeError as exc:
            warn(f"Could not parse {EXECUTE_FILE}: {exc}; recreating execute hook config")

    commands = body.setdefault("commands", [])
    hook = ["", "complete", HOOK_COMMAND]
    if not any(cmd[1:3] == hook[1:3] for cmd in commands if len(cmd) >= 3):
        commands.append(hook)

    write_deluge_json(EXECUTE_FILE, header, body)
    EXECUTE_MARKER.write_text("bootstrapped-from-repo\n", encoding="utf-8")
    print(f"[deluge-init] Execute hook configured: complete -> {HOOK_COMMAND}")


if not wait_for(CORE_FILE):
    warn(f"{CORE_FILE} not found; skipping Deluge download/execute bootstrap")
    raise SystemExit(0)

try:
    header, body = parse_deluge_json(CORE_FILE)
except json.JSONDecodeError as exc:
    warn(f"Could not parse {CORE_FILE}: {exc}")
    raise SystemExit(0)

body["allow_remote"] = True
body["download_location"] = QUARANTINE
body["move_completed"] = False
body["move_completed_path"] = QUARANTINE

plugins = list(body.get("enabled_plugins") or [])
if EXECUTE_PLUGIN not in plugins:
    plugins.append(EXECUTE_PLUGIN)
body["enabled_plugins"] = plugins

write_deluge_json(CORE_FILE, header, body)
print(f"[deluge-init] core.conf: allow_remote=true, download_location={QUARANTINE}")

ensure_execute_hook()
PY
