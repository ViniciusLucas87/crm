@echo off
echo === Sprint 47.6 Rebuild ===
cd /d "c:\Users\vinic\OneDrive\Desktop\PacificNorthSystems\CRM System"

echo.
echo [1/3] Building API...
docker compose build api --no-cache
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: API build failed
    pause
    exit /b 1
)

echo.
echo [2/3] Building Web...
docker compose build web --no-cache
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Web build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Deploying...
docker compose up -d --force-recreate api web

echo.
echo === Done ===
docker compose ps
pause
