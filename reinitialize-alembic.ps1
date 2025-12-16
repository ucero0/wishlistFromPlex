# Reinitialize Alembic Script for Windows PowerShell
# This script will create a fresh initial migration from your current models

Write-Host "=== Alembic Reinitialization Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path ".\services\fastapi-app\migrations\alembic.ini")) {
    Write-Host "ERROR: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not running or not accessible" -ForegroundColor Red
    exit 1
}

# Check if database container is running
Write-Host ""
Write-Host "Checking database container..." -ForegroundColor Yellow
$dbRunning = docker ps --filter "name=plex-wishlist-db" --format "{{.Names}}" | Select-String "plex-wishlist-db"
if (-not $dbRunning) {
    Write-Host "ERROR: Database container is not running. Please start it first with: docker-compose up -d db" -ForegroundColor Red
    exit 1
}
Write-Host "Database container is running" -ForegroundColor Green

# Navigate to migrations directory
$migrationsPath = ".\services\fastapi-app\migrations"
Push-Location $migrationsPath

try {
    Write-Host ""
    Write-Host "Creating initial migration from current models..." -ForegroundColor Yellow
    
    # Create initial migration
    alembic revision --autogenerate -m "initial_schema"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Initial migration created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Review the migration file in: services/fastapi-app/migrations/alembic/versions/" -ForegroundColor White
        Write-Host "2. Apply the migration with: cd services/fastapi-app/migrations && alembic upgrade head" -ForegroundColor White
        Write-Host "   Or restart your FastAPI container to apply migrations automatically" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "ERROR: Failed to create migration" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "=== Alembic Reinitialization Complete ===" -ForegroundColor Cyan



