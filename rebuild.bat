@echo off
echo ============================================
echo  Sprint 15 - Rebuild All Containers
echo ============================================
echo.

echo [1/4] Stopping containers...
docker compose down
echo.

echo [2/4] Building API (no cache)...
set DOCKER_BUILDKIT=0
docker compose build --no-cache api
echo.

echo [3/4] Building Web (no cache)...
set DOCKER_BUILDKIT=0
docker compose build --no-cache web
echo.

echo [4/4] Starting all services...
docker compose up -d
echo.

echo Waiting for containers to start...
timeout /t 10 /nobreak >nul

echo.
echo Running migration...
docker exec crmsystem-api-1 alembic upgrade head
echo.

echo ============================================
echo  Build complete! 
echo  API: http://localhost:8000
echo  Web: http://localhost:3000
echo ============================================
