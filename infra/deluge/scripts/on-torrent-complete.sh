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
API_URL="${SCANNER_API_URL:-http://fastapi:8000}"
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
if [ -n "$API_KEY" ]; then
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "{\"torrent_hash\": \"$TORRENT_HASH\"}" \
        "$API_URL/scanner/scan")
else
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"torrent_hash\": \"$TORRENT_HASH\"}" \
        "$API_URL/scanner/scan")
fi

log "Scanner response: $RESPONSE"

# Check if scan was successful
STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$STATUS" = "clean" ]; then
    log "Scan passed - file organized successfully"
elif [ "$STATUS" = "infected" ]; then
    log "WARNING: Threat detected - file quarantined!"
else
    log "ERROR: Scan status: $STATUS"
fi

