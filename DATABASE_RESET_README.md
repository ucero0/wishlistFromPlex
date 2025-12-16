# Database Reset Guide

This guide will help you completely reset your PostgreSQL database and Alembic migrations to start from scratch.

## What Was Done

✅ **All Alembic migration files have been deleted** from `services/fastapi-app/migrations/alembic/versions/`

## Steps to Reset Everything

### Option 1: Using the Provided Scripts (Recommended)

#### For Windows (PowerShell):
```powershell
# Step 1: Reset the database (removes postgres-data and recreates it)
.\reset-database.ps1

# Step 2: Create a fresh initial migration
.\reinitialize-alembic.ps1

# Step 3: Apply the migration (or restart your FastAPI container)
cd services/fastapi-app/migrations
alembic upgrade head
```

#### For Linux/Mac:
```bash
# Step 1: Reset the database (removes postgres-data and recreates it)
./reset-database.sh

# Step 2: Create a fresh initial migration
./reinitialize-alembic.sh

# Step 3: Apply the migration (or restart your FastAPI container)
cd services/fastapi-app/migrations
alembic upgrade head
```

### Option 2: Manual Steps

1. **Stop and remove the database:**
   ```bash
   docker-compose stop db
   # Remove the postgres-data directory
   rm -rf ./postgres-data  # Linux/Mac
   # or
   Remove-Item -Recurse -Force .\postgres-data  # Windows PowerShell
   ```

2. **Start the database container (creates fresh database):**
   ```bash
   docker-compose up -d db
   # Wait for it to be healthy (check with: docker ps)
   ```

3. **Create a fresh initial migration:**
   ```bash
   cd services/fastapi-app/migrations
   alembic revision --autogenerate -m "initial_schema"
   ```

4. **Apply the migration:**
   ```bash
   alembic upgrade head
   # Or simply restart your FastAPI container - it will run migrations automatically
   ```

## Important Notes

- **All existing data will be lost** when you remove the `postgres-data` directory
- The `alembic_version` table in the database will be automatically recreated when you run the first migration
- If you're using Docker Compose, the FastAPI container's entrypoint script will automatically run migrations on startup
- Make sure your database container is running before creating migrations

## Troubleshooting

### If migrations fail:
- Ensure the database container is healthy: `docker ps`
- Check database connection: `docker exec -it plex-wishlist-db psql -U plex_wishlist_user -d plex_wishlist`
- Verify your `DATABASE_URL` environment variable is correct

### If you see "Target database is not up to date":
- This means there are existing migrations. Since we deleted all migration files, you need to:
  1. Drop the `alembic_version` table: `DROP TABLE alembic_version;`
  2. Or reset the database completely using the scripts above



