#!/usr/bin/with-contenv bash
# Ensure RPC user from env exists in Deluge auth (format: user:password:level, plain password).
set -euo pipefail

USERNAME="${DELUGE_USERNAME:-deluge}"
PASSWORD="${DELUGE_PASSWORD:-deluge}"
AUTH_FILE="/config/auth"
LEVEL="${DELUGE_AUTH_LEVEL:-10}"

if [[ ! -f "${AUTH_FILE}" ]]; then
  echo "[deluge-init] ${AUTH_FILE} not found yet, skipping API user setup"
  exit 0
fi

if grep -q "^${USERNAME}:" "${AUTH_FILE}"; then
  echo "[deluge-init] Deluge RPC user '${USERNAME}' already present in auth"
  exit 0
fi

echo "${USERNAME}:${PASSWORD}:${LEVEL}" >> "${AUTH_FILE}"
echo "[deluge-init] Added Deluge RPC user '${USERNAME}' for remote API access"
