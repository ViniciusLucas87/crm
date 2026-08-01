@echo off
cd /d "c:\Users\vinic\OneDrive\Desktop\PacificNorthSystems\CRM System"
docker compose build api --no-cache
docker compose up -d --force-recreate api
echo DONE
