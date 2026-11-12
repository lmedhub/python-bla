# Plan

Source of truth for scope: [HANDOFF.md](HANDOFF.md). This file tracks status and every
decision taken after HANDOFF was written.

## Phases

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Skeleton, uv, pre-commit, import-linter, CI skeleton, compose db/redis, health check, ADRs | in review (branch `phase-0`) |
| 1 | Domain + application, test-driven, no Django | not started |
| 2 | Infrastructure: custom User first, Task model, migrations, repositories | not started |
| 3 | Interfaces: auth, tasks API, throttling, OpenAPI, `openapi.yaml` | not started |
| 4 | Celery: assignment notification, overdue digest, Redis-down behavior | not started |
| 5 | Frontend | not started |
| 6 | Docker polish, seed, full CI, README, architecture doc | not started |
| 7 | Hardening: EXPLAIN, security review, console check, clean clone | not started |

## Decisions and deviations

| # | Decision | Where |
| --- | --- | --- |
| D1 | Django `>=6.1,<6.2`; Python 3.12 everywhere (local, CI, images) | `backend/pyproject.toml` |
| D2 | Keep simplejwt 5.5.1 although it only declares Django ≤5.2 (smoke test on 6.1.3 passed) | ADR 0003 |
| D3 | No django-celery-beat (caps Django <6.1; uv silently picks 2.1.0). Built-in beat + env cron | ADR 0004 |
| D4 | **django-filter dropped** (changes a locked decision): serializer → `TaskFilter` → repository | ADR 0006 |
| D5 | Throttles fail open when Redis is down; health reports `degraded` | ADR 0005 |
| D6 | Added deps: gunicorn, pre-commit, django-stubs, djangorestframework-stubs. Not used: freezegun (Clock port instead), django-redis (Django's built-in RedisCache) | `pyproject.toml` |
| D7 | `ATOMIC_REQUESTS=True`: one transaction per request instead of a Unit-of-Work port. Health opts out so a DB outage gives 503, not 500 | `config/settings/base.py` |
| D8 | "Today" is UTC, from the Clock port | ADR (Phase 1) |
| D9 | No `POST /tasks/{id}/complete`; the frontend uses `PATCH status=done` | — |
| D10 | Error shape for every status: `{"code", "detail", "fields"}` | Phase 3 |
| D11 | Shared code (health, error handler, pagination envelope) lives in `apps/core` | ADR 0001 |
| D12 | Test settings are self-contained, with local-only DB defaults (`taskmanager`/`taskmanager`), so `uv run pytest` needs no `.env`. local/prod read everything from the environment and refuse to start without `SECRET_KEY` (50+ chars) | `config/settings/` |
| D13 | `mypy --strict` for the whole backend (HANDOFF asks for domain + application only); relaxed only in tests | `pyproject.toml` |
| D14 | `CLAUDE.md` imports `HANDOFF.md` (`@HANDOFF.md`) instead of copying it to three files | `CLAUDE.md` |
| D15 | `docs/source/` (brief, job post) stays local and is gitignored | `.gitignore` |
| D16 | Makefile is for Linux/macOS/CI. The README lists the same commands for Windows | `Makefile`, README |
| D17 | "interfaces must not use the ORM" is enforced by ruff TID251, because import-linter cannot forbid `django.db` (an external subpackage) | `apps/*/interfaces/ruff.toml` |
| D18 | No migrations in Phase 0, so the custom User model can be the first migration in Phase 2 | — |
| D19 | No `.dockerignore` yet: there is no Dockerfile until the API image is built | Phase 6 |

## Known limits (so far)

- The database-down branch of `database_is_up()` is not covered by an automated test (it is
  checked by hand against a stopped container). The 503 response itself is tested.
- On Windows, a stopped Redis on `localhost` takes ~2 s to report down (IPv6 then IPv4 attempts).

## Open questions

- None right now.
