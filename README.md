# GoGoCarpool - Carpooling Platform

Django REST API backend for a carpooling service.

## Tech Stack

- Python 3.12
- Django 6.0
- Django REST Framework
- Celery + Redis (async tasks)
- SQLite (development)

## Quick Start (Windows PowerShell)

### Терминал 1 — Redis (если не запущен как служба)
```powershell
& "C:\Program Files\Redis\redis-server.exe"
```

### Терминал 2 — Celery worker
```powershell
cd C:\Projects\GoGoCarpooling
.\venv\Scripts\Activate.ps1
celery -A GoGoCarpool worker -l info
```

### Терминал 3 — Django сервер
```powershell
cd C:\Projects\GoGoCarpooling
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

Сервер будет доступен по адресу: http://127.0.0.1:8000/

### Первоначальная настройка (если venv отсутствует)

```powershell
# Создать виртуальное окружение (Python 3.12)
py -3.12 -m venv venv

# Активировать
.\venv\Scripts\Activate.ps1

# Установить зависимости
pip install -r requirements.txt

# Скопировать и настроить переменные окружения
copy .env.example .env
# Отредактировать .env — указать секреты

# Применить миграции
python manage.py migrate
```

### Полезные команды

```powershell
python manage.py makemigrations   # Создать миграции
python manage.py migrate          # Применить миграции
python manage.py createsuperuser  # Создать админа
python manage.py check            # Проверить проект
```

## API Documentation

API is available at: `http://localhost:8000/api/`

### Main Endpoints

- `/api/auth/` - Authentication
- `/api/trips/` - Trips management
- `/api/bookings/` - Bookings
- `/api/users/` - User profiles
- `/api/cities/` - Cities
- `/api/ratings/` - Ratings
- `/api/notifications/` - Notifications

## Project Structure

```
carpooling/
├── models/         # Data models
├── serializers/    # DRF serializers
└── views/          # API views
```

## License

Private project
