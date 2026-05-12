---
name: django-layout
description: A deterministic program for generating production-ready Django sites with uv, Docker, and htmx.
triggers:
  - "create a new django project"
  - "generate the files for a django project called myproject"
---

# Django Project Specification & Tooling
When this skill is activated, use the following files and rules to generate the project.

## 1. Project Dependencies (pyproject.toml)
```toml
[project]
name = "myproject"
version = "0.1.0"
dependencies = [
    "django",
    "django-environ",
    "django-allauth",
    "django-htmx",
    "django-storages[s3]",
    "boto3",
    "whitenoise",
    "gunicorn",
    "psycopg[binary]",
    "redis",
    "celery",
    "django-health-check",
    "sentry-sdk",
]

[tool.uv]
dev-dependencies = [
    "pytest-django",
    "pytest-cov",
    "factory-boy",
    "django-debug-toolbar",
    "django-extensions",
    "django-browser-reload",
    "ruff",
    "ty",
    "pre-commit",
]
```

## 2. Infrastructure

### Dockerfile
```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ARG UID=1000
ARG GID=1000
RUN groupadd -g "$GID" app && useradd -u "$UID" -g "$GID" -m app

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --chown=app:app . .

USER app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
```

### docker-compose.yml
```yaml
services:
  web:
    build:
      context: .
      args:
        UID: ${UID:-1000}
        GID: ${GID:-1000}
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./.data/backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  celery:
    build:
      context: .
      args:
        UID: ${UID:-1000}
        GID: ${GID:-1000}
    command: celery -A config worker -l info
    env_file: .env
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
```

### Makefile
```makefile
include .env
export

build:
	docker compose build --build-arg UID=$(shell id -u) --build-arg GID=$(shell id -g)

up:
	docker compose up -d

migrate:
	docker compose exec web python manage.py migrate

test:
	docker compose exec web pytest --cov=apps

db-backup:
	docker compose exec db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > .data/backups/backup.sql
```

### entrypoint.sh
```bash
#!/bin/bash
set -e
python manage.py migrate --no-input
if [ "$DJANGO_ENV" = "production" ]; then
    python manage.py collectstatic --no-input
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
else
    python manage.py runserver 0.0.0.0:8000
fi
```

### .env.example
```
# Django
DJANGO_ENV=development
DJANGO_SECRET_KEY=change-me-generate-with-python-secrets
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=myproject
POSTGRES_USER=myproject
POSTGRES_PASSWORD=myproject

# Redis / Celery
REDIS_URL=redis://redis:6379/0

# AWS S3 (production media/static storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=

# Sentry
SENTRY_DSN=
```

## 3. Application Configuration

### Settings rule (config/settings.py)
Generate a **single** `config/settings.py`. Use the `DJANGO_ENV` environment variable to gate
behaviour — never split into multiple settings files. Valid values are `development`, `staging`,
`production`, and `test`. Apply the pattern consistently:

```python
DJANGO_ENV = env("DJANGO_ENV", default="development")
DEBUG = DJANGO_ENV in ("development", "test")
```

### config/__init__.py
```python
from .celery import app as celery_app

__all__ = ["celery_app"]
```

### config/celery.py
```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

### config/wsgi.py
```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
```

### config/asgi.py
```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
```

### config/urls.py
```python
from django.contrib import admin
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("health/", include("health_check.urls")),
]

if settings.DJANGO_ENV in ("development", "test"):
    import debug_toolbar
    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("__reload__/", include("django_browser_reload.urls")),
    ]
```

## 4. Core Logic & Templates
- **Directory Layout:** Apps in `/apps`, Config in `/config`, Templates in `/assets/templates`.
- **Auth:** Use `apps.accounts.adapters.CustomAccountAdapter`.
- **Base Template:** Responsive with Alpine.js hamburger menu and sidebar blocks.
- **Error Handling:** Include endpoints in dev for 404, 500, and Sentry triggers.

## 5. Quality Control (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: type-check
        name: type-check
        entry: uv run ty check
        language: system
        types: [python]
        pass_filenames: false
```

# Final Instructions
1. Replace all occurrences of `myproject` with the project name supplied by the user.
2. Create the directory structure.
3. Generate all listed files with the provided content.
4. Copy `.env.example` to `.env` and prompt the user to set `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`.
5. Initialize a git repository and run `uv lock`.
6. Verify by running `make build && make up` then checking the `/health/` endpoint.
