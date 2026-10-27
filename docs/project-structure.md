# Структура проекта

```text
booktracer/
├── booktracker/              # настройки Django и точки входа WSGI/ASGI
│   ├── settings.py            # конфигурация приложения, окружения и БД
│   ├── urls.py                # маршруты admin, accounts и library
│   ├── wsgi.py                # WSGI-точка входа для Gunicorn
│   └── asgi.py                # ASGI-точка входа
├── library/                   # основная предметная область
│   ├── models.py              # модели каталога, чтения и бронирований
│   ├── views.py               # HTML-представления и REST API
│   ├── urls.py                # URL-маршруты приложения
│   ├── serializers.py         # преобразование моделей в JSON и проверка входных данных
│   ├── admin.py               # регистрация моделей в Django Admin
│   ├── migrations/            # история схемы базы данных
│   └── management/commands/   # дополнительные команды Django
├── templates/                 # HTML-шаблоны страниц и компонентов
├── static/                    # CSS и JavaScript
├── library_data.json          # учебные начальные данные (fixture)
├── requirements.txt           # Python-зависимости
├── .env.example               # безопасный шаблон переменных окружения
├── build.sh                   # установка зависимостей и сбор статики для Render
├── dockerfile                 # образ веб-приложения
├── compose.yaml               # локальный запуск приложения и PostgreSQL
├── manage.py                  # команды Django
└── docs/                      # техническая документация
```

## Основные конфигурационные файлы

- `booktracker/settings.py`: настройки безопасности, приложений, базы данных, шаблонов и статики.
- `booktracker/urls.py`: подключает `/admin/`, встроенные страницы авторизации `/accounts/` и маршруты `library`.
- `requirements.txt`: зависимости приложения.
- `.env.example`: только имена переменных и безопасные примеры. Секреты сюда не помещаются.
- `build.sh`: устанавливает зависимости и собирает статические файлы; миграции запускаются отдельным шагом.
- `dockerfile` и `compose.yaml`: локальный контейнерный запуск. Compose использует PostgreSQL, а запуск без `DATABASE_URL` — SQLite.
- `library_data.json`: fixture с начальными данными. Её загрузка — отдельная операция и не выполняется автоматически при каждом старте.
