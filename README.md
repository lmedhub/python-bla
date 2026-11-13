# Task Manager

A task manager API (Django 6.1 + DRF + PostgreSQL + Celery/Redis) with a React frontend,
built as a technical interview exercise.

**Status:** Phase 4 (backend done: API, background email with Celery, Docker images for the
backend). See [PLAN.md](PLAN.md). The frontend, demo data, full setup guide and architecture
summary come in Phases 5 and 6.

## Run the backend with Docker

```sh
cp .env.example .env
docker compose up -d --build
```

| Service | What it is | URL |
| --- | --- | --- |
| `api` | Django + gunicorn. Runs migrations on start | http://localhost:8000/api/v1/docs |
| `worker` | Celery worker: assignment emails, overdue digest | — |
| `beat` | Celery beat: runs the digest on `OVERDUE_DIGEST_CRON` (UTC) | — |
| `mailpit` | Catches every email | http://localhost:8025 |
| `db`, `redis` | Postgres 18, Redis 8 | ports 5432, 6379 |

There are no demo users yet (Phase 6 adds `seed_demo`).
To run `manage.py runserver` at the same time, stop the `api` service or set `API_PORT` in `.env`.

## Run the checks

Needs [uv](https://docs.astral.sh/uv/) and Docker.

```sh
cp .env.example .env
docker compose up -d db redis
```

Linux / macOS:

```sh
make lint    # ruff, ruff format, mypy --strict, import-linter, missing migrations
make test    # pytest with a 90% coverage gate
```

Windows (same commands, without make):

```sh
cd backend
uv run ruff check . ; uv run ruff format --check . ; uv run mypy . ; uv run lint-imports --no-cache
uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test
uv run pytest
```

Health check (`200 ok`, `200 degraded` without Redis, `503 down` without Postgres):

```sh
cd backend
uv run --env-file ../.env python manage.py runserver
curl http://localhost:8000/api/v1/health
```

Pre-commit hooks: `uv run --directory backend pre-commit install`.

Celery outside Docker (from `backend/`, with `docker compose up -d db redis mailpit`). On Windows
the worker needs `--pool solo`, because Celery's default pool does not run on Windows:

```sh
uv run --env-file ../.env celery -A config.celery worker --loglevel info --pool solo
uv run --env-file ../.env celery -A config.celery beat --loglevel info
```

## API

With the server running (`uv run --env-file ../.env python manage.py runserver` in `backend/`,
after `uv run --env-file ../.env python manage.py migrate`):

- Swagger UI: http://localhost:8000/api/v1/docs (sign in with `POST /auth/login`, then "Authorize" with the access token)
- ReDoc: http://localhost:8000/api/v1/redoc
- The contract: [openapi.yaml](openapi.yaml), regenerated with `make schema`

Every error has the shape `{"code", "detail", "fields"}`.

## Docs

- [HANDOFF.md](HANDOFF.md): scope and rules
- [PLAN.md](PLAN.md): status, decisions and deviations
- [docs/adr/](docs/adr/): architecture decision records
- [docs/GENAI.md](docs/GENAI.md): how AI was used, validated and corrected
