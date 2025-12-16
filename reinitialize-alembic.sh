#!/bin/bash
# Reinitialize Alembic Script for Linux/Mac
# This script will create a fresh initial migration from your current models

set -e

echo "=== Alembic Reinitialization Script ==="
echo ""

# Check if we're in the right directory
if [ ! -f "./services/fastapi-app/migrations/alembic.ini" ]; then
    echo "ERROR: Please run this script from the project root directory"
    exit 1
fi

# Check if Docker is running
echo "Checking Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo "ERROR: Docker is not running or not accessible"
    exit 1
fi
echo "Docker is running"

# Check if database container is running
echo ""
echo "Checking database container..."
if ! docker ps --format "{{.Names}}" | grep -q "plex-wishlist-db"; then
    echo "ERROR: Database container is not running. Please start it first with: docker-compose up -d db"
    exit 1
fi
echo "Database container is running"

# Navigate to migrations directory
cd services/fastapi-app/migrations

echo ""
echo "Creating initial migration from current models..."

# Create initial migration
alembic revision --autogenerate -m "initial_schema"

if [ $? -eq 0 ]; then
    echo ""
    echo "Initial migration created successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review the migration file in: services/fastapi-app/migrations/alembic/versions/"
    echo "2. Apply the migration with: cd services/fastapi-app/migrations && alembic upgrade head"
    echo "   Or restart your FastAPI container to apply migrations automatically"
else
    echo ""
    echo "ERROR: Failed to create migration"
    exit 1
fi

echo ""
echo "=== Alembic Reinitialization Complete ==="



