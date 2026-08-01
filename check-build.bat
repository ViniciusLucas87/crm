@echo off
cd /d "C:\Users\vinic\OneDrive\Desktop\PacificNorthSystems\CRM System\apps\web"
call npm run build 2>&1
echo.
echo BUILD EXIT CODE: %ERRORLEVEL%
