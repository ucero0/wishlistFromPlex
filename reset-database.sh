#!/bin/bash
# Reset Database Script for Linux/Mac
# This script will:
# 1. Stop the database container
# 2. Remove the postgres-data volume
# 3. Restart the database container

set -e

echo "=== Database Reset Script ==="
echo ""

# Check if Docker is running
echo "Checking Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo "ERROR: Docker is not running or not accessible"
    exit 1
fi
echo "Docker is running"

# Stop the database container
echo ""
echo "Stopping database container..."
docker-compose stop db

# Remove the postgres-data directory
echo ""
echo "Removing postgres-data directory..."
if [ -d "./postgres-data" ]; then
    rm -rf ./postgres-data
    echo "postgres-data directory removed"
else
    echo "postgres-data directory not found (already removed or never created)"
fi

# Start the database container (this will recreate the database)
echo ""
echo "Starting database container (this will create a fresh database)..."
docker-compose up -d db

echo ""
echo "Waiting for database to be ready..."
sleep 5

# Wait for database to be healthy
MAX_RETRIES=30
RETRY_COUNT=0
DB_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$DB_READY" = false ]; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' plex-wishlist-db 2>/dev/null || echo "starting")
    if [ "$HEALTH" = "healthy" ]; then
        DB_READY=true
        echo "Database is ready!"
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Waiting for database... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ "$DB_READY" = false ]; then
    echo "WARNING: Database may not be fully ready. Please check manually."
fi

echo ""
echo "=== Database Reset Complete ==="
echo ""
echo "Next steps:"
echo "1. Run the reinitialize-alembic script to create a fresh initial migration"
echo "2. Or run: cd services/fastapi-app/migrations && alembic revision --autogenerate -m 'initial_schema'"









