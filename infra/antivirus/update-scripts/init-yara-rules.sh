#!/bin/sh
# Initial setup script to clone YARA rules repository on first run
# This runs once when the container starts if YARA rules don't exist

YARA_RULES_PATH="/yara-rules"
YARA_REPO_URL="https://github.com/Yara-Rules/rules.git"
YARA_REPO_BRANCH="master"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Install git if not available
if ! command -v git &> /dev/null; then
    log "Installing git for YARA rules..."
    apk add --no-cache --quiet git > /dev/null 2>&1
fi

# Clone YARA rules if directory is empty or doesn't exist
if [ ! -d "$YARA_RULES_PATH" ] || [ -z "$(ls -A $YARA_RULES_PATH 2>/dev/null)" ]; then
    log "Initializing YARA rules from GitHub repository..."
    if git clone --depth 1 --branch "$YARA_REPO_BRANCH" "$YARA_REPO_URL" "$YARA_RULES_PATH" 2>&1; then
        RULE_COUNT=$(find "$YARA_RULES_PATH" -name "*.yar" -o -name "*.yara" 2>/dev/null | wc -l)
        log "YARA rules initialized successfully: $RULE_COUNT rules loaded"
    else
        log "Warning: Failed to initialize YARA rules from GitHub"
        # Create empty directory so the service can still start
        mkdir -p "$YARA_RULES_PATH"
    fi
elif [ ! -d "$YARA_RULES_PATH/.git" ]; then
    # Directory exists but is not a git repo, initialize it
    log "Converting existing YARA rules directory to git repository..."
    cd "$YARA_RULES_PATH" || exit 0
    # Backup existing files
    if [ "$(ls -A .)" ]; then
        mkdir -p ../yara-rules-backup
        cp -r . ../yara-rules-backup/
    fi
    # Initialize git and add remote
    git init
    git remote add origin "$YARA_REPO_URL"
    git fetch origin
    git checkout -b "$YARA_REPO_BRANCH" origin/"$YARA_REPO_BRANCH" || git checkout -b "$YARA_REPO_BRANCH"
    log "YARA rules directory converted to git repository"
fi

