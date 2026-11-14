# Plan

Source of truth for scope: [HANDOFF.md](HANDOFF.md). This file tracks status and every
decision taken after HANDOFF was written.

## Phases

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Skeleton, uv, pre-commit, import-linter, CI skeleton, compose db/redis, health check, ADRs | done (PR #1) |
| 1 | Domain + application, test-driven, no Django | done (PR #2) |
| 2 | Infrastructure: custom User first, Task model, migrations, repositories | done (PR #3) |
| 3 | Interfaces: auth, tasks API, throttling, OpenAPI, `openapi.yaml` | done (PR #4) |
| 4 | Celery: assignment notification, overdue digest, Redis-down behavior; backend image and compose services (moved from 6) | done (PR #5) |
| 5 | Frontend: generated types, auth, list/filters/URL state, forms, tests | done (PR #6) |
| 6 | nginx + frontend image, seed, full CI, README, architecture doc; refresh without cookie → 204 | done (PR #7) |
| 7 | Hardening: EXPLAIN, security review, console check, clean clone | in progress (branch `phase-7`) |

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
| D8 | "Today" is UTC, from the Clock port. Due date may not be in the past on create; any date on update | ADR 0007 |
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
| D20 | Red commits contain **typed stubs** (`raise NotImplementedError`), so tests fail on behavior and the pre-commit mypy hook still passes. Hooks are never skipped | `docs/GENAI.md` |
| D21 | Shared errors `InvalidInputError` (400), `PermissionDeniedError` (403), `NotFoundError` (404) in `apps/core/domain`. Renamed from the planned `ValidationFailed` etc. (ruff N818, and no clash with Django/DRF names) | ADR 0008 |
| D22 | A page past the end returns 200 with empty `results` and the real `count` | `application/queries.py` |
| D23 | The assignee's permission is judged on fields that actually **change**, so re-sending an unchanged title with a status change is allowed. Permission is checked before validation | `domain/task.py`, ADR 0008 |
| D24 | `GET /users` returns all active users without pagination (assignee picker) | Phase 3 |
| D25 | The overdue digest use case is built in Phase 4, with Celery (done) | `tasks/application/notifications.py` |
| D26 | Tasks checks assignees with `get_user_model()` in `tasks.infrastructure` (option b), so it never imports users | ADR 0009 |
| D27 | Emails stored lowercase (domain `normalize_email` + DB check constraint); login lookup is case-insensitive | ADR 0009 |
| D28 | **Optimistic locking** on task updates (`version` column, `UPDATE ... WHERE version = ?`, 409 `ConflictError`) plus optional `expected_version` in the use case. Replaces "last write wins" | ADR 0010 |
| D29 | Task timestamps come from the `Clock` port (no `auto_now`), so tests assert exact times | `tasks/infrastructure/repositories.py` |
| D30 | Database check constraints mirror domain invariants: valid status, non-empty title, `completed_at` set iff done | `tasks/infrastructure/models.py` |
| D31 | `created_by` is PROTECT (users are deactivated, not deleted); `assignee` is SET_NULL | `tasks/infrastructure/models.py` |
| D32 | API returns user ids only; the frontend maps names from `GET /users` | Phase 3 / 5 |
| D33 | `make lint` / CI fail when a model change has no migration (`makemigrations --check`) | `Makefile` |
| D34 | Clients send `version` in the PATCH body (not `If-Match`) | ADR 0011 |
| D35 | **No per-task permission flags** in responses (user feedback). Login/refresh return the user; the frontend derives permissions from `created_by` / `assignee` | ADR 0011 |
| D36 | Refresh returns `{access, user}`, same as login | ADR 0003, 0011 |
| D37 | Relative pagination links | ADR 0011 |
| D38 | Swagger UI / ReDoc assets pinned (`swagger-ui-dist@5.34.0`, `redoc@2.5.4`), loaded from jsdelivr | ADR 0011 |
| D39 | `NUM_PROXIES` read from the environment (1 behind nginx) | `config/settings/environment.py` |
| D40 | Phase 3 notifier logged only (`LoggingNotifier`); replaced by `CeleryNotifier` in Phase 4 and removed | `tasks/interfaces/container.py` |
| D41 | The pagination envelope lives in `tasks/interfaces` (only tasks paginate), not `core` as D11 planned | `tasks/interfaces/pagination.py` |
| D42 | **"Today" is the caller's date** from the `X-Timezone` header (IANA name, UTC if absent), via a per-request `ZonedClock`. Chosen by the user (option b) after the manual run showed the UTC problem | ADR 0007 (amended) |
| D43 | **Backend image and the `api`, `worker`, `beat`, `mailpit` compose services moved from Phase 6 to Phase 4** (user's choice), plus a CI job that builds the image. nginx, the frontend image and seeding stay in Phase 6 | `backend/Dockerfile`, `docker-compose.yml` |
| D44 | Mail is configured with Django 6.1's `MAILERS` setting; the `EMAIL_*` settings are deprecated in 6.1 | `config/settings/base.py` |
| D45 | Celery jobs live in `tasks/interfaces/jobs.py` (entry points, like views). `CeleryNotifier` publishes by job name, so infrastructure never imports interfaces; the container re-exports the names | ADR 0012 |
| D46 | Idempotent jobs through a `SentNotification` table with a unique key: "check, send, record", at-least-once (a crash can duplicate one email, never lose one) | ADR 0012 |
| D47 | The worker does **not** wrap jobs in `transaction.atomic` (the Phase 4 draft said it would): check, send, record needs no multi-statement atomicity, and a transaction cannot include SMTP | ADR 0012 |
| D48 | The overdue digest uses the UTC date (no caller, so no `X-Timezone`) | ADR 0012 |
| D49 | mypy `disallow_untyped_decorators = false` for `apps.*.interfaces.jobs` only: Celery has no type hints. No `celery-types` stub package added | `pyproject.toml` |
| D50 | `LOGGING` sends every logger to stdout at INFO, so Django's own errors show with `DEBUG` off | `config/settings/base.py` |
| D51 | Backend containers use `dns_opt: [timeout:1, attempts:1]`: with Redis stopped, its name lookup took 8 s and bypassed the socket timeouts | ADR 0005 |
| D52 | gunicorn runs with `--no-control-socket` (new in gunicorn 25+, writes under `$HOME`, which the app user has not got; Docker manages the process) | `backend/docker/start-api.sh` |
| D53 | Base image `python:3.12.16-slim-trixie` already has time zone data (checked `America/Sao_Paulo`), so no `tzdata` package. uv `0.13.7` image in the build stage | `backend/Dockerfile` |
| D54 | Frontend versions pinned exactly. **TypeScript 5.9.3, not 7.0**: typescript-eslint and openapi-typescript do not support 7 yet | ADR 0013 |
| D55 | `frontend/.npmrc` pins the public npm registry: the user-level `~/.npmrc` points at a private work registry, whose URLs would land in `package-lock.json` | ADR 0013 |
| D56 | MSW for API fakes in tests (not in HANDOFF; approved for Phase 5). Tests fail on any console warning or error and on unexpected requests | ADR 0013 |
| D57 | Create and edit are pages (`/tasks/new`, `/tasks/:id/edit`); delete confirmation is a native `<dialog>` | ADR 0013 |
| D58 | CSS Modules plus one global stylesheet; no UI kit | ADR 0013 |
| D59 | No frontend coverage gate (HANDOFF does not ask for one; avoids another dependency) | — |
| D60 | One refresh in flight at a time, shared by every caller: refresh tokens rotate, so parallel refreshes would sign the user out | ADR 0013 |
| D61 | The status toggle sends no `version`; the edit form does | ADR 0013 |
| D62 | Dates are formatted in the browser's language (`navigator.language`), not the OS default | `src/lib/dates.ts` |
| D63 | Makefile: `lint`, `test`, `schema` cover both sides; `lint-backend`, `test-frontend`, `openapi`, `types` and so on cover one. CI's backend job uses the backend-only targets | `Makefile` |
| D64 | `POST /auth/refresh` without any cookie answers **204** (no session), not 401, so a signed-out visit logs nothing in the console. A bad cookie is still 401 (user's choice "1a") | ADR 0003 (amended) |
| D65 | `REFRESH_COOKIE_SECURE` comes from the environment, default `true` | `config/settings/environment.py` |
| D66 | Demo data: `seed_demo` in its own `apps/demo` app (nothing may import it), only on an empty database, at startup only with `SEED_DEMO=true`; password from `DEMO_PASSWORD` | ADR 0014 |
| D67 | nginx (`web`, non-root) is the only entry point; `api` has no host port; `NUM_PROXIES=1` in compose | ADR 0014 |
| D68 | CSP and security headers on the app's pages only; Swagger UI under `/api/` is left to Django because it loads its scripts from a CDN | `frontend/nginx.conf` |
| D69 | CI's `docker` job starts the whole stack from a clean checkout with `.env.example` and runs `scripts/smoke_test.py` through nginx. Schemathesis (optional in HANDOFF) is not added | `.github/workflows/ci.yml` |
| D70 | The smoke test is plain Python (standard library), so it runs on the CI runner and on Windows without `jq` | `scripts/smoke_test.py` |
| D71 | **New index `(due_date, id)`** for the list order (EXPLAIN: full sort before). No partial index for overdue (measured, under 1 ms gained). The data script is committed so the numbers can be reproduced | ADR 0015, `docs/explain.md`, `scripts/explain_list.sql` |
| D72 | Runtime images apply their distro's security updates at build time (`apt-get upgrade`, `apk upgrade`): no newer base tag had the fixes. Debian CVEs with no fix are documented, not worked around. Scanned with Trivy (Docker Scout needs a login) | `backend/Dockerfile`, `frontend/Dockerfile`, `docs/security-review.md` |
| D73 | Django sends `X-Frame-Options: DENY` (Swagger UI and ReDoc are outside nginx's CSP). CSRF middleware, HSTS and the HTTPS redirect stay off, for the reasons in the security review | `config/settings/base.py`, `docs/security-review.md` |

## Known limits (so far)

- The database-down branch of `database_is_up()` is not covered by an automated test (it is
  checked by hand against a stopped container). The 503 response itself is tested.
- On Windows, a stopped Redis on `localhost` takes ~2 s to report down (IPv6 then IPv4 attempts).
- Clients that do not send `X-Timezone` get UTC dates (ADR 0007).
- Use cases report only the first failing business rule (title, then due date, then assignee).
- `GET /users` is unpaginated; fine for a team, not for a large organisation.
- Deleting a task is not version-checked (ADR 0010).
- While Redis is down, assignment emails are lost (logged with task and user ids), and each request
  that touches Redis is about 1 s slower per touch (DNS lookup limit). A transactional outbox would
  remove the loss (ADR 0012).
- A worker crash between sending and recording an email can send it twice (ADR 0012).
- `SentNotification` grows by one row per email; no cleanup job yet.
- Celery beat has no healthcheck; the worker's (`inspect ping`) shows "unhealthy" for up to 30 s
  after a Redis outage ends.
- The backend image has 47 HIGH findings (11 CVEs) that Debian has not fixed; none is reachable
  from the app (docs/security-review.md).
- No HSTS or HTTPS redirect: TLS is expected to end at a load balancer in front of the stack.
- `npm audit` reports a moderate advisory in `minimatch` (GHSA-g3hv-75wg-m249), reached only through
  ESLint and typescript-eslint; `npm audit --omit=dev` is clean. typescript-eslint has no
  release with a fixed `minimatch` yet.
- jsdom has no `<dialog>.showModal()`: tests stub it; focus and Esc are checked in a real browser.
- On Windows, Vitest must run from an upper-case drive path (README).
- The demo password is in `.env.example` and the README; it protects demo data only.
- The digest uses the UTC date; a scheduled job has no caller time zone.
- Every list request runs `COUNT(*)` over the matching rows, and deep pages walk the skipped rows
  (`OFFSET`): 9 ms and 23 ms at 100,000 tasks. Keyset pagination is the next step if it matters
  (docs/explain.md).
- `nulls_last=True` in the list order cannot be tested on Postgres, which already sorts NULLs last
  for ascending order (an "equivalent mutant"). It is kept for intent and portability.

## Open questions

- None open. (The signed-out refresh 401 was resolved by D64; the `Secure` cookie by D65.)
