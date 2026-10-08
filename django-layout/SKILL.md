---
name: django-layout
description: Scaffold a production-ready Django project with uv, Docker, and PostgreSQL. Asks which optional add-ons (Celery/Redis, S3 storage, auth, htmx, Sentry, dev tools) to include before generating anything, so the result only contains what was actually requested. Use when the user wants to create a new Django project, or generate the files for a Django project scaffold.
version: 0.2.0
---

# Django Project Specification & Tooling

This skill generates a Django project in two phases: first agree the shape of the project with
the user, then generate exactly that — nothing more. A fixed template that includes packages
nobody asked for means the project's first few commits are spent ripping them back out. Asking
first avoids that.

## Phase 1 — Confirm scope

Before generating any files, ask the user two things:

1. **Project name** (replaces `myproject` everywhere below).
2. **Which optional add-ons to include**, from the list in "Optional add-ons" below. Present
   the list and ask them to confirm, decline, or adjust each one — don't silently assume
   defaults for anything beyond the core.

Confirm their choices back before generating anything. If they ask for something not listed
here (a different database, a different frontend approach), treat it as a deliberate deviation
from this recipe and adapt the core accordingly, rather than forcing it into one of the add-ons
below.

## Phase 2 — Core (always included)

The core is deliberately small: a running Django site with Postgres, Docker, and a quality
toolchain. Nothing here should need removing later regardless of what add-ons are chosen.

### pyproject.toml
```toml
[project]
name = "myproject"
version = "0.1.0"
dependencies = [
    "django",
    "django-environ",
    "whitenoise",
    "gunicorn",
    "psycopg[binary]",
]

[tool.uv]
dev-dependencies = [
    "pytest-django",
    "pytest-cov",
    "factory-boy",
    "ruff",
    "ty",
    "pre-commit",
]
```
Append each accepted add-on's dependencies (below) to the relevant list — don't create a
separate file per add-on.

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
      # Add `redis: {condition: service_healthy}` here if Celery/Redis was accepted.

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

volumes:
  postgres_data:
```
If Celery/Redis is accepted, add the `redis` and `celery` services from that add-on's section
below, and the `redis` dependency on `web`.

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
```
Append each accepted add-on's environment variables (below) to this file.

### Settings rule (config/settings.py)
Generate a **single** `config/settings.py`. Use the `DJANGO_ENV` environment variable to gate
behaviour — never split into multiple settings files. Valid values are `development`, `staging`,
`production`, and `test`. Apply the pattern consistently:

```python
DJANGO_ENV = env("DJANGO_ENV", default="development")
DEBUG = DJANGO_ENV in ("development", "test")
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
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
```
Add each accepted add-on's URL includes (below) to this list.

### Directory layout
Apps in `/apps`, config in `/config`, templates in `/assets/templates`.

### Quality control (.pre-commit-config.yaml)
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

## Optional add-ons

Each add-on is independent — accept any combination. For each one accepted, splice its pieces
into the core files above rather than generating stray extra files.

### Celery + Redis (background tasks)
- **Dependencies:** add `redis`, `celery` to `pyproject.toml`.
- **`config/__init__.py`:**
  ```python
  from .celery import app as celery_app

  __all__ = ["celery_app"]
  ```
- **`config/celery.py`:**
  ```python
  import os
  from celery import Celery

  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

  app = Celery("config")
  app.config_from_object("django.conf:settings", namespace="CELERY")
  app.autodiscover_tasks()
  ```
- **`docker-compose.yml`:** add a `redis` service and a `celery` service, and make `web` depend
  on `redis` as well as `db`:
  ```yaml
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
  ```
- **`.env.example`:** add `REDIS_URL=redis://redis:6379/0`.

### django-storages + S3 (production media/static storage)
- **Dependencies:** add `django-storages[s3]`, `boto3` to `pyproject.toml`.
- **`.env.example`:** add
  ```
  AWS_ACCESS_KEY_ID=
  AWS_SECRET_ACCESS_KEY=
  AWS_STORAGE_BUCKET_NAME=
  AWS_S3_REGION_NAME=
  ```
- Configure `STORAGES` in `config/settings.py` to use `storages.backends.s3.S3Storage` when
  `DJANGO_ENV == "production"`, falling back to local disk storage + whitenoise otherwise.

### django-allauth (authentication)
- **Dependencies:** add `django-allauth` to `pyproject.toml`.
- **`config/urls.py`:** add `path("accounts/", include("allauth.urls"))`.
- Create `apps/accounts/adapters.py` with a `CustomAccountAdapter(DefaultAccountAdapter)` as the
  extension point for custom signup/login behaviour, and wire it up via
  `ACCOUNT_ADAPTER` in settings.

### django-htmx + Alpine.js (interactive frontend)
- **Dependencies:** add `django-htmx` to `pyproject.toml`.
- Add `django_htmx.middleware.HtmxMiddleware` to `MIDDLEWARE`.
- Base template (`assets/templates/base.html`): responsive layout with an Alpine.js-driven
  hamburger menu and sidebar blocks, htmx attributes wired for partial page updates.

### Sentry (error monitoring)
- **Dependencies:** add `sentry-sdk` to `pyproject.toml`.
- **`.env.example`:** add `SENTRY_DSN=`.
- Initialise in `config/settings.py`, gated on `DJANGO_ENV == "production"` and `SENTRY_DSN`
  being set.
- If dev tools (below) are also accepted, add a dev-only endpoint that deliberately raises, to
  verify Sentry is wired up before going to production.

### django-health-check (health endpoint)
- **Dependencies:** add `django-health-check` to `pyproject.toml`.
- **`config/urls.py`:** add `path("health/", include("health_check.urls"))`.

### Dev tools (debug toolbar, browser reload, extra management commands)
- **Dependencies:** add `django-debug-toolbar`, `django-extensions`, `django-browser-reload` to
  the `dev-dependencies` list (not the main `dependencies` list — these must never load outside
  `development`/`test`).
- **`config/urls.py`:** gated on `DJANGO_ENV in ("development", "test")`:
  ```python
  if settings.DJANGO_ENV in ("development", "test"):
      import debug_toolbar
      urlpatterns += [
          path("__debug__/", include(debug_toolbar.urls)),
          path("__reload__/", include("django_browser_reload.urls")),
      ]
  ```
- Include a dev-only 404/500 test endpoint for exercising Django's error pages locally.

## Final Instructions

1. Replace all occurrences of `myproject` with the project name confirmed in Phase 1.
2. Create the directory structure, including only the pieces each accepted add-on needs.
3. Generate the core files plus the spliced-in content for each accepted add-on. Do not
   generate a file, dependency, or environment variable for an add-on that wasn't accepted.
4. Copy `.env.example` to `.env` and prompt the user to set `DJANGO_SECRET_KEY` and
   `POSTGRES_PASSWORD` (and any accepted add-on's secrets, e.g. `SENTRY_DSN`,
   `AWS_SECRET_ACCESS_KEY`).
5. Initialize a git repository and run `uv lock`.
6. Verify by running `make build && make up`, then checking the site loads (and `/health/` if
   that add-on was accepted).
