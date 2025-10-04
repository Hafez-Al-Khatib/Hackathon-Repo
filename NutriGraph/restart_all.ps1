# NutriGraph - Kill all processes and show restart commands

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "NUTRIGRAPH - COMPLETE RESTART" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

# Kill any Python processes (backend/frontend)
Write-Host "`nStopping all Python processes..." -ForegroundColor Yellow
try {
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✓ Python processes stopped" -ForegroundColor Green
} catch {
    Write-Host "✓ No Python processes running" -ForegroundColor Green
}

# Check port 8000
Write-Host "`nChecking port 8000..." -ForegroundColor Yellow
$port8000 = netstat -ano | Select-String ":8000" | Select-String "LISTENING"
if ($port8000) {
    Write-Host "⚠ Port 8000 still in use" -ForegroundColor Red
    $processId = ($port8000 -split '\s+')[-1]
    Write-Host "  Killing process $processId..." -ForegroundColor Yellow
    taskkill /PID $processId /F
    Start-Sleep -Seconds 1
    Write-Host "✓ Port 8000 freed" -ForegroundColor Green
} else {
    Write-Host "✓ Port 8000 is free" -ForegroundColor Green
}

Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "READY TO START!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan

Write-Host "`nNow run these commands in SEPARATE terminals:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Terminal 1 (Backend):" -ForegroundColor Cyan
Write-Host "  cd c:\Users\Hafez\Desktop\NutriGraph" -ForegroundColor White
Write-Host "  python backend\main.py" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 (Frontend):" -ForegroundColor Cyan
Write-Host "  cd c:\Users\Hafez\Desktop\NutriGraph" -ForegroundColor White
Write-Host "  streamlit run frontend\app.py" -ForegroundColor White
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "After starting both:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:8501 in browser" -ForegroundColor White
Write-Host "2. Upload an image" -ForegroundColor White
Write-Host "3. Check FRONTEND terminal for FILE READ DEBUG logs" -ForegroundColor White
Write-Host "4. Click 'Analyze & Log Meal'" -ForegroundColor White
Write-Host "5. Check BOTH terminals for logs" -ForegroundColor White
Write-Host ""
Write-Host "Expected: File size should be > 0 in BOTH terminals!" -ForegroundColor Green
Write-Host ""
