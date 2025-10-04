@echo off
REM NutriGraph Docker Build Script
REM Simple batch version for Windows

echo ======================================
echo   NutriGraph Docker Build
echo ======================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    exit /b 1
)

REM Check for .env file
if not exist "prototypes\.env" (
    echo ERROR: Missing prototypes\.env file!
    echo Please create prototypes\.env with your GOOGLE_API_KEY
    exit /b 1
)

echo Stopping existing containers...
docker-compose down 2>nul

echo.
echo Building backend image...
docker-compose build backend
if errorlevel 1 (
    echo ERROR: Backend build failed!
    exit /b 1
)

echo.
echo Building frontend image...
docker-compose build frontend
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    exit /b 1
)

echo.
echo Starting containers...
docker-compose up -d

echo.
echo ======================================
echo   Build Complete!
echo ======================================
echo.
echo Frontend: http://localhost:8501
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To view logs:  docker-compose logs -f
echo To stop:       docker-compose down
echo.

docker-compose ps
