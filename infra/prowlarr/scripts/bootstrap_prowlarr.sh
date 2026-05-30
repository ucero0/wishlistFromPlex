#!/usr/bin/with-contenv bash
# Idempotent Prowlarr bootstrap: indexers from seed.json (once); Deluge + FlareSolverr from compose env (every start).
set -euo pipefail

MARKER="/config/.prowlarr-bootstrap-v1.done"
SEED="${PROWLARR_BOOTSTRAP_SEED:-/bootstrap/seed.json}"
API="${PROWLARR_BOOTSTRAP_API:-http://127.0.0.1:9696/api/v1}"
API_KEY="${PROWLARR_API_KEY:-}"
DELUGE_PASS="${DELUGE_WEB_PASSWORD:-${DELUGE_PASSWORD:-}}"

# Connection settings: docker-compose prowlarr service env (not seed.json)
FLARE_URL="${FLARESOLVERR_URL:-${PROWLARR_BOOTSTRAP_FLARESOLVERR_URL:-http://127.0.0.1:8191}}"
FLARE_TIMEOUT="${FLARESOLVERR_REQUEST_TIMEOUT:-${PROWLARR_BOOTSTRAP_FLARESOLVERR_TIMEOUT:-60}}"
DELUGE_HOST="${PROWLARR_DELUGE_HOST:-${PROWLARR_BOOTSTRAP_DELUGE_HOST:-127.0.0.1}}"
DELUGE_PORT="${PROWLARR_DELUGE_WEB_PORT:-${PROWLARR_BOOTSTRAP_DELUGE_PORT:-8112}}"
DELUGE_CATEGORY="${PROWLARR_DELUGE_CATEGORY:-prowlarr}"
DELUGE_USE_SSL="${PROWLARR_DELUGE_USE_SSL:-false}"
DELUGE_ADD_PAUSED="${PROWLARR_DELUGE_ADD_PAUSED:-false}"

FORCE="${PROWLARR_BOOTSTRAP_FORCE:-false}"
SYNC_INDEXERS="false"

log() { echo "[prowlarr-bootstrap] $*"; }
warn() { echo "[prowlarr-bootstrap] WARNING: $*" >&2; }

if [[ -z "$API_KEY" ]]; then
  echo "[prowlarr-bootstrap] ERROR: PROWLARR_API_KEY is not set" >&2
  exit 1
fi

if [[ ! -f "$SEED" ]]; then
  echo "[prowlarr-bootstrap] ERROR: Seed file not found: $SEED" >&2
  exit 1
fi

if [[ ! -f "$MARKER" || "${FORCE,,}" == "true" || "$FORCE" == "1" ]]; then
  SYNC_INDEXERS="true"
fi

api() {
  curl -sS -f -H "X-Api-Key: ${API_KEY}" -H "Accept: application/json" "$@"
}

api_json() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  if [[ -n "$body" ]]; then
    curl -sS -f -X "$method" -H "X-Api-Key: ${API_KEY}" -H "Accept: application/json" \
      -H "Content-Type: application/json" -d "$body" "$url"
  else
    curl -sS -f -X "$method" -H "X-Api-Key: ${API_KEY}" -H "Accept: application/json" "$url"
  fi
}

wait_for_api() {
  local deadline=$((SECONDS + 180))
  while (( SECONDS < deadline )); do
    if api "${API}/system/status" >/dev/null 2>&1; then
      log "Prowlarr API is ready"
      return 0
    fi
    sleep 2
  done
  echo "[prowlarr-bootstrap] ERROR: Prowlarr API not ready after 180s" >&2
  exit 1
}

seed_or_env() {
  local env_value="$1"
  local jq_path="$2"
  if [[ -n "$env_value" ]]; then
    echo "$env_value"
  else
    jq -r "$jq_path" "$SEED"
  fi
}

ensure_tag() {
  local label="$1"
  local tag_id
  tag_id="$(api "${API}/tag" | jq -r --arg l "$label" 'first(.[] | select(.label == $l) | .id) // empty')"
  if [[ -n "$tag_id" && "$tag_id" != "null" ]]; then
    echo "$tag_id"
    return 0
  fi
  tag_id="$(api_json POST "${API}/tag" "{\"label\":\"${label}\"}" | jq -r '.id')"
  log "Created tag '${label}' (id=${tag_id})"
  echo "$tag_id"
}

ensure_flaresolverr() {
  local name="$1"
  local tag_id="$2"
  local host="${FLARE_URL%/}/"
  local existing_id
  existing_id="$(api "${API}/indexerProxy" | jq -r --arg n "$name" 'first(.[] | select(.name == $n) | .id) // empty')"
  local payload
  payload="$(api "${API}/indexerProxy/schema" | jq \
    --arg n "$name" \
    --arg h "$host" \
    --argjson t "$tag_id" \
    --argjson timeout "$FLARE_TIMEOUT" '
    .[] | select(.implementation == "FlareSolverr") |
    .name = $n |
    .tags = [$t] |
    .fields = (.fields | map(
      if .name == "host" then .value = $h
      elif .name == "requestTimeout" then .value = $timeout
      else . end))
  ')"
  if [[ -n "$existing_id" && "$existing_id" != "null" ]]; then
    payload="$(echo "$payload" | jq --argjson id "$existing_id" '. + {id: $id}')"
    api_json PUT "${API}/indexerProxy/${existing_id}" "$payload" >/dev/null
    log "Updated FlareSolverr proxy (host=${host}, timeout=${FLARE_TIMEOUT}s)"
  else
    api_json POST "${API}/indexerProxy" "$payload" >/dev/null
    log "Created FlareSolverr proxy (host=${host}, timeout=${FLARE_TIMEOUT}s)"
  fi
}

