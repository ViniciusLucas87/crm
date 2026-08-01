$ErrorActionPreference = "Continue"
$logFile = "C:\Users\vinic\rebuild-log.txt"
"=== Rebuild started at $(Get-Date) ===" | Out-File $logFile

Write-Host "Stopping containers..."
docker compose down 2>&1 | Out-File $logFile -Append

Write-Host "Building API..."
$env:DOCKER_BUILDKIT=0
docker compose build --no-cache api 2>&1 | Out-File $logFile -Append

Write-Host "Building Web..."
$env:DOCKER_BUILDKIT=0
docker compose build --no-cache web 2>&1 | Out-File $logFile -Append

Write-Host "Starting..."
docker compose up -d 2>&1 | Out-File $logFile -Append

Start-Sleep -Seconds 5

Write-Host "Running migration..."
docker exec crmsystem-api-1 alembic upgrade head 2>&1 | Out-File $logFile -Append

"=== Rebuild completed at $(Get-Date) ===" | Out-File $logFile -Append
Write-Host "Done. Check $logFile"
