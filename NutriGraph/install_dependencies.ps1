# Install all dependencies for NutriGraph
Write-Host "Installing NutriGraph Dependencies..." -ForegroundColor Cyan
Write-Host "=" * 60

# Core dependencies
Write-Host "`nInstalling core packages..." -ForegroundColor Yellow
pip install google-generativeai python-dotenv Pillow networkx pyvis matplotlib

# Backend dependencies
Write-Host "`nInstalling backend packages..." -ForegroundColor Yellow
pip install fastapi uvicorn python-multipart

# Frontend dependencies
Write-Host "`nInstalling frontend packages..." -ForegroundColor Yellow
pip install streamlit requests

Write-Host "`n" + "=" * 60
Write-Host "All dependencies installed!" -ForegroundColor Green
Write-Host "`nYou can now run:" -ForegroundColor Cyan
Write-Host "  Backend:  python backend\main.py"
Write-Host "  Frontend: streamlit run frontend\app.py"
