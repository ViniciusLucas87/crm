@echo off
cd /d "c:\Users\vinic\OneDrive\Desktop\PacificNorthSystems\CRM System"
"C:\Program Files\Docker\Docker\resources\bin\docker.exe" compose build web
echo BUILD_EXIT_CODE=%ERRORLEVEL%
