@echo off
set DOCKER_BUILDKIT=0
docker compose build --no-cache api
docker compose up -d --force-recreate api
