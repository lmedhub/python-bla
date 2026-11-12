# 0001. Feature-first Clean Architecture, enforced by tools

- Status: accepted
- Date: 2026-11-11

## Context

The brief grades separation of concerns. Layer rules written only in a README
erode quickly, especially with generated code.

## Decision

- Each feature (`tasks`, `users`, plus a small `core`) has four layers:
  `domain` → `application` → `infrastructure` / `interfaces`.
- `domain` and `application` are plain Python. Ports are `typing.Protocol`s.
- The Django app for a feature **is** its infrastructure layer
  (`apps.<feature>.infrastructure.apps.<Feature>Config`, with a short label like `tasks`).
  So `models.py` and `migrations/` sit inside `infrastructure/` with no tricks.
- The composition root is `interfaces/container.py`. It is the only interfaces
  module allowed to import infrastructure.
- Foreign keys to users use the `settings.AUTH_USER_MODEL` string, so `tasks` never
  imports `users.infrastructure`.
- The rules are checked by **import-linter** (5 contracts in `backend/pyproject.toml`)
  and by **ruff TID251** (no `django.db.models` / `connection` in `interfaces/`).
  Both run in pre-commit and CI.

## Consequences

- A broken rule fails the build. This was shown with a deliberate bad import
  (see `docs/GENAI.md`).
- import-linter cannot forbid a subpackage of an external package (`django.db`),
  so that one rule lives in ruff instead.
- More files than a typical Django app. Each one has a single job.
