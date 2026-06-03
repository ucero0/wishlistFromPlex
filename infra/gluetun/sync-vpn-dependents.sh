#!/bin/sh
# Reconcile Deluge, Prowlarr, and FlareSolverr with the current Gluetun network namespace.
#
# Usage:
#   sync-vpn-dependents.sh once   # run one reconciliation pass
#   sync-vpn-dependents.sh watch  # listen for gluetun start events (vpn-stack-sync service)
#
# Requires: docker CLI with compose plugin, access to /var/run/docker.sock

set -eu

COMPOSE_DIR="${COMPOSE_PROJECT_DIR:-/stack}"
COMPOSE_FILE="${COMPOSE_FILE:-${COMPOSE_DIR}/docker-compose.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
GLUETUN="${GLUETUN_CONTAINER:-gluetun}"
DEPENDENTS="${VPN_DEPENDENTS:-deluge prowlarr flaresolverr}"
HEALTH_WAIT_SECONDS="${HEALTH_WAIT_SECONDS:-180}"
SETTLE_SECONDS="${SETTLE_SECONDS:-15}"
DEBOUNCE_SECONDS="${DEBOUNCE_SECONDS:-30}"
LOCK_FILE="${LOCK_FILE:-/tmp/vpn-stack-sync.lock}"
LAST_RUN_FILE="${LAST_RUN_FILE:-/tmp/vpn-stack-sync.last}"
LOG_PREFIX="${LOG_PREFIX:-[vpn-stack-sync]}"

log() {
  printf '%s %s %s\n' "$LOG_PREFIX" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
}

log_warn() {
  printf '%s %s WARNING: %s\n' "$LOG_PREFIX" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
}

container_exists() {
  docker inspect "$1" >/dev/null 2>&1
}

compose_project() {
  if [ -n "$COMPOSE_PROJECT_NAME" ]; then
    printf '%s' "$COMPOSE_PROJECT_NAME"
    return 0
  fi

  project="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$GLUETUN" 2>/dev/null || true)"
  if [ -n "$project" ] && [ "$project" != "<no value>" ]; then
    printf '%s' "$project"
    return 0
  fi

  log_warn "Could not detect compose project from gluetun labels; using directory basename"
  basename "$COMPOSE_DIR"
}

gluetun_id() {
  docker inspect -f '{{.Id}}' "$GLUETUN" 2>/dev/null || true
}

dependent_network_mode() {
  docker inspect -f '{{.HostConfig.NetworkMode}}' "$1" 2>/dev/null || true
}

gluetun_health_status() {
  docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$GLUETUN" 2>/dev/null || printf 'missing'
}

wait_for_gluetun_healthy() {
  deadline=$(( $(date +%s) + HEALTH_WAIT_SECONDS ))
  log "Waiting up to ${HEALTH_WAIT_SECONDS}s for ${GLUETUN} to become healthy..."

  while [ "$(date +%s)" -lt "$deadline" ]; do
    status="$(gluetun_health_status)"
    case "$status" in
      healthy)
        log "${GLUETUN} is healthy"
        return 0
        ;;
      unhealthy)
        log_warn "${GLUETUN} reported unhealthy; retrying..."
        ;;
      missing)
        log_warn "${GLUETUN} not found; retrying..."
        ;;
      *)
        log "${GLUETUN} status=${status}; waiting..."
        ;;
    esac
    sleep 5
  done

  log_warn "${GLUETUN} did not become healthy within ${HEALTH_WAIT_SECONDS}s"
  return 1
}

assess_dependents() {
  gid="$1"
  recreate=false

  for svc in $DEPENDENTS; do
    if ! container_exists "$svc"; then
      log_warn "${svc} is missing"
      recreate=true
      continue
    fi

    mode="$(dependent_network_mode "$svc")"
    case "$mode" in
      "container:${gid}")
        log "${svc} shares current ${GLUETUN} namespace"
        ;;
      *)
        log_warn "${svc} uses stale namespace (${mode}); recreate required"
        recreate=true
        ;;
    esac
  done

  if [ "$recreate" = true ]; then
    printf 'recreate'
  else
    printf 'restart'
  fi
}

recreate_dependents() {
  project="$(compose_project)"
  log "Recreating dependents: ${DEPENDENTS} (project=${project})"
  docker compose -p "$project" -f "$COMPOSE_FILE" up -d --force-recreate --no-deps $DEPENDENTS
  log "Recreate completed"
}

restart_dependents() {
  log "Restarting dependents to refresh VPN-side connections: ${DEPENDENTS}"
  # shellcheck disable=SC2086
  if docker restart -t 30 $DEPENDENTS >/dev/null; then
    log "Restart completed"
    return 0
  fi

  log_warn "Restart failed; falling back to recreate"
  recreate_dependents
}

sync_once() {
  (
    flock -x 9 || {
      log "Another sync is in progress; skipping"
      exit 0
    }

    if ! wait_for_gluetun_healthy; then
      exit 1
    fi

    if [ "$SETTLE_SECONDS" -gt 0 ]; then
      log "Settling ${SETTLE_SECONDS}s after ${GLUETUN} became healthy..."
      sleep "$SETTLE_SECONDS"
    fi

    gid="$(gluetun_id)"
    if [ -z "$gid" ]; then
      log_warn "Cannot read ${GLUETUN} container id"
      exit 1
    fi

    action="$(assess_dependents "$gid")"
    case "$action" in
      recreate) recreate_dependents ;;
      restart) restart_dependents ;;
      *) log_warn "Unknown action: ${action}"; exit 1 ;;
    esac
  ) 9>"$LOCK_FILE"
}

should_debounce() {
  [ -f "$LAST_RUN_FILE" ] || return 1
  last="$(cat "$LAST_RUN_FILE")"
  now="$(date +%s)"
  [ $((now - last)) -lt "$DEBOUNCE_SECONDS" ]
}

record_sync_run() {
  date +%s >"$LAST_RUN_FILE"
}

watch_gluetun_starts() {
  log "Watching docker events: container=${GLUETUN} event=start"

  sync_once || log_warn "Initial sync pass failed"
  record_sync_run

  docker events \
    --filter "container=${GLUETUN}" \
    --filter "event=start" \
    --format '{{.Time}}' |
  while read -r _; do
    if should_debounce; then
      log "Debouncing gluetun start event"
      continue
    fi
    record_sync_run
    log "Gluetun start event detected"
    sync_once || log_warn "Sync pass failed after gluetun start"
  done
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <once|watch>

  once   Run a single reconciliation pass.
  watch  Reconcile on startup and whenever ${GLUETUN} starts.
EOF
}

main() {
  cmd="${1:-watch}"
  case "$cmd" in
    once) sync_once ;;
    watch) watch_gluetun_starts ;;
    -h|--help|help) usage ;;
    *)
      log_warn "Unknown command: ${cmd}"
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
