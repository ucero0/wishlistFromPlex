#!/bin/bash
# Script called by Deluge Execute plugin when a torrent completes
# Arguments passed by Deluge:
#   $1 - Torrent ID (hash)
#   $2 - Torrent name
#   $3 - Torrent save path

TORRENT_HASH="$1"
TORRENT_NAME="$2"
TORRENT_PATH="$3"

# FastAPI service URL (adjust if running in different network)
# Default to plex-wishlist-api container if SCANFORVIRUS_API_URL is not set
API_URL="${SCANFORVIRUS_API_URL:-http://fastapi:8000/antivirus/scan/torrent}"
API_KEY="${API_KEY:-}"

# Log file
LOG_FILE="/config/scanner.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Torrent completed: $TORRENT_NAME (hash: $TORRENT_HASH)"
log "Save path: $TORRENT_PATH"

# Wait a moment for files to be fully written
sleep 5

# Call the scanner API
HTTP_CODE=0
if [ -n "$API_KEY" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "{\"torrent_hash\": \"$TORRENT_HASH\"}" \
        "$API_URL")
else
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "{\"torrent_hash\": \"$TORRENT_HASH\"}" \
        "$API_URL")
fi

# Extract HTTP status code (last line) and response body
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

log "Scanner API URL: $API_URL"
log "HTTP Status Code: $HTTP_CODE"
log "Scanner response: $RESPONSE_BODY"

# Check HTTP status code
if [ "$HTTP_CODE" != "200" ]; then
    log "ERROR: API call failed with HTTP status $HTTP_CODE"
    exit 1
fi

# Check if scan was successful
STATUS=$(echo "$RESPONSE_BODY" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$STATUS" = "clean" ]; then
    log "Scan passed - file organized successfully"
elif [ "$STATUS" = "infected" ]; then
    log "WARNING: Threat detected - torrent and files deleted!"
elif [ "$STATUS" = "error" ]; then
    log "ERROR: Scan failed - $RESPONSE_BODY"
    exit 1
else
    log "ERROR: Unknown scan status: $STATUS"
    exit 1
fi

