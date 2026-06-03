#!/bin/sh
set -eu

if [ ! -S "${DOCKER_SOCK:-/var/run/docker.sock}" ]; then
  echo "[vpn-stack-sync] ERROR: Docker socket not mounted at ${DOCKER_SOCK:-/var/run/docker.sock}" >&2
  exit 1
fi

if [ ! -f "${COMPOSE_FILE:-/stack/docker-compose.yml}" ]; then
  echo "[vpn-stack-sync] ERROR: Compose file not found at ${COMPOSE_FILE:-/stack/docker-compose.yml}" >&2
  exit 1
fi

exec /usr/local/bin/sync-vpn-dependents watch
