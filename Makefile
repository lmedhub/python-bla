# For Linux, macOS and CI. On Windows, run the same commands directly (see README).
BACKEND := cd backend &&
FRONTEND := cd frontend &&

.PHONY: up down test test-backend test-frontend lint lint-backend lint-frontend schema openapi types seed fresh

up:
	docker compose up -d --build

down:
	docker compose down

test: test-backend test-frontend

test-backend:
	$(BACKEND) uv run pytest

test-frontend:
	$(FRONTEND) npm test

lint: lint-backend lint-frontend

lint-backend:
	$(BACKEND) uv run ruff check .
	$(BACKEND) uv run ruff format --check .
	$(BACKEND) uv run mypy .
	$(BACKEND) uv run lint-imports --no-cache
	$(BACKEND) uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test

lint-frontend:
	$(FRONTEND) npm run lint
	$(FRONTEND) npm run typecheck

# openapi.yaml from the serializers, then the frontend's TypeScript types from openapi.yaml.
schema: openapi types

openapi:
	$(BACKEND) uv run python manage.py spectacular --validate --fail-on-warn --file ../openapi.yaml --settings=config.settings.test

types:
	$(FRONTEND) npm run generate:api

# Demo data, if the database has no users yet (the API container also does this on start).
seed:
	docker compose exec api python manage.py seed_demo

fresh:
	docker compose down -v
	docker compose up -d --build
