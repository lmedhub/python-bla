# For Linux, macOS and CI. On Windows, run the same commands directly (see README).
BACKEND := cd backend &&

.PHONY: up down test lint schema seed fresh

up:
	docker compose up -d --build

down:
	docker compose down

test:
	$(BACKEND) uv run pytest

lint:
	$(BACKEND) uv run ruff check .
	$(BACKEND) uv run ruff format --check .
	$(BACKEND) uv run mypy .
	$(BACKEND) uv run lint-imports --no-cache
	$(BACKEND) uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test

schema:
	$(BACKEND) uv run python manage.py spectacular --validate --fail-on-warn --file ../openapi.yaml --settings=config.settings.test

seed:
	@echo "seed: added in Phase 6" && exit 1

fresh:
	docker compose down -v
	docker compose up -d --build
