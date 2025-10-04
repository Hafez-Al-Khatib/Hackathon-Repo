# Start NutriGraph Backend
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Starting NutriGraph Backend API" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if in correct directory
if (!(Test-Path "backend\main.py")) {
    Write-Host "Error: Please run this script from the NutriGraph root directory" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (!(Test-Path "backend\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv backend\venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& backend\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -q -r backend\requirements.txt

# Start server
Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API docs available at: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

python backend\main.py
