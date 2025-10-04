# Start NutriGraph Frontend
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Starting NutriGraph Frontend UI" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if in correct directory
if (!(Test-Path "frontend\app.py")) {
    Write-Host "Error: Please run this script from the NutriGraph root directory" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (!(Test-Path "frontend\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv frontend\venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& frontend\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -q -r frontend\requirements.txt

# Start Streamlit
Write-Host ""
Write-Host "Starting Streamlit app..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "Make sure the backend is running first!" -ForegroundColor Yellow
Write-Host ""

streamlit run frontend\app.py
