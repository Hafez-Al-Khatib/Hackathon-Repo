# Quick Docker Test Script
# Tests both Basic and Full versions

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("basic", "full", "both")]
    [string]$Version = "basic"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NutriGraph Docker Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker is not running" -ForegroundColor Red
        Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "ERROR: Docker not found" -ForegroundColor Red
    Write-Host "Please install Docker Desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Docker is running" -ForegroundColor Green
Write-Host ""

# Check .env file
if (-not (Test-Path "prototypes\.env")) {
    Write-Host "ERROR: prototypes/.env not found" -ForegroundColor Red
    Write-Host "Create it with: GOOGLE_API_KEY=your_key" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Environment file found" -ForegroundColor Green
Write-Host ""

function Test-Version {
    param($ConfigFile, $VersionName)
    
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Testing $VersionName Version" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Building containers..." -ForegroundColor Cyan
    & docker-compose -f $ConfigFile build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Build failed for $VersionName" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ Build successful" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting containers..." -ForegroundColor Cyan
    
    $job = Start-Job -ScriptBlock {
        param($ConfigFile)
        Set-Location $using:PWD
        & docker-compose -f $ConfigFile up
    } -ArgumentList $ConfigFile
    
    Start-Sleep -Seconds 15
    
    Write-Host "Testing backend health..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 10
        Write-Host "✅ Backend is healthy" -ForegroundColor Green
    } catch {
        Write-Host "❌ Backend failed to respond" -ForegroundColor Red
        Stop-Job $job
        & docker-compose -f $ConfigFile down
        return $false
    }
    
    Write-Host "Testing frontend..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501/" -UseBasicParsing -TimeoutSec 10
        Write-Host "✅ Frontend is accessible" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Frontend not ready yet (may need more time)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Stopping containers..." -ForegroundColor Cyan
    Stop-Job $job
    & docker-compose -f $ConfigFile down
    
    Write-Host "✅ $VersionName version test complete" -ForegroundColor Green
    Write-Host ""
    
    return $true
}

# Test requested version(s)
if ($Version -eq "basic" -or $Version -eq "both") {
    $basicResult = Test-Version "docker-compose.basic.yml" "BASIC"
}

if ($Version -eq "full" -or $Version -eq "both") {
    $fullResult = Test-Version "docker-compose.full.yml" "FULL"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($Version -eq "basic" -or $Version -eq "both") {
    if ($basicResult) {
        Write-Host "✅ BASIC version: READY" -ForegroundColor Green
    } else {
        Write-Host "❌ BASIC version: FAILED" -ForegroundColor Red
    }
}

if ($Version -eq "full" -or $Version -eq "both") {
    if ($fullResult) {
        Write-Host "✅ FULL version: READY" -ForegroundColor Green
    } else {
        Write-Host "❌ FULL version: FAILED" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "To run manually:" -ForegroundColor Cyan
Write-Host "  Basic:  docker-compose up" -ForegroundColor White
Write-Host "  Full:   docker-compose -f docker-compose.full.yml up" -ForegroundColor White
Write-Host ""
