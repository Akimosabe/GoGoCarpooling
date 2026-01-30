# GoGoCarpool

Платформа для совместных поездок (карпулинг). Backend: Django REST API. Frontend: React + TypeScript + Vite.

## Требования

- Python 3.12
- Node.js 18+
- Redis — для очереди задач (письма, уведомления). Без Redis письма отправляются синхронно.

## Установка

### 1. Backend (Django)

```powershell
cd C:\Projects\GoGoCarpooling
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
```

### 2. Frontend

```powershell
cd C:\Projects\GoGoCarpooling\frontend
npm install
```

### 3. Скрытые настройки (почта, секреты)

В корне проекта создайте файл **`hiddensettings.env`** (он в `.gitignore`, в репозиторий не попадёт). Django при старте подхватит из него переменные окружения.

Пример содержимого (подставьте свои значения):

```env
DJANGO_SECRET_KEY=ваш-секретный-ключ
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Yandex SMTP: пароль — пароль приложения, не от входа в почту
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=587
EMAIL_HOST_USER=ваш-email@yandex.com
EMAIL_HOST_PASSWORD=пароль-приложения

REDIS_URL=redis://localhost:6379/0
```

Для разработки без реальной отправки писем добавьте в файл:
`EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` — письма будут выводиться в консоль Django.

---

## Развёртывание (запуск для работы)

Чтобы всё работало (сайт, API, письма, уведомления), нужно **одновременно** запустить **Redis**, **Django**, **Frontend** и (при необходимости) **Celery**. Запускать в **отдельных терминалах** и **строго по порядку**.

### Очередность запуска (почему именно так)

| Шаг | Что запускать | Зачем этот порядок |
|-----|----------------|--------------------|
| **1** | Redis | Очередь должна быть доступна до Django и Celery. |
| **2** | Django | API должен подняться до фронта (фронт ходит на 8000). |
| **3** | Frontend | Сайт на 5173, подключается к API. |
| **4** | Celery | Воркер подключается к Redis; Django уже ставит задачи в очередь. |

Если Redis не запущен — письма восстановления пароля уйдут синхронно из Django. Если Redis запущен, но Celery не запущен — задачи будут в очереди и не выполнятся, тогда сработает запасной вариант (Django отправит сам).

### Запуск вручную (по шагам)

### 1. Redis (очередь задач: письма, уведомления)

Без Redis письма восстановления пароля всё равно отправляются (синхронно). С Redis — через очередь Celery.

**Windows (если Redis установлен, например в `C:\Program Files\Redis`):**

```powershell
& "C:\Program Files\Redis\redis-server.exe"
```

**Или через Docker:**

```powershell
docker run -d -p 6379:6379 --name redis redis
```

Оставьте терминал с Redis открытым (или запустите Redis как службу). Порт **6379** должен быть занят.

### 2. Backend (Django)

```powershell
cd C:\Projects\GoGoCarpooling
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

- API: **http://127.0.0.1:8000/**
- Остановка: `Ctrl+C`

### 3. Frontend (Vite)

```powershell
cd C:\Projects\GoGoCarpooling\frontend
npm run dev
```

- Сайт: **http://localhost:5173/** (или адрес из консоли)
- Остановка: `Ctrl+C`

### 4. Celery (воркер очереди) — если запущен Redis

Нужен только если Redis запущен и вы хотите, чтобы письма и уведомления обрабатывались через очередь (а не синхронно).

**Windows** — обязательно с пулом `solo` (иначе возможны ошибки):

```powershell
cd C:\Projects\GoGoCarpooling
.\venv\Scripts\Activate.ps1
celery -A GoGoCarpool worker -l info --pool=solo
```

**Linux/macOS** — можно без `--pool=solo`.

Оставьте терминал открытым.

---

**Итог при запуске:**

| Что        | Порт   | Зачем                          |
|-----------|--------|---------------------------------|
| Redis     | 6379   | Очередь задач (письма и т.д.)  |
| Django    | 8000   | API и админка                   |
| Frontend  | 5173   | Интерфейс сайта                |
| Celery    | —      | Выполняет задачи из Redis       |

Откройте в браузере **http://localhost:5173/** — сайт должен работать. Письма (восстановление пароля) работают и без Redis (синхронно); с Redis и Celery — через очередь.

### Запуск одним скриптом (все терминалы по очереди)

В корне проекта лежит скрипт **`start-all.ps1`**. Он по очереди открывает четыре окна PowerShell и запускает в них Redis, Django, Frontend и Celery. Запускать из корня проекта:

```powershell
cd C:\Projects\GoGoCarpooling
.\start-all.ps1
```

Откроются 4 окна (с небольшой паузой между ними). Закрытие окна останавливает соответствующий процесс. Путь к Redis в скрипте зашит как `C:\Program Files\Redis\redis-server.exe` — при другом расположении Redis отредактируйте скрипт.

## Сборка фронтенда (production)

```powershell
cd C:\Projects\GoGoCarpooling\frontend
npm run build
```

Результат в `frontend/dist/`. Раздавать статику через веб-сервер (nginx, etc.) и проксировать `/api` и `/media` на Django.

## Структура проекта

```
GoGoCarpooling/
├── carpooling/          # Django-приложение (модели, API, задачи)
├── frontend/            # React SPA (Vite)
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   └── contexts/
│   └── package.json
├── GoGoCarpool/         # Настройки Django
├── manage.py
└── requirements.txt
```

## API

Base URL: http://localhost:8000/api/

- `GET/POST /api/auth/` — регистрация, вход
- `GET /api/auth/me/` — текущий пользователь
- `GET /api/trips/` — список поездок (поиск)
- `GET /api/trips/<id>/` — детали поездки
- `POST /api/trips/create/` — создание поездки
- `GET /api/my-trips/` — мои поездки
- `POST /api/trips/<id>/book/` — бронирование
- `GET /api/my-bookings/` — мои бронирования
- `GET /api/users/<id>/profile/` — профиль пользователя
- `GET /api/cities/`, `GET /api/cities/autocomplete/` — города
- `GET/POST /api/notifications/` — уведомления

## Полезные команды

**Backend:**

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py createsuperuser
python manage.py check
```

**Frontend:**

```powershell
cd frontend
npm run dev
npm run build
npm run lint
```
