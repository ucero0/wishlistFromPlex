#!/usr/bin/with-contenv bash
# Apply Deluge RPC + Web UI credentials from .env after the Deluge daemon has started.
set -euo pipefail

python3 <<'PY'
import os
import sys
import time
from pathlib import Path

USERNAME = os.environ.get("DELUGE_USERNAME", "deluge").strip()
PASSWORD = os.environ.get("DELUGE_PASSWORD", "").strip()
LEVEL = os.environ.get("DELUGE_AUTH_LEVEL", "10").strip()

AUTH_FILE = Path("/config/auth")
KNOWN_WEAK = ("deluge", "")


def warn(msg: str) -> None:
    print(f"[deluge-init] WARNING: {msg}", file=sys.stderr)


def wait_for(path: Path, attempts: int = 60, delay: float = 2.0) -> bool:
    for _ in range(attempts):
        if path.is_file():
            return True
        time.sleep(delay)
    return False


if PASSWORD in KNOWN_WEAK:
    warn(
        'DELUGE_PASSWORD is missing or still "deluge". '
        "Set a strong password in .env before first start in production."
    )

if not wait_for(AUTH_FILE):
    print("[deluge-init] /config/auth not found after waiting; skipping credential setup")
    raise SystemExit(1)

lines = AUTH_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
updated: list[str] = []
user_present = False

for line in lines:
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith("localclient:"):
        updated.append(stripped)
        continue

    parts = stripped.split(":")
    if len(parts) < 3:
        updated.append(stripped)
        continue

    entry_user, entry_pass = parts[0], parts[1]
    if entry_user == "deluge" and entry_pass == "deluge":
        continue
    if entry_user == USERNAME:
        updated.append(f"{USERNAME}:{PASSWORD}:{LEVEL}")
        user_present = True
        continue

    updated.append(stripped)

if not user_present:
    updated.append(f"{USERNAME}:{PASSWORD}:{LEVEL}")

AUTH_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")
print(f"[deluge-init] RPC user '{USERNAME}' configured from .env")
PY

WEB_PASSWORD="${DELUGE_WEB_PASSWORD:-${DELUGE_PASSWORD:-}}"
FORCE_WEB="${DELUGE_FORCE_WEB_PASSWORD:-false}"
WEB_MARKER="/config/.deluge-web-password-configured"

if [[ -z "$WEB_PASSWORD" || "$WEB_PASSWORD" == "deluge" ]]; then
  echo "[deluge-init] WARNING: Web UI password not set; skipping Web UI bootstrap." >&2
  exit 0
fi

if [[ -f "$WEB_MARKER" && "${FORCE_WEB,,}" != "true" && "$FORCE_WEB" != "1" ]]; then
  echo "[deluge-init] Web UI password already bootstrapped (set DELUGE_FORCE_WEB_PASSWORD=true to overwrite)"
  exit 0
fi

# deluge-web overwrites web.conf on shutdown unless it is stopped first
if [[ -d /run/service/svc-deluge-web ]]; then
  s6-svc -d /run/service/svc-deluge-web 2>/dev/null || true
  sleep 2
fi

python3 <<'PY'
import hashlib
import json
import os
import secrets
from pathlib import Path

WEB_PASSWORD = os.environ.get("DELUGE_WEB_PASSWORD", os.environ.get("DELUGE_PASSWORD", "")).strip()
WEB_FILE = Path("/config/web.conf")
HOSTLIST_FILE = Path("/config/hostlist.conf")
WEB_MARKER = Path("/config/.deluge-web-password-configured")
WEB_HEADER = {"file": 2, "format": 1}
WEB_DEFAULTS = {
    "enabled_plugins": [],
    "default_daemon": "",
    "pwd_salt": "",
    "pwd_sha1": "",
    "session_timeout": 3600,
    "sessions": {},
    "sidebar_show_zero": False,
    "sidebar_multiple_filters": True,
    "show_session_speed": False,
    "show_sidebar": True,
    "theme": "gray",
    "first_login": False,
    "language": "",
    "base": "/",
    "interface": "0.0.0.0",
    "port": 8112,
    "https": False,
    "pkey": "ssl/daemon.pkey",
    "cert": "ssl/daemon.cert",
}


def default_daemon_from_hostlist() -> str:
    if not HOSTLIST_FILE.is_file():
        return ""
    text = HOSTLIST_FILE.read_text(encoding="utf-8", errors="replace")
    start = text.find('{"hosts"')
    if start == -1:
        start = text.find('"hosts"')
        if start == -1:
            return ""
        start = text.rfind("{", 0, start)
    try:
        data = json.loads(text[start:])
        hosts = data.get("hosts") or []
        if hosts and hosts[0]:
            return str(hosts[0][0])
    except json.JSONDecodeError:
        pass
    return ""


def read_web_config() -> dict:
    if not WEB_FILE.is_file():
        config = dict(WEB_DEFAULTS)
        config["default_daemon"] = default_daemon_from_hostlist()
        return config
    text = WEB_FILE.read_text(encoding="utf-8", errors="replace").strip()
    start = text.find('{"base"')
    if start == -1:
        start = text.find("{", text.find("}") + 1 if "}" in text else 0)
    return json.loads(text[start:])


def write_web_config(config: dict) -> None:
    WEB_FILE.write_text(
        json.dumps(WEB_HEADER, indent=4) + json.dumps(config, indent=4) + "\n",
        encoding="utf-8",
    )


config = read_web_config()
if not config.get("default_daemon"):
    config["default_daemon"] = default_daemon_from_hostlist()

salt = secrets.token_hex(20)
config["pwd_salt"] = salt
config["pwd_sha1"] = hashlib.sha1((salt + WEB_PASSWORD).encode("utf-8")).hexdigest()
config["first_login"] = False
write_web_config(config)
WEB_MARKER.write_text("bootstrapped-from-env\n", encoding="utf-8")
print("[deluge-init] Web UI password configured from .env (login user: admin, not DELUGE_USERNAME)")
PY

if [[ -d /run/service/svc-deluge-web ]]; then
  s6-svc -u /run/service/svc-deluge-web 2>/dev/null || true
fi
