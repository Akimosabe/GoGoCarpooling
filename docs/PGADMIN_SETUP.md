# Переход на PostgreSQL: что сделать вам (pgAdmin 4 + проект)

Без сохранения данных. После выполнения этих шагов Django будет работать с PostgreSQL.

---

## Часть 1. В pgAdmin 4

### 1.1. Подключиться к серверу

- Откройте pgAdmin 4.
- В левой панели: **Servers** → ваш сервер PostgreSQL (например, PostgreSQL 15).
- Если при первом входе просят пароль — введите пароль пользователя **postgres** (тот, что задавали при установке PostgreSQL).

### 1.2. Создать пользователя (роль) для приложения

1. Правый клик по **Login/Group Roles** → **Create** → **Login/Group Role**.
2. Вкладка **General**:
   - **Name:** `gogocarpool` (или любое имя — его потом укажете в `hiddensettings.env`).
3. Вкладка **Definition**:
   - **Password:** придумайте пароль и запомните его (нужен для `DJANGO_DB_PASSWORD`).
4. Вкладка **Privileges:** включите **Can login**.
5. **Save**.

### 1.3. Создать базу данных

1. Правый клик по **Databases** → **Create** → **Database**.
2. Вкладка **General**:
   - **Database:** `gogocarpool` (или то же имя, что будет в `DJANGO_DB_NAME`).
   - **Owner:** выберите созданную роль `gogocarpool`.
3. **Save**.

Больше в pgAdmin ничего делать не нужно. Дальше — настройка проекта.

---

## Часть 2. В проекте (в корне GoGoCarpooling)

### 2.1. Файл `hiddensettings.env`

В **корне проекта** (рядом с `manage.py`) откройте или создайте файл **`hiddensettings.env`** и добавьте (подставьте свои значения):

```env
DJANGO_DB_NAME=gogocarpool
DJANGO_DB_USER=gogocarpool
DJANGO_DB_PASSWORD=ваш_пароль_от_роли_gogocarpool
```

Если PostgreSQL на этой же машине и порт стандартный (5432), хост и порт можно не указывать. Если база на другом компьютере или другой порт:

```env
DJANGO_DB_HOST=127.0.0.1
DJANGO_DB_PORT=5432
```

Сохраните файл.

### 2.2. Установить драйвер и применить миграции

В терминале, в корне проекта, с активированным venv:

```bash
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

- `migrate` создаст все таблицы в PostgreSQL.
- `createsuperuser` — логин/пароль для входа в админку (новые, т.к. данные не переносим).

### 2.3. Запуск

Запустите проект как обычно (например, `start-all.ps1` или `python manage.py runserver`). Django подключится к PostgreSQL.

---

## Краткий чеклист

| # | Где | Что сделать |
|---|-----|-------------|
| 1 | pgAdmin | Создать Login/Group Role с именем и паролем (например, `gogocarpool`). |
| 2 | pgAdmin | Создать Database с тем же именем, Owner — эта роль. |
| 3 | Проект | В корне создать/отредактировать `hiddensettings.env`: `DJANGO_DB_NAME`, `DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`. |
| 4 | Терминал | `pip install -r requirements.txt` → `python manage.py migrate` → `python manage.py createsuperuser`. |

Когда сделаете свою часть (pgAdmin + `hiddensettings.env`), напишите — подскажу, что проверить, если что-то пойдёт не так.
