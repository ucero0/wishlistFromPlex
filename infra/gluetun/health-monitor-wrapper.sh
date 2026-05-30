#!/bin/sh
# Wrapper script that monitors gluetun health and exits container when unhealthy
# This allows Docker's restart policy to restart the container

CONTAINER_NAME="gluetun"
CHECK_INTERVAL=30  # Check every 30 seconds
UNHEALTHY_COUNT=0
UNHEALTHY_THRESHOLD=3  # Exit after 3 consecutive unhealthy checks

log() {
    echo "[health-monitor] $(date +'%Y-%m-%d %H:%M:%S') $1" >&2
}

# Function to check if gluetun is healthy by checking tun0 interface
check_health() {
    # Check if OpenVPN process is running and tun0 has IP
    if pgrep openvpn > /dev/null 2>&1 && \
       test -d /proc/sys/net/ipv4/conf/tun0 && \
       ip addr show tun0 2>/dev/null | grep -q 'inet '; then
        return 0  # Healthy
    else
        return 1  # Unhealthy
    fi
}

# Start gluetun in background (it's already running, but we monitor it)
log "Starting health monitor for $CONTAINER_NAME"
log "Will exit container after $UNHEALTHY_THRESHOLD consecutive unhealthy checks"

while true; do
    if check_health; then
        # Reset counter when healthy
        if [ "$UNHEALTHY_COUNT" -gt 0 ]; then
            log "Container is healthy again (was unhealthy for $UNHEALTHY_COUNT checks)"
            UNHEALTHY_COUNT=0
        fi
    else
        UNHEALTHY_COUNT=$((UNHEALTHY_COUNT + 1))
        log "Container is unhealthy (count: $UNHEALTHY_COUNT/$UNHEALTHY_THRESHOLD)"
        
        if [ "$UNHEALTHY_COUNT" -ge "$UNHEALTHY_THRESHOLD" ]; then
            log "Container has been unhealthy for $UNHEALTHY_THRESHOLD checks. Exiting to trigger restart..."
            exit 1
        fi
    fi
    
    sleep "$CHECK_INTERVAL"
done
