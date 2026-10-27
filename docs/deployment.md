# Локальный запуск и развёртывание на Render

## 1. Локальный запуск с нуля (Windows PowerShell)

Из корня репозитория:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Откройте `.env`: задайте локальный `DJANGO_SECRET_KEY`, оставьте `DJANGO_DEBUG=True`, `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`, а `DATABASE_URL` оставьте пустым для SQLite.

```powershell
python manage.py check
python manage.py migrate
python manage.py loaddata library_data.json
python manage.py createsuperuser
python manage.py runserver
```

Fixture загружайте один раз на чистую базу. Если записи уже есть, сначала проверьте их, чтобы избежать дублей/конфликтов. После запуска проверьте `/`, `/admin/`, `/api/books/` и `/api/genres/`.

## 2. Docker Compose (альтернативный локальный запуск)

Требуется установленный Docker Desktop.

```powershell
docker compose up --build
```

Compose запускает веб-приложение и PostgreSQL; приложение выполняет `migrate` при старте. Для остановки:

```powershell
docker compose down
```

Чтобы сохранить данные PostgreSQL между остановками, не удаляйте именованный volume. `docker compose down -v` удалит его и данные.

## 3. Render: Web Service + PostgreSQL

Используйте бесплатные доступные возможности платформы, если они подходят текущим ограничениям Render. Важно учитывать, что доступность и срок хранения бесплатной базы/сервиса определяются актуальными условиями Render.

1. Убедитесь, что `.env`, `db.sqlite3`, `.venv/`, `venv/` и секреты не добавлены в Git.
2. Создайте PostgreSQL в Render. Web Service и база должны находиться в одном регионе.
3. Создайте Web Service из GitHub-репозитория.
4. Build Command: `bash build.sh`.
5. Start Command: `gunicorn booktracker.wsgi:application --bind 0.0.0.0:$PORT`.
6. В Environment задайте:
   - `DJANGO_SECRET_KEY` — длинный случайный секретный ключ Django.
   - `DJANGO_DEBUG=False` — отключает подробные отладочные страницы.
   - `DJANGO_ALLOWED_HOSTS=имя-сервиса.onrender.com` — список разрешённых имён хоста через запятую.
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://имя-сервиса.onrender.com` — доверенные origin для CSRF, включая схему `https://`.
   - `DATABASE_URL` — Internal Database URL из настроек PostgreSQL Render; не копируйте его в README, репозиторий, скриншоты или отчёт.
7. Выполните миграции отдельно после сборки: откройте доступную для сервиса консоль/шелл и выполните `python manage.py migrate` с переменными окружения Web Service. Если используемая конфигурация Render не предоставляет Shell на текущем тарифе, организуйте выполнение миграций через согласованную команду/процесс запуска, не предполагая наличие платной функции.
8. Создайте администратора командой `python manage.py createsuperuser` в среде, подключённой к той же базе, если он ещё не создан.
9. Проверьте главную страницу, `/admin/`, `GET /api/books/` и `GET /api/genres/`. Для пользовательских API проверьте вход и CSRF.

## 4. Что делают переменные окружения

| Переменная | Назначение |
|---|---|
| `DJANGO_SECRET_KEY` | Ключ подписи Django; секрет, нельзя публиковать |
| `DJANGO_DEBUG` | `True` для локальной разработки, `False` на публичном сервисе |
| `DJANGO_ALLOWED_HOSTS` | Разрешённые домены через запятую |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Доверенные origin, каждый с `http://` или `https://` |
| `DATABASE_URL` | Строка подключения к базе; секрет, если содержит учётные данные |

`Internal Database URL` предназначен для соединения между сервисами внутри инфраструктуры Render. Его следует использовать в `DATABASE_URL` переменных Web Service, а не публиковать. В локальной среде `DATABASE_URL` можно оставить пустым — тогда настройки выбирают SQLite.

## 5. Сборка, миграции, запуск и проверка — разные шаги

- Сборка: `bash build.sh` устанавливает зависимости и собирает статику.
- Миграции: `python manage.py migrate` создаёт/обновляет таблицы.
- Запуск: Gunicorn запускает `booktracker.wsgi:application`.
- Проверка: `python manage.py check`, `python manage.py showmigrations`, открытие страниц и проверка API.
- Наполнение: `python manage.py loaddata library_data.json` — отдельная операция, не включена в сборку и не должна автоматически перезаписывать данные публичной базы.

## 6. Перенос данных

Локальная SQLite и облачная PostgreSQL не являются одной базой. Команда `migrate` переносит схему, но не записи. Если нужно перенести данные, сначала сделайте резервную копию, экспортируйте только нужные модели, проверьте зависимости и выполните контролируемую загрузку в PostgreSQL. Не копируйте `db.sqlite3` в публичный репозиторий.
