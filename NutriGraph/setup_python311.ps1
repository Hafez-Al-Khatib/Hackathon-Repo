# Setup script for Python 3.11 with full embedding support

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NutriGraph Python 3.11 Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.11 is available
$python311 = Get-Command "py" -ErrorAction SilentlyContinue

if (-not $python311) {
    Write-Host "ERROR: Python launcher not found" -ForegroundColor Red
    Write-Host "Please install Python 3.11 from python.org" -ForegroundColor Yellow
    exit 1
}

# Check Python 3.11 version
$version = & py -3.11 --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python 3.11 not found" -ForegroundColor Red
    Write-Host "Please install Python 3.11 from python.org" -ForegroundColor Yellow
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Cyan
    exit 1
}

Write-Host "Found: $version" -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "Creating Python 3.11 virtual environment..." -ForegroundColor Cyan
& py -3.11 -m venv venv311

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "Virtual environment created!" -ForegroundColor Green
Write-Host ""

# Activate and install packages
Write-Host "Installing packages (this may take a few minutes)..." -ForegroundColor Cyan
& .\venv311\Scripts\python.exe -m pip install --upgrade pip
& .\venv311\Scripts\pip.exe install -r backend\requirements.txt
& .\venv311\Scripts\pip.exe install gensim==4.3.2 node2vec==0.4.6

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To use Python 3.11 with embeddings:" -ForegroundColor Cyan
    Write-Host "1. Activate: .\venv311\Scripts\Activate" -ForegroundColor Yellow
    Write-Host "2. Run backend: python backend\main.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Embeddings will be ENABLED with Python 3.11!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ERROR: Package installation failed" -ForegroundColor Red
    Write-Host "Check your internet connection and try again" -ForegroundColor Yellow
}
