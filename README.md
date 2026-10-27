# BookTracer

BookTracer — веб-приложение для просмотра каталога книг, ведения личного списка чтения и бронирования доступных экземпляров. Проект построен на Django и Django REST Framework; развёртывание предусмотрено на Render, локально поддерживаются SQLite и Docker Compose с PostgreSQL.

## Возможности

- Просмотр каталога, поиск по названию и автору, фильтр по жанру, сортировка и постраничная выдача.
- Просмотр описания книги и её фрагмента.
- Избранное и личные статусы чтения: «Планирую читать», «Читаю сейчас», «Прочитано».
- Бронирование книг и переходы между статусами: создано, подтверждено, выдано, завершено, отменено.
- История событий бронирования.
- Django Admin для управления авторами, жанрами, книгами и пользовательскими записями.
- REST API для каталога, статусов чтения и бронирований.

## Технологии

- Python 3.11+ (для локального запуска используйте версию, совместимую с зависимостями проекта).
- Django 5.2–6.1, Django REST Framework.
- SQLite для локального запуска без `DATABASE_URL`; PostgreSQL при заданном `DATABASE_URL`.
- Gunicorn для запуска WSGI-приложения на Render.
- WhiteNoise для статических файлов.
- `dj-database-url` для разбора URL базы данных, `python-dotenv` для локального `.env`.

## Быстрый старт — Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Откройте `.env` и при необходимости измените `DJANGO_SECRET_KEY`. Для локального запуска оставьте `DATABASE_URL` пустым, чтобы использовалась SQLite.

```powershell
python manage.py check
python manage.py migrate
python manage.py loaddata library_data.json
python manage.py createsuperuser
python manage.py runserver
```

Если `library_data.json` уже загружен ранее, команда `loaddata` может сообщить о повторяющихся уникальных данных. Не запускайте её повторно без проверки содержимого базы. Затем откройте `http://127.0.0.1:8000/`; административная панель доступна по `/admin/`.

## Быстрая проверка API

- `GET /api/books/` — список книг.
- `GET /api/genres/` — список жанров.
- `GET /api/books/1/` — сведения о книге с ID 1, если она существует.
- `GET /api/my-book-statuses/` — требует входа пользователя.
- `GET /api/reservations/` — требует входа пользователя.

Подробные маршруты, методы, параметры, примеры и ограничения приведены в [`docs/api.md`](docs/api.md).

## Документация

- [Архитектура](docs/architecture.md)
- [Структура проекта](docs/project-structure.md)
- [Модели базы данных](docs/database.md)
- [REST API](docs/api.md)
- [Локальный запуск и развёртывание на Render](docs/deployment.md)
- [Типичные ошибки и диагностика](docs/troubleshooting.md)
- [Проверка воспроизводимости](docs/reproducibility.md)

## Важные замечания

- Локальная SQLite и PostgreSQL на Render — разные базы. Миграции создают таблицы, но не переносят содержимое локальной базы.
- Не публикуйте `.env`, `db.sqlite3`, пароли, токены, cookie или значения `DATABASE_URL`.
- Для публичного развёртывания обязательно задайте секретный `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, актуальные `DJANGO_ALLOWED_HOSTS` и `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Архив с документацией не подтверждает сам по себе успешный запуск в чистом окружении. Заполните фактические результаты в `docs/reproducibility.md` после выполнения команд на своей машине.
