#!/bin/sh
set -e

echo "=== Docker Entrypoint Starting ==="

echo "Waiting for PostgreSQL to be ready..."

DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_PORT=${DB_PORT:-5432}

echo "Connecting to $DB_HOST:$DB_PORT"

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
echo "=== Running Alembic migrations ==="
alembic upgrade head
echo "=== Starting application ==="
exec "$@"
