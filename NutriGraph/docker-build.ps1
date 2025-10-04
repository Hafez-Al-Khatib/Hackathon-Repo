# NutriGraph Docker Build & Deploy Script
# Complete dockerization with health checks and validation

param(
    [switch]$NoBuild,
    [switch]$Clean,
    [switch]$Logs,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  NutriGraph Docker Manager" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
function Test-DockerRunning {
    try {
        docker info > $null 2>&1
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-DockerRunning)) {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check for .env file
if (-not (Test-Path "prototypes\.env")) {
    Write-Host "❌ Missing prototypes\.env file!" -ForegroundColor Red
    Write-Host "Please create prototypes\.env with your GOOGLE_API_KEY" -ForegroundColor Yellow
    exit 1
}

# Stop containers
if ($Stop) {
    Write-Host "🛑 Stopping NutriGraph containers..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Containers stopped" -ForegroundColor Green
    exit 0
}

# Clean everything
if ($Clean) {
    Write-Host "🧹 Cleaning Docker resources..." -ForegroundColor Yellow
    docker-compose down -v --remove-orphans
    docker system prune -f
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
    exit 0
}

# Show logs
if ($Logs) {
    Write-Host "📋 Showing container logs..." -ForegroundColor Yellow
    docker-compose logs -f
    exit 0
}

# Build and deploy
Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan

if ($NoBuild) {
    Write-Host "⏩ Skipping build (using existing images)" -ForegroundColor Yellow
} else {
    # Stop existing containers
    Write-Host "Stopping existing containers..." -ForegroundColor Yellow
    docker-compose down 2>$null
    
    # Build images
    Write-Host "Building backend image..." -ForegroundColor Cyan
    docker-compose build backend
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Backend build failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Building frontend image..." -ForegroundColor Cyan
    docker-compose build frontend
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Images built successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 Starting containers..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start containers!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow

# Wait for backend health check
$maxWait = 60
$waited = 0
$backendHealthy = $false

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    
    $backendStatus = docker inspect --format='{{.State.Health.Status}}' nutrigraph-backend 2>$null
    
    if ($backendStatus -eq "healthy") {
        $backendHealthy = $true
        Write-Host "✅ Backend is healthy!" -ForegroundColor Green
        break
    }
    
    Write-Host "⏳ Backend starting... ($waited/$maxWait seconds)" -ForegroundColor Yellow
}

if (-not $backendHealthy) {
    Write-Host "❌ Backend failed to become healthy!" -ForegroundColor Red
    Write-Host "Showing backend logs:" -ForegroundColor Yellow
    docker-compose logs backend
    exit 1
}

# Wait for frontend health check
$waited = 0
$frontendHealthy = $false

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    
    $frontendStatus = docker inspect --format='{{.State.Health.Status}}' nutrigraph-frontend 2>$null
    
    if ($frontendStatus -eq "healthy") {
        $frontendHealthy = $true
        Write-Host "✅ Frontend is healthy!" -ForegroundColor Green
        break
    }
    
    Write-Host "⏳ Frontend starting... ($waited/$maxWait seconds)" -ForegroundColor Yellow
}

if (-not $frontendHealthy) {
    Write-Host "⚠️ Frontend health check did not pass, but may still be running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  ✅ NutriGraph is Running!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Frontend: http://localhost:8501" -ForegroundColor Cyan
Write-Host "🔌 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs:    .\docker-build.ps1 -Logs" -ForegroundColor White
Write-Host "  Stop:         .\docker-build.ps1 -Stop" -ForegroundColor White
Write-Host "  Clean:        .\docker-build.ps1 -Clean" -ForegroundColor White
Write-Host "  Rebuild:      .\docker-build.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Container status:" -ForegroundColor Yellow
docker-compose ps
