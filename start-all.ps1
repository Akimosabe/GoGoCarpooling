# Start all GoGoCarpool services: opens 4 PowerShell windows in sequence.
# Run from project root: .\start-all.ps1

$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
$RedisPath = "C:\Program Files\Redis\redis-server.exe"

Write-Host "GoGoCarpool: starting Redis, Django, Frontend, Celery (one window each)." -ForegroundColor Green
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# 1. Redis
Write-Host "[1/4] Opening window: Redis (port 6379)..." -ForegroundColor Cyan
if (Test-Path $RedisPath) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Redis' -ForegroundColor Yellow; & '$RedisPath'"
} else {
    Write-Host "    Redis not found at: $RedisPath" -ForegroundColor Red
    Write-Host "    Open a window manually and run redis-server (or change RedisPath in script)." -ForegroundColor Yellow
}
Start-Sleep -Seconds 2

# 2. Django
Write-Host "[2/4] Opening window: Django (port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; Write-Host 'Django runserver' -ForegroundColor Yellow; .\venv\Scripts\Activate.ps1; python manage.py runserver"
Start-Sleep -Seconds 2

# 3. Frontend
Write-Host "[3/4] Opening window: Frontend (port 5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\frontend'; Write-Host 'Vite (Frontend)' -ForegroundColor Yellow; npm run dev"
Start-Sleep -Seconds 2

# 4. Celery
Write-Host "[4/4] Opening window: Celery (queue worker)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; Write-Host 'Celery worker (solo pool for Windows)' -ForegroundColor Yellow; .\venv\Scripts\Activate.ps1; celery -A GoGoCarpool worker -l info --pool=solo"

Write-Host ""
Write-Host "Done. 4 windows opened. Site: http://localhost:5173/" -ForegroundColor Green
Write-Host "Closing a window stops that process." -ForegroundColor Gray
