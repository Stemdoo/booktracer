# BookTracker — подготовка к ПЗ №8

## Локальный запуск

Python 3.12 или 3.13 рекомендуется. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

При локальном запуске `DJANGO_DEBUG` по умолчанию `True`; если переменная явно задана в `False`, укажите `DJANGO_SECRET_KEY`. На публичном сервисе ключ обязателен.

## Render

1. Загрузите содержимое проекта в GitHub, не добавляя `.env`, `db.sqlite3` или `.venv`.
2. Создайте PostgreSQL и Web Service в одном регионе Render.
3. Укажите Build Command: `bash build.sh`.
4. Укажите Start Command: `gunicorn booktracker.wsgi:application --bind 0.0.0.0:$PORT`.
5. Добавьте `DATABASE_URL` (Internal Database URL), `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=имя-сервиса.onrender.com`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://имя-сервиса.onrender.com`.
6. После сборки выполните `python manage.py migrate` в контролируемой консоли с теми же переменными окружения.
7. При необходимости создайте администратора командой `python manage.py createsuperuser`.
8. Проверьте `https://имя-сервиса.onrender.com/healthz/`, главную страницу и API.

## Проверки для отчёта

```bash
python manage.py check
python manage.py showmigrations
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Проверки API: `GET /api/books/`, `GET /api/genres/`, авторизованный `GET /api/my-book-statuses/` и `POST` на `/api/my-book-statuses/` с JSON `{"book": 1, "status": "to_read"}`. Для изменяющих запросов используйте авторизованную сессию и CSRF-токен, если он требуется конфигурацией.

`/healthz/` подтверждает доступность Django, но не соединение с базой данных. Связь с БД следует подтвердить реальным запросом к каталогу/API. Для доказательства постоянного хранения создайте запись, перезапустите Web Service и проверьте запись повторно.

## Важно

- Примеры из методички с `config.wsgi` и `/api/categories/` относятся к другому учебному проекту. В BookTracker правильный WSGI-модуль — `booktracker.wsgi:application`, а каталог жанров — `/api/genres/`.
- Не переносите в отчёт секреты, пароли, cookie или CSRF-токены.
- Локальная SQLite-база не переносится автоматически в облачный PostgreSQL. После миграций облачную базу нужно наполнить заново либо отдельно выполнить контролируемый перенос данных.
