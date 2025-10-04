# Quick start script for NutriGraph

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NutriGraph Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path "prototypes\.env")) {
    Write-Host "ERROR: prototypes/.env not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Create prototypes/.env with:" -ForegroundColor Yellow
    Write-Host "GOOGLE_API_KEY=your_key_here" -ForegroundColor White
    Write-Host ""
    Write-Host "Get a key from: https://makersuite.google.com/app/apikey" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Environment file found" -ForegroundColor Green
Write-Host ""

# Check if port 8000 is in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  Port 8000 already in use" -ForegroundColor Yellow
    Write-Host "Stopping existing backend..." -ForegroundColor Yellow
    Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
}

Write-Host "Starting NutriGraph..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend will start on: http://localhost:8000" -ForegroundColor White
Write-Host "Frontend will start on: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host ""

# Start backend in background
$backend = Start-Process python -ArgumentList "backend\main.py" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3

# Check if backend started
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend started successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend failed to start" -ForegroundColor Red
    Write-Host "Check for errors and try again" -ForegroundColor Yellow
    if ($backend) { Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }
    exit 1
}

Write-Host ""
Write-Host "Starting frontend..." -ForegroundColor Cyan
Write-Host ""

# Start frontend (blocking)
try {
    & streamlit run frontend\app.py
} finally {
    # Cleanup when frontend stops
    Write-Host ""
    Write-Host "Stopping backend..." -ForegroundColor Yellow
    if ($backend) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ All services stopped" -ForegroundColor Green
}
