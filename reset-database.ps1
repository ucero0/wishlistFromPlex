# Reset Database Script for Windows PowerShell
# This script will:
# 1. Stop the database container
# 2. Remove the postgres-data volume
# 3. Restart the database container

Write-Host "=== Database Reset Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not running or not accessible" -ForegroundColor Red
    exit 1
}

# Stop the database container
Write-Host ""
Write-Host "Stopping database container..." -ForegroundColor Yellow
docker-compose stop db

# Remove the postgres-data directory
Write-Host ""
Write-Host "Removing postgres-data directory..." -ForegroundColor Yellow
if (Test-Path ".\postgres-data") {
    Remove-Item -Recurse -Force ".\postgres-data"
    Write-Host "postgres-data directory removed" -ForegroundColor Green
} else {
    Write-Host "postgres-data directory not found (already removed or never created)" -ForegroundColor Yellow
}

# Start the database container (this will recreate the database)
Write-Host ""
Write-Host "Starting database container (this will create a fresh database)..." -ForegroundColor Yellow
docker-compose up -d db

Write-Host ""
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Wait for database to be healthy
$maxRetries = 30
$retryCount = 0
$dbReady = $false

while ($retryCount -lt $maxRetries -and -not $dbReady) {
    try {
        $health = docker inspect --format='{{.State.Health.Status}}' plex-wishlist-db 2>$null
        if ($health -eq "healthy") {
            $dbReady = $true
            Write-Host "Database is ready!" -ForegroundColor Green
        } else {
            $retryCount++
            Write-Host "Waiting for database... (attempt $retryCount/$maxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    } catch {
        $retryCount++
        Write-Host "Waiting for database... (attempt $retryCount/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $dbReady) {
    Write-Host "WARNING: Database may not be fully ready. Please check manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Database Reset Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run the reinitialize-alembic script to create a fresh initial migration" -ForegroundColor White
Write-Host "2. Or run: cd services/fastapi-app/migrations && alembic revision --autogenerate -m 'initial_schema'" -ForegroundColor White









