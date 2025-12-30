#!/bin/sh
# Setup cron job to run antivirus updates daily at 2 AM
# This script runs in the background and sets up the cron job

CRON_JOB="0 2 * * * /usr/local/bin/update-antivirus.sh >> /var/log/clamav-updates.log 2>&1"

# Create log directory if it doesn't exist
mkdir -p /var/log

# Install cron if not available (ClamAV image is based on Alpine)
if ! command -v crond &> /dev/null && ! command -v cron &> /dev/null; then
    echo "Installing cron..."
    apk add --no-cache --quiet dcron > /dev/null 2>&1
fi

# Copy update script to a location in PATH
cp /update-scripts/update-antivirus.sh /usr/local/bin/update-antivirus.sh
chmod +x /usr/local/bin/update-antivirus.sh

# Wait a moment for the system to be ready
sleep 5

# Add cron job if it doesn't exist
if ! crontab -l 2>/dev/null | grep -q "update-antivirus.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab - 2>/dev/null
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cron job added: Daily updates at 2 AM" >> /var/log/clamav-updates.log
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cron job already exists" >> /var/log/clamav-updates.log
fi

# Start cron daemon in background (non-blocking)
if command -v crond &> /dev/null; then
    crond -f -l 2 &
elif command -v cron &> /dev/null; then
    cron
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cron setup completed" >> /var/log/clamav-updates.log
