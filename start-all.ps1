# Запуск всех сервисов GoGoCarpool: по очереди открываются 4 окна PowerShell.
# Запускать из корня проекта: .\start-all.ps1

$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
$RedisPath = "C:\Program Files\Redis\redis-server.exe"

Write-Host "GoGoCarpool: запуск Redis, Django, Frontend, Celery (по одному окну)." -ForegroundColor Green
Write-Host "Корень проекта: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# 1. Redis
Write-Host "[1/4] Открываю окно: Redis (порт 6379)..." -ForegroundColor Cyan
if (Test-Path $RedisPath) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Redis' -ForegroundColor Yellow; & '$RedisPath'"
} else {
    Write-Host "    Redis не найден по пути: $RedisPath" -ForegroundColor Red
    Write-Host "    Откройте окно вручную и запустите redis-server (или измените RedisPath в скрипте)." -ForegroundColor Yellow
}
Start-Sleep -Seconds 2

# 2. Django
Write-Host "[2/4] Открываю окно: Django (порт 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; Write-Host 'Django runserver' -ForegroundColor Yellow; .\venv\Scripts\Activate.ps1; python manage.py runserver"
Start-Sleep -Seconds 2

# 3. Frontend
Write-Host "[3/4] Открываю окно: Frontend (порт 5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\frontend'; Write-Host 'Vite (Frontend)' -ForegroundColor Yellow; npm run dev"
Start-Sleep -Seconds 2

# 4. Celery
Write-Host "[4/4] Открываю окно: Celery (воркер очереди)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; Write-Host 'Celery worker (solo pool для Windows)' -ForegroundColor Yellow; .\venv\Scripts\Activate.ps1; celery -A GoGoCarpool worker -l info --pool=solo"

Write-Host ""
Write-Host "Готово. Открыто 4 окна. Сайт: http://localhost:5173/" -ForegroundColor Green
Write-Host "Закрытие окна останавливает соответствующий процесс." -ForegroundColor Gray
