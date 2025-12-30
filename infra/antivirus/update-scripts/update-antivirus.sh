#!/bin/sh
# Script to update ClamAV virus definitions and YARA rules
# This script runs daily via cron at 2 AM

LOG_FILE="/var/log/clamav-updates.log"
YARA_RULES_PATH="/yara-rules"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting antivirus updates..."

# Update ClamAV virus definitions
log "Updating ClamAV virus definitions..."
if freshclam --log="$LOG_FILE"; then
    log "ClamAV virus definitions updated successfully"
    # Reload ClamAV daemon to use new definitions
    pkill -USR2 clamd || log "Warning: Could not reload ClamAV daemon"
else
    log "Error: Failed to update ClamAV virus definitions"
fi

# Update YARA rules from GitHub repository
log "Updating YARA rules from GitHub..."
YARA_REPO_URL="https://github.com/Yara-Rules/rules.git"
YARA_REPO_BRANCH="master"

# Install git if not available
if ! command -v git &> /dev/null; then
    log "Installing git..."
    apk add --no-cache --quiet git > /dev/null 2>&1
fi

# Update or clone YARA rules repository
if [ -d "$YARA_RULES_PATH/.git" ]; then
    # Repository exists, pull latest updates
    cd "$YARA_RULES_PATH" || exit 1
    log "Pulling latest YARA rules from GitHub..."
    if git fetch origin >> "$LOG_FILE" 2>&1 && git reset --hard origin/$YARA_REPO_BRANCH >> "$LOG_FILE" 2>&1; then
        log "YARA rules updated successfully from GitHub repository"
        # Count updated rules
        RULE_COUNT=$(find "$YARA_RULES_PATH" -name "*.yar" -o -name "*.yara" 2>/dev/null | wc -l)
        log "Total YARA rules available: $RULE_COUNT"
    else
        log "Warning: Failed to update YARA rules from GitHub"
    fi
else
    # Repository doesn't exist, clone it
    log "Cloning YARA rules repository from GitHub..."
    if [ -d "$YARA_RULES_PATH" ] && [ "$(ls -A $YARA_RULES_PATH)" ]; then
        # Directory exists but is not a git repo, backup and clone
        log "Backing up existing rules and cloning repository..."
        mv "$YARA_RULES_PATH" "${YARA_RULES_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    if git clone --depth 1 --branch "$YARA_REPO_BRANCH" "$YARA_REPO_URL" "$YARA_RULES_PATH" >> "$LOG_FILE" 2>&1; then
        log "YARA rules repository cloned successfully"
        RULE_COUNT=$(find "$YARA_RULES_PATH" -name "*.yar" -o -name "*.yara" 2>/dev/null | wc -l)
        log "Total YARA rules available: $RULE_COUNT"
    else
        log "Error: Failed to clone YARA rules repository from GitHub"
        # Restore backup if clone failed
        if [ -d "${YARA_RULES_PATH}.backup."* ]; then
            log "Restoring backup..."
            mv "${YARA_RULES_PATH}.backup."* "$YARA_RULES_PATH"
        fi
    fi
fi

log "Antivirus updates completed"