ensure_deluge() {
  local name="$1"
  if [[ -z "$DELUGE_PASS" ]]; then
    warn "DELUGE_WEB_PASSWORD / DELUGE_PASSWORD not set; Deluge client may fail auth"
  fi

  local deadline=$((SECONDS + 300))
  while (( SECONDS < deadline )); do
    local existing_id payload method url http_code
    existing_id="$(api "${API}/downloadclient" | jq -r --arg n "$name" 'first(.[] | select(.name == $n) | .id) // empty')"
    payload="$(api "${API}/downloadclient/schema" | jq \
      --arg n "$name" \
      --arg host "$DELUGE_HOST" \
      --argjson port "$DELUGE_PORT" \
      --arg pass "$DELUGE_PASS" \
      --arg category "$DELUGE_CATEGORY" \
      --argjson use_ssl "$DELUGE_USE_SSL" \
      --argjson add_paused "$DELUGE_ADD_PAUSED" '
      .[] | select(.implementation == "Deluge") |
      .enable = true |
      .name = $n |
      .fields = (.fields | map(
        if .name == "host" then .value = $host
        elif .name == "port" then .value = $port
        elif .name == "password" then .value = $pass
        elif .name == "category" then .value = $category
        elif .name == "useSsl" then .value = $use_ssl
        elif .name == "addPaused" then .value = $add_paused
        else . end))
    ')"

    if [[ -n "$existing_id" && "$existing_id" != "null" ]]; then
      payload="$(echo "$payload" | jq --argjson id "$existing_id" '. + {id: $id}')"
      method="PUT"
      url="${API}/downloadclient/${existing_id}?forceSave=true"
    else
      method="POST"
      url="${API}/downloadclient?forceSave=true"
    fi

    http_code="$(curl -sS -o /dev/null -w "%{http_code}" -X "$method" \
      -H "X-Api-Key: ${API_KEY}" -H "Accept: application/json" \
      -H "Content-Type: application/json" -d "$payload" "$url")"
    if [[ "$http_code" =~ ^(200|201|202)$ ]]; then
      if [[ "$method" == "PUT" ]]; then
        log "Updated Deluge download client (${DELUGE_HOST}:${DELUGE_PORT}, category=${DELUGE_CATEGORY})"
      else
        log "Created Deluge download client (${DELUGE_HOST}:${DELUGE_PORT}, category=${DELUGE_CATEGORY})"
      fi
      return 0
    fi

    warn "Deluge download client not ready (HTTP ${http_code}); waiting for Deluge Web UI..."
    sleep 10
  done

  warn "Could not configure Deluge download client after 300s — check DELUGE_PASSWORD and restart deluge + prowlarr"
  return 1
}

ensure_indexers() {
  local tag_id="$1"
  local count
  count="$(jq '.indexers | length' "$SEED")"
  local i
  for ((i = 0; i < count; i++)); do
    local spec name definition use_flare priority extra
    spec="$(jq -c ".indexers[$i]" "$SEED")"
    name="$(echo "$spec" | jq -r '.name')"
    definition="$(echo "$spec" | jq -r '.definition')"
    use_flare="$(echo "$spec" | jq -r '.flaresolverr // false')"
    priority="$(echo "$spec" | jq -r '.priority // 25')"
    extra="$(echo "$spec" | jq -c '.extraFields // {}')"

    if api "${API}/indexer" | jq -e --arg n "$name" 'any(.[]; .name == $n)' >/dev/null; then
      log "Indexer '${name}' already exists — skipping"
      continue
    fi

    local schema payload
    schema="$(api "${API}/indexer/schema" | jq --arg d "$definition" '.[] | select(.definitionName == $d)')"
    if [[ -z "$schema" || "$schema" == "null" ]]; then
      warn "Definition '${definition}' not found — skipping '${name}'"
      continue
    fi

    payload="$(echo "$schema" | jq \
      --arg n "$name" \
      --argjson priority "$priority" \
      --argjson use_flare "$use_flare" \
      --argjson tag_id "$tag_id" \
      --argjson extra "$extra" '
      .name = $n |
      .enable = true |
      .priority = $priority |
      .appProfileId = (if .appProfileId == 0 then 1 else .appProfileId end) |
      .tags = (if $use_flare then [$tag_id] else [] end) |
      reduce ($extra | to_entries[]) as $e (.;
        .fields = (.fields | map(if .name == $e.key then .value = $e.value else . end))
      )
    ')"

    api_json POST "${API}/indexer?forceSave=true" "$payload" >/dev/null
    log "Created indexer '${name}' (${definition})"
  done
}

wait_for_api

TAG_LABEL="$(seed_or_env "${PROWLARR_FLARESOLVERR_TAG:-}" '.tag.label')"
FLARE_NAME="$(seed_or_env "${PROWLARR_FLARESOLVERR_NAME:-}" '.flaresolverr.name')"
DELUGE_NAME="$(seed_or_env "${PROWLARR_DELUGE_CLIENT_NAME:-}" '.deluge.name')"

TAG_ID="$(ensure_tag "$TAG_LABEL")"
ensure_flaresolverr "$FLARE_NAME" "$TAG_ID"

if [[ "$SYNC_INDEXERS" == "true" ]]; then
  ensure_indexers "$TAG_ID"
  touch "$MARKER"
  log "Indexer bootstrap completed (marker written)"
else
  log "Indexers skipped (already bootstrapped); Deluge and FlareSolverr synced from docker-compose env"
fi

ensure_deluge "$DELUGE_NAME" || true

log "Bootstrap completed successfully"
