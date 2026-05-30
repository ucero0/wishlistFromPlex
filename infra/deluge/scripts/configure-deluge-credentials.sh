#!/usr/bin/with-contenv bash
# Apply Deluge RPC + Web UI credentials from .env after the Deluge daemon has started.
set -euo pipefail

python3 <<'PY'
import hashlib
import os
import re
import secrets
import sys
import time
from pathlib import Path

USERNAME = os.environ.get("DELUGE_USERNAME", "deluge").strip()
PASSWORD = os.environ.get("DELUGE_PASSWORD", "").strip()
WEB_PASSWORD = os.environ.get("DELUGE_WEB_PASSWORD", PASSWORD).strip()
LEVEL = os.environ.get("DELUGE_AUTH_LEVEL", "10").strip()
FORCE_WEB = os.environ.get("DELUGE_FORCE_WEB_PASSWORD", "").lower() in ("1", "true", "yes")

AUTH_FILE = Path("/config/auth")
WEB_FILE = Path("/config/web.conf")
WEB_MARKER = Path("/config/.deluge-web-password-configured")
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

if WEB_PASSWORD in KNOWN_WEAK:
    warn("Web UI password not set (DELUGE_WEB_PASSWORD / DELUGE_PASSWORD). Skipping Web UI bootstrap.")
    raise SystemExit(0)

if WEB_MARKER.exists() and not FORCE_WEB:
    print("[deluge-init] Web UI password already bootstrapped (set DELUGE_FORCE_WEB_PASSWORD=true to overwrite)")
    raise SystemExit(0)

if not wait_for(WEB_FILE, attempts=30, delay=2.0):
    print("[deluge-init] /config/web.conf not ready yet; RPC is configured.")
    raise SystemExit(1)

salt = secrets.token_hex(20)
pwd_sha1 = hashlib.sha1((salt + WEB_PASSWORD).encode("utf-8")).hexdigest()
web_text = WEB_FILE.read_text(encoding="utf-8", errors="replace")
web_text = re.sub(r'"pwd_salt": "[^"]*"', f'"pwd_salt": "{salt}"', web_text, count=1)
web_text = re.sub(r'"pwd_sha1": "[^"]*"', f'"pwd_sha1": "{pwd_sha1}"', web_text, count=1)
web_text = re.sub(r'"first_login": true', '"first_login": false', web_text, count=1)
WEB_FILE.write_text(web_text, encoding="utf-8")
WEB_MARKER.write_text("bootstrapped-from-env\n", encoding="utf-8")
print("[deluge-init] Web UI password configured from .env (login: admin)")
PY
