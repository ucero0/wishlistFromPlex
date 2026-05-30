#!/bin/sh
# Wrapper entrypoint that monitors gluetun health and exits container when unhealthy
# This allows Docker's restart policy to restart the container without a separate service

# Start health monitor in background
sh /health-monitor-wrapper.sh &

# Store monitor PID
MONITOR_PID=$!

# Function to cleanup and exit
cleanup() {
    kill $MONITOR_PID 2>/dev/null
    exit 1
}

# Trap signals to cleanup
trap cleanup TERM INT

# Execute gluetun's original entrypoint
exec /gluetun-entrypoint "$@"
