#!/bin/sh
# Monitor gluetun health and restart if unhealthy
# This script monitors Docker health events and restarts gluetun when it becomes unhealthy

CONTAINER_NAME="gluetun"
CHECK_INTERVAL=30  # Check every 30 seconds
UNHEALTHY_COUNT=0
UNHEALTHY_THRESHOLD=3  # Restart after 3 consecutive unhealthy checks

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

check_health() {
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null)
    if [ "$?" -ne 0 ]; then
        log "ERROR: Could not check health of container $CONTAINER_NAME"
        return 1
    fi
    
    if [ "$HEALTH" = "unhealthy" ]; then
        UNHEALTHY_COUNT=$((UNHEALTHY_COUNT + 1))
        log "WARNING: $CONTAINER_NAME is unhealthy (count: $UNHEALTHY_COUNT/$UNHEALTHY_THRESHOLD)"
        
        if [ "$UNHEALTHY_COUNT" -ge "$UNHEALTHY_THRESHOLD" ]; then
            log "Container $CONTAINER_NAME has been unhealthy for $UNHEALTHY_COUNT checks. Restarting..."
            docker restart "$CONTAINER_NAME"
            if [ "$?" -eq 0 ]; then
                log "Successfully restarted $CONTAINER_NAME"
                UNHEALTHY_COUNT=0
            else
                log "ERROR: Failed to restart $CONTAINER_NAME"
            fi
        fi
    else
        if [ "$UNHEALTHY_COUNT" -gt 0 ]; then
            log "Container $CONTAINER_NAME is now healthy again"
            UNHEALTHY_COUNT=0
        fi
    fi
}

log "Starting gluetun health monitor (checking every ${CHECK_INTERVAL}s)"
log "Container: $CONTAINER_NAME"
log "Unhealthy threshold: $UNHEALTHY_THRESHOLD consecutive checks"

while true; do
    check_health
    sleep "$CHECK_INTERVAL"
done
