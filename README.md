# Task Manager

A task manager API (Django 6.1 + DRF + PostgreSQL + Celery/Redis) with a React frontend,
built as a technical interview exercise.

**Status:** Phase 0 (skeleton, tooling and health check). See [PLAN.md](PLAN.md).
The full setup guide, demo credentials and architecture summary come in Phase 6.

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

## Docs

- [HANDOFF.md](HANDOFF.md): scope and rules
- [PLAN.md](PLAN.md): status, decisions and deviations
- [docs/adr/](docs/adr/): architecture decision records
- [docs/GENAI.md](docs/GENAI.md): how AI was used, validated and corrected
