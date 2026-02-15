# Сборка фронта (Node)
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Бэкенд (Django) + статика фронта
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN python manage.py collectstatic --noinput

EXPOSE 10000
# Без Shell на Render: миграции, города из seed, суперпользователь из env (если заданы), затем gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_cities && if [ -n \"$DJANGO_SUPERUSER_EMAIL\" ]; then python manage.py createsuperuser --noinput 2>/dev/null || true; fi && exec gunicorn GoGoCarpool.wsgi --bind 0.0.0.0:$PORT --workers 1 --threads 2"]
