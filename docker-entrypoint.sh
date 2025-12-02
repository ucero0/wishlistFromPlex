#!/bin/bash
set -e

echo "=== Docker Entrypoint Starting ==="

echo "Waiting for PostgreSQL to be ready..."

# Extract host and port from DATABASE_URL
# Format: postgresql://user:pass@host:port/dbname
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

# Default port if not specified
DB_PORT=${DB_PORT:-5432}

echo "Connecting to $DB_HOST:$DB_PORT"

# Wait for PostgreSQL to accept connections (max 60 seconds)
MAX_RETRIES=30
RETRY_COUNT=0
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: PostgreSQL did not become ready in time"
        exit 1
    fi
    echo "PostgreSQL is unavailable - sleeping (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "PostgreSQL is ready!"

# Run Alembic migrations
echo "Running database migrations..."
if alembic upgrade head; then
    echo "Database migrations completed successfully"
else
    echo "WARNING: Alembic migrations failed. This might be okay for first-time setup."
    echo "SQLAlchemy will attempt to create tables on application startup."
fi

echo "=== Starting application ==="
exec "$@"

