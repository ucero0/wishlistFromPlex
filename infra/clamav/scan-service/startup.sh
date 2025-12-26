#!/bin/sh
# Startup script for ClamAV container with HTTP scan service
# This script runs after dependencies are installed and before ClamAV services start

# Make scripts executable
chmod +x /update-scripts/*.sh 2>/dev/null || true
chmod +x /scan-service/*.sh 2>/dev/null || true
chmod +x /scan-service/*.py 2>/dev/null || true

# Install Python 3 if not available
if ! command -v python3 &> /dev/null; then
    apk add --no-cache --quiet python3 py3-pip > /dev/null 2>&1
fi

# Install YARA if not available
if ! command -v yara &> /dev/null; then
    apk add --no-cache --quiet yara yara-dev > /dev/null 2>&1 || echo "Warning: YARA installation failed"
fi

# Initialize YARA rules from GitHub on first run
/update-scripts/init-yara-rules.sh

# Setup cron for daily updates (runs in background)
/update-scripts/setup-cron.sh &

# Create log directory
mkdir -p /var/log

# Start HTTP scanning service (runs in background)
# Output goes to stderr (which docker-compose captures) and also append to log file
# Use unbuffered Python for real-time output
(python3 -u /scan-service/http_scan_server.py 2>&1 | tee -a /var/log/scan-service.log) &

# Wait a moment for services to start
sleep 2

# Now start ClamAV services using the default /init script
# The /init script will handle freshclam and clamd based on environment variables
exec /init "$@"

