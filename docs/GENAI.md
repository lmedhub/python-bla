# GenAI usage log

How this project was built with an AI pair-programmer (Claude Code, in VS Code), how its
output was checked, and where it was wrong. Kept up to date phase by phase.

## 1. The prompts

**Instructions file.** [HANDOFF.md](../HANDOFF.md) holds the full scope, the locked stack, the
architecture rules, the phases and the definition of done. The agent reads it through
`CLAUDE.md`.

**Initial prompt** (sent once, before any code):

```
You are my pair-programmer for a senior Python/Django technical interview
exercise. A panel will review the repo and ask me to defend every decision,
so I must understand and be able to explain everything you write.

1. Read HANDOFF.md in the repo root completely. It is the source of truth for
   scope, stack, architecture, rules, phases and definition of done. Also read
   the brief and job post in docs/source/ if present.

2. Do NOT write application code yet. Your first task is Phase 0 planning only:
   a. Summarize the project back to me in under 15 lines, so I can confirm you
      understood the priorities (Clean Architecture, TDD, no console warnings,
      GenAI fluency).
   b. List gaps, contradictions or risky assumptions in HANDOFF.md. Be specific
      and propose a default for each. Check at least: Django 6 / DRF /
      simplejwt / drf-spectacular / django-filter version compatibility
      (verify against current docs or by resolving with uv, not from memory),
      the HttpOnly-refresh + in-memory-access token flow behind the nginx proxy,
      and how the Redis-down requirement interacts with transaction.on_commit.
   c. Propose the exact Phase 0 file tree and the import-linter contracts.
   d. Propose the first 5 ADR titles with a one-line decision each.
   e. Give me the Phase 0 plan as a checklist, with the verification commands
      you will run.

3. Then stop and wait. I will answer your questions and say "go".

Working rules for the whole project:
- TDD: failing test first, run it, show it fail, then implement. Commit red and
  green separately when practical.
- Never claim something passes unless you ran it; report real command output.
- No extra dependencies, features or abstractions beyond HANDOFF.md without asking.
- At the end of each phase: stop, report (changes, commands and results,
  deviations, open questions), and wait for "go".
- Keep PLAN.md current and keep docs/GENAI.md live, including a mistakes log
  of your own errors that tests, linters, import-linter or I caught. Log real
  ones only.
- If something is ambiguous, ask. Do not silently decide.
```

**Follow-ups so far**

- Answers to the 26 gaps the agent listed. Drop django-filter, throttles fail open, approve the
  extra dev dependencies, Makefile for Linux/macOS/CI only, one branch and PR per phase,
  no AI attribution in commits, then `go`.
- Per phase: `go. Phase N. Post your plan with the tests you will write first, then wait.`
- Phase 4: the plan offered two options for the worker and beat containers. The user answered
  `1. alternative`: build the backend image now instead of in Phase 6. The agent posted the extra
  scope (Dockerfile, compose services, CI build job) and waited for `go` again.
- Between phases: `npm token?` The agent diagnosed the E401 as an expired private work registry
  in the user-level `~/.npmrc`, and proposed a project `.npmrc` instead of refreshing the token.
- Phase 5: `go` on a plan with five questions (MSW, pages, browser check, CSS Modules, coverage
  gate); every recommended default was taken.
- Phase 6: `1a, go`: the user chose to answer a cookie-less refresh with 204, then approved the
  Phase 6 plan with its recommended defaults (demo app, no API host port, CI stack job).
- Sessions: from Phase 4, each session ended with the agent writing `SESSION_HANDOFF.md`
  (state, next steps, environment gotchas; not committed), and the next session started with
  only its name as the prompt. This kept each session's context small.
- Phase 7: `go` without answers to the plan's three questions. The agent said so and took its
  recommended defaults: commit the EXPLAIN data script, document unfixed base-image CVEs, and
  leave the user's own running stack alone (a scratch compose project instead).
- After Phase 7: `is there e2e test coverage?` The agent answered from the repo (API tests, MSW
  unit tests, the smoke test; the browser walk was a throwaway script), proposed a Playwright
  suite, and the user answered its two questions: no Swagger test, Chromium only.

## 2. Sample output

The planning step found real problems before any code was written. One example, quoted from
the agent's gap list:

> **django-celery-beat is a silent trap.** When I added it, uv did not fail. It quietly
> resolved to **2.1.0, a 2021 release** without the version cap. **Default:** don't use it.
> Celery's built-in `beat_schedule` with a crontab read from the `OVERDUE_DIGEST_CRON` env var
> meets "configurable schedule" with no extra dependency.

A representative code sample, the composition root, which is the only place where
interfaces may reach infrastructure ([container.py](../backend/apps/core/interfaces/container.py)):

```python
"""Composition root: the only interfaces module allowed to import infrastructure."""

from apps.core.application.health import HealthReport, check_health
from apps.core.infrastructure.probes import database_is_up, redis_is_up


def health_report() -> HealthReport:
    return check_health(database=database_is_up, redis=redis_is_up)
```

## 3. How output was validated

| Check | How |
| --- | --- |
| Versions | PyPI JSON for every package, then a real `uv pip compile` of the full set (not memory) |
| Django 6 compatibility | Smoke test on Django 6.1.3: simplejwt login, rotation, reuse rejected (401), blacklist; `spectacular --validate`; run with `-W default`, no deprecation warnings |
| TDD | Tests committed red first (`test:`), then the code (`feat:`). Phase 0 red: 4 `ModuleNotFoundError`s. From Phase 1, red commits include typed stubs, so the red is a behavior failure (e.g. "28 failed, 1 passed", "45 failed") and the pre-commit hooks still pass |
| Mutation check (Phase 2) | Infrastructure: update without the version filter → concurrency test fails; overdue without "not done" → 2 tests fail; removing `nulls_last=True` → **survived**, because Postgres already sorts NULLs last for ASC (documented, not hidden) |
| OpenAPI | `spectacular --validate --fail-on-warn` inside the test suite; it caught an enum that was not named and an operationId clash |
| Mutation check (Phase 3) | Missing `default=None` on the `overdue` filter, DRF validating the PATCH title before permission, links dropping filters: each caught by a test |
| Manual run (Phase 3) | Real server + Postgres + Redis: login (cookie flags), me, create, stale version 409, list, bad filter 400, no token 401, delete, docs pages |
| Migrations | `makemigrations --check` exits 1 after an unmigrated model change (tried on purpose, then reverted) |
| Mutation check | Phase 1: three business rules broken on purpose ("done" again moves `completed_at`, assignee may edit any field, past due date allowed on create). Each was caught by 2 tests (domain + use case), then reverted |
| Coverage | `--cov-fail-under=90` in `addopts`, so every run enforces it |
| Architecture | `lint-imports` 5/5 kept, then **negative tests**: a deliberate `import django` in `tasks.domain` and an interfaces→infrastructure import were both reported BROKEN, then reverted |
| ORM ban | Ruff TID251 negative test: `from django.db import models` in `interfaces/` is flagged |
| Types | `mypy --strict` with django-stubs and DRF stubs |
| Behavior | Health endpoint checked by hand against the real stack, with Redis then Postgres stopped: `200 ok` → `200 degraded` → `503 down` → `200 ok` |
| Makefile | `make -n` in a Linux container (no make on the Windows dev machine) |
| Real broker (Phase 4) | `CeleryNotifier` tests publish to the test Redis and decode the queued message (job name, IDs-only args); rollback leaves the queue empty |
| Redis down (Phase 4) | Automated: a broker on a closed port, both for the notifier and for a real committing request (`transaction=True`): 201, task saved, error logged, under 5 s. By hand: Redis container stopped under the full stack (see mistake 31) |
| Manual run (Phase 4) | `docker compose up --build`: API healthy as a non-root user (uid 10001); assign a task → worker log "sent" → email in Mailpit; beat with a per-minute cron → digest in Mailpit; Redis stopped → 201 and health `degraded`; Redis back → worker reconnects and sends |
| Real browser (Phase 5) | A throwaway Playwright script (scratchpad, not a project dependency) drove the installed Edge through sign in, filter, create, edit, complete, delete (Esc and focus on the dialog), reload, a 320 px viewport, Tab order and sign out, against both the dev server and the production build. All 13 steps passed. Console on the production build: one line, the signed-out refresh 401 (open question in PLAN) |
| Frontend tests (Phase 5) | Every test fails on a `console.error` / `console.warn` or an unexpected request; the suite runs in `America/Sao_Paulo` to catch date-only bugs |
| Mutation check (Phase 5) | Replacing the shared refresh (`??=`) with a fresh one per caller fails exactly the "refreshed only once for requests that fail together" test |
| Clean clone (Phase 6) | `git clone` into a scratch folder, `cp .env.example .env`, `docker compose up --build --wait` under a separate project name and ports: every service healthy in about 150 s, "Seeded 4 users and 30 tasks", smoke test 7/7, nginx as uid 101 |
| Real browser (Phase 6) | Same 13-step walk through nginx and the strict CSP: 0 console messages, 0 responses at or above 400 (the signed-out 401 is gone). Swagger UI: Authorize with a real token, then "Try it out" on `GET /users/me` answers 200, 0 console messages |
| Diagrams (Phase 6) | Every mermaid block in `docs/architecture.md` and the README parsed and rendered with mermaid 12.3.0 in a real browser before committing |
| Query plans (Phase 7) | `EXPLAIN (ANALYZE, BUFFERS)` on 100,000 seeded tasks, for the SQL captured from the real repository, before and after the index; the documented reproduction run again from scratch ([explain.md](explain.md)). A test checks the plan of the default list query |
| Image scan (Phase 7) | Trivy 0.76.1 on freshly built images, before and after the distro updates: web 13 → 0 HIGH/CRITICAL; backend left with only findings Debian has not fixed. `npm audit` with and without dev dependencies |
| Deploy check (Phase 7) | `manage.py check --deploy` with prod settings: 4 warnings, one fixed test-first (framing), three explained in [security-review.md](security-review.md) |
| Clean clone (Phase 7) | Fresh clone of `phase-7`, `.env.example`, separate project and ports: healthy in 57 s (cached layers), seeded, smoke test 7/7, both images non-root; headers, cookie flags and the login 429 checked with `curl` |
| Real browser (Phase 7) | The 13-step walk through nginx: 0 console messages, 0 page errors, 0 responses at or above 400. Swagger Authorize → `GET /users/me` 200, 0 console messages |
| Browser tests (after Phase 7) | The throwaway walk became 13 Playwright tests, run against a clean-clone stack on spare ports: 13 passed in 9.8 s, twice. They pass on code that already worked, so the console check was proven by breaking it: a temporary `console.warn("probe")` in one test made it fail with `"warning: probe"`. Frontend image rebuilt with the new files (`tsc -b` covers them); `npm audit` unchanged |
| TDD note (Phase 4) | The Redis-down API test passed already in its red commit, because it uses `CeleryNotifier`, finished one slice earlier. It is a guard, not a driver |

## 4. Mistakes log

Real ones only. Format: what happened, how it was found, how it was fixed.

| # | Phase | What happened | Found by | Fix |
| --- | --- | --- | --- | --- |
| 1 | 0 plan | A loop of `npm view … 2>/dev/null` printed empty versions; the redirect hid an npm auth error (E401) | Re-ran without hiding stderr | Read the public npm registry API directly; noted the broken npm token for the user |
| 2 | 0 | After installing uv, I guessed its location (`WinGet/Links`); it is not there, so `uv: command not found` | The shell error | Looked up the real winget package path |
| 3 | 0 | First green run: all tests passed but coverage was 87%. The env-driven settings modules (`local`, `prod`, `environment`) had no tests | Coverage gate (`--cov-fail-under=90`) | Added settings-load tests, including "refuses to start without SECRET_KEY / ALLOWED_HOSTS" (98%) |
| 4 | 0 | A line in the health view was over 100 characters | ruff E501 | Restructured the response code |
| 5 | 0 | Misread ruff SIM300: I thought it flagged `ENVIRONMENT[...]` and moved it to a variable; ruff actually flagged the upper-case `prod.SECRET_KEY` | Second ruff run, same error | Used ruff's suggested operand order |
| 6 | 0 | Added an import-linter `ignore_imports` rule for tasks tests importing users, for test code that does not exist yet | import-linter fails on ignore rules that match nothing | Removed it; it comes back when a real test needs it |
| 7 | 0 | CI used `astral-sh/setup-uv@v10`. I had checked the latest release (v10.3.3) but assumed a floating `v10` tag existed; it does not. The first CI run failed at "Set up job" | First CI run on PR #1 | Pinned both actions to commit SHAs (with the version in a comment), after checking the refs through the GitHub API |
| 8 | 1 | My plan said "commit the red tests", but red tests import modules that do not exist yet, and the pre-commit mypy hook rejected the commit | pre-commit (mypy `import-not-found`) | Red commits now include typed stubs that raise `NotImplementedError`. Hooks were not skipped |
| 9 | 1 | Named the shared exceptions `ValidationFailed`, `PermissionDenied`, `NotFound` as planned | ruff N818 (exception names should end in `Error`) | Renamed to `InvalidInputError`, `PermissionDeniedError`, `NotFoundError`, also avoiding Django/DRF name clashes (ADR 0008) |
| 10 | 1 | Test modules imported actor-id constants from `conftest.py`, which pytest does not intend to be imported | Self-review before commit | Moved them to `tests/application/constants.py` |
| 11 | 1 | Untyped fixture parameters made mypy see `Any` returned as `Task`; `date \| None \| Unset` unions; three test lines over 100 chars | mypy `no-any-return`, ruff RUF036 / E501 / PT012 | Typed the fixtures, put `None` last, split the lines |
| 12 | 1 | Wrote `if changes.assignee_id not in (None, previous_assignee_id)`: correct, but harder to explain than it needs to be | Self-review against HANDOFF "explain in one sentence" | Rewrote as an explicit `is not None and != previous` check |
| 13 | 2 | The first user model stub contained a pointless `__init__` override (dead code) | Self-review before generating the migration | Removed it |
| 14 | 2 | Wrapped factory_boy with `cast` and `type: ignore`, assuming it was untyped; it is generic (`DjangoModelFactory[T]`, `.create() -> T`) | mypy notes, then reading the factory_boy source | Typed the factory with generics: no cast, no ignore |
| 15 | 2 | Then removed the tests' `disallow_untyped_calls = false`, assuming generics covered everything; `Sequence` and `Password` are untyped | mypy `no-untyped-call` in the pre-commit hook | Restored the relaxation for tests only, with a comment saying why |
| 16 | 2 | A shell heredoc batch that wrote several files had broken quoting and ran nothing | bash syntax error | Wrote the files one by one with the editor tool |
| 17 | 2 | First `SystemClock` test accepted "today or yesterday": it would pass with a broken implementation | Self-review | Replaced with a deterministic subclass test (`now()` fixed at 23:59 UTC) |
| 18 | 2 | Reported the migration check's exit code through `\| tail`, which printed `exit=0` (the exit code of `tail`) | Noticed the output did not match the expected failure | Re-ran without the pipe: exit code 1 |
| 19 | 3 | Repeated mistake 10: API tests imported `NOW` from a `conftest.py` | Self-review before the first run | Imported it from `tests/application/constants.py` |
| 20 | 3 | The throttling module imported `APIView` at runtime; DRF imports that module while defining `APIView`, so every request failed with a circular `ImportError` | All throttle tests failed with the same import error | Import only under `TYPE_CHECKING` (it is needed for hints only) |
| 21 | 3 | My mutation helper reverted with `git checkout`, but two mutated files were uncommitted (one untracked): two mutations stayed in the working tree | Checked `git status` / the files after the run | Restored by hand and confirmed `git diff` against HEAD is empty. Mutate only committed files from now on |
| 22 | 3 | Named the OpenAPI enum by pointing `ENUM_NAME_OVERRIDES` at the `TaskStatus` StrEnum class; drf-spectacular did not match it | `--fail-on-warn` test (enum collision warning) | Pointed it at the exact `STATUS_CHOICES` list the serializers use |
| 23 | 3 | Two `APIView` GETs (list and detail) got the same operationId | `--fail-on-warn` test | Explicit `operation_id="tasks_list"` |
| 24 | 3 | Declared a serializer field called `fields`, which clashes with DRF's `Serializer.fields` | mypy | Built the Error component with `inline_serializer` |
| 25 | 3 | Passed `request.user.pk` (`int \| None`) to a use case expecting `int` | mypy `arg-type` | `current_user_id(request)` helper that raises 401 on `None`, with tests |
| 26 | 3 | Two more shell heredocs with triple quotes failed to parse | bash syntax error | Wrote the edit scripts to files and ran them |
| 27 | 3 | For the OpenAPI slice I ran red (6 failing) but did not commit the red state before adding annotations | Self-review of the commit list | Committed as one `feat:` commit and recorded it here, instead of faking a red commit |
| 28 | 3 | My OpenAPI test collected every parameter of the list operation, so adding a header broke a test about query parameters | The test run after the time zone change | Filtered the test to `in == "query"`, which is what it meant |
| 29 | 4 | Configured mail with `EMAIL_HOST`, `EMAIL_PORT` and `EMAIL_TIMEOUT`, from memory. Django 6.1 deprecates them for the new `MAILERS` setting | `filterwarnings = error` turned `RemovedInDjango2028Warning` into a failure on the first green run | Read Django's `MailersHandler` source, switched to `MAILERS` (`smtp_mailer()` helper) and adjusted the red test's assertion |
| 30 | 4 | The red `CeleryNotifier` tests had no `django_db` mark; `on_commit` needs a database connection even when nothing is written | "Database access not allowed" in the green run | Added the mark, with a comment saying why |
| 31 | 4 | The Redis-down plan relied on socket timeouts. In Docker, a stopped Redis container's name stops resolving, and that lookup took 8 s per attempt: `POST /tasks` took 16 s, health 8 s | Manual run against the real stack; the automated tests use `127.0.0.1`, which has no DNS step | `dns_opt: [timeout:1, attempts:1]` for the backend services: 2.1 s and 1.0 s, measured. Numbers in ADR 0005 |
| 32 | 4 | The plan said a failed publish "is logged", but Django's default logging prints `django.*` errors only when `DEBUG` is on, and the containers run with it off | Self-review of Django's `DEFAULT_LOGGING` before the Docker run, then confirmed in the container log | `LOGGING` sends every logger to stdout |
| 33 | 4 | gunicorn 27 opens a control socket under `$HOME`; the non-root user has no home, so it logged `Permission denied` at start | `docker compose logs api` | `--no-control-socket` (Docker manages the process) |
| 34 | 4 | Removed `LoggingNotifier` and its unit test, but missed a Phase 3 API test that asserted its log line | Full test run | Removed it; the new API test checks the queued job instead |
| 35 | 5 | Wrote MSW's `onUnhandledRequest` option from memory; MSW 3 renamed it `onUnhandledFrame` | tsc | Read MSW 3's type definitions, used the new name |
| 36 | 5 | First test config used Vitest's `onConsoleLog` to "fail on console warnings"; it only hides them | Self-review of what the option does, before the first run | Spy on `console.error` / `console.warn` and assert in `afterEach` that neither was called |
| 37 | 5 | MSW tries handlers in the order given to `server.use`. Three times I listed an always-matching handler before a `{ once: true }` one. Once a test passed for the wrong reason (no session ever started) | An unexpected pass in a red run; a failing green run; self-review | Put the one-time handler first, with a comment, and assert the intermediate state (the user's name shows before the login page) |
| 38 | 5 | The test's URL probe was an `<output>` element, which has the implicit role `status`, clashing with "Loading…" | Testing Library: multiple elements with role "status" | A plain `<div>` |
| 39 | 5 | Dates used the runtime's default locale, which is the operating system's (Portuguese here): output differed between machines | A test expecting "Nov 20, 2026" | Pass `navigator.language` explicitly |
| 40 | 5 | A form test typed a past due date to get a server error, but the date input's `min` blocks the submit first (jsdom enforces it like a browser) | Failing test | Use input the browser accepts and the server rejects |
| 41 | 5 | `autoFocus` on the dialog's Cancel button ran while the `<dialog>` was still closed, so nothing got focus | The focus test | Focus Cancel explicitly right after `showModal()` |
| 42 | 5 | Wrote a status filter handler that parsed a fake URL to validate one value: too clever to explain in one sentence | Self-review | An `isTaskStatus` type guard |
| 43 | 5 | Restored a mutation with PowerShell `Set-Content`, which rejected its arguments, so the mutation stayed in the file | The error message, then `grep` of the file | Restored with `sed`, checked the line, encoding and line endings, re-ran 30/30. Same lesson as mistake 21: verify the restore |
| 44 | 5 | Added frontend commands to `make lint` / `make test`, which CI's backend job runs without Node dependencies | Self-review before committing | Split targets (`lint-backend`, `test-frontend`, ...); CI's backend job calls the backend ones |
| 45 | 5 | No favicon: the browser's automatic `/favicon.ico` request logged a 404 | Browser check | An SVG favicon |
| 46 | 6 | The first request walkthrough named a view that does not exist (`TaskListView`) and drew the response leaving before the commit; with `ATOMIC_REQUESTS` the commit and the `on_commit` publish happen first | Self-review against the code before committing | `TaskCollectionView`, and commit → publish → response |
| 47 | 6 | Put a `;` inside a mermaid sequence-diagram message, where it ends the statement | Self-review, then all diagrams rendered with mermaid in a browser | A comma |
| 48 | 6 | A shell heredoc dropped a `\` line continuation in the CI workflow, joining two commands on one line | `cat -A` of the file after a suspicious `grep` | Rewrote the step as two plain lines with `export` |
| 49 | 6 | The Swagger UI check (throwaway script) assumed accessible names that Swagger UI 5 does not use, so it timed out three times | The script's own timeouts, a screenshot, a list of buttons | Swagger's own CSS classes and operation ids |
| 50 | 2 | The model comment (and this log, section 7) said `(status, due_date)` serves the default list order. It cannot: the order has no status filter, so Postgres read and sorted the whole table (14.7 ms for 10 rows of 100,000) | `EXPLAIN (ANALYZE)` on seeded data in Phase 7 | A `(due_date, id)` index (0.04 ms), a test on the real query plan, ADR 0015 |
| 51 | 7 | Again wrote Windows paths with `\` inside a shell heredoc; the heredoc dropped a backslash and the Python edit script did not parse | The `SyntaxError` | Forward slashes in paths. Same lesson as mistake 48 |
| 52 | 7 | Ran the smoke test against the clean clone without exporting `DEMO_PASSWORD`, so the sign-in step sent a blank password | The smoke test's own failure (400, "may not be blank") | Exported it from `.env`, as CI does: 7/7 |
| 53 | + | The e2e plan said Vitest only picks up `*.test.*` files, so the Playwright `*.spec.ts` files would stay out of the unit run. Vitest's default `include` matches `*.spec.*` too | Checking Vitest's defaults while wiring the config, before the first run | `exclude: [...configDefaults.exclude, "e2e/**"]` in `vite.config.ts` |
| 54 | + | Removed the temporary `console.warn` probe with `git checkout --`, which does nothing to an untracked file; the probe stayed in the spec | The editor's notice that the file still had the line, then `grep` | Deleted the line; `grep -c probe` returns 0 |

## 5. Findings that changed the plan

- django-celery-beat silently resolves to an old version on Django 6.1 (ADR 0004).
- PyJWT warns on HMAC keys under 32 bytes, so settings now require a 50+ character `SECRET_KEY`.
- With `ATOMIC_REQUESTS`, Django connects to the database before the view runs, so a DB outage
  would give a 500 from the health check. The health route opts out, and a test without DB
  access guards it.
- import-linter cannot forbid `django.db` (a subpackage of an external package), so ruff TID251 does it.
- import-linter's cache once reported a violation that had already been reverted (a false
  BROKEN). Pre-commit runs it with `--no-cache`.
- The in-memory fake repository deliberately does **not** re-implement filtering: copying the
  filter logic into a fake would only test the copy. `ListTasks` is checked for what it passes
  (filter, page, `clock.today()`); real filtering is tested against Postgres in Phase 2.
- The fake repository stores **copies** (like a database), so a test can prove that a rejected
  update saved nothing.
- Postgres sorts NULLs last for `ASC` by default, so the explicit `nulls_last=True` is an
  equivalent mutant there (no test can detect its removal). Kept for intent, and logged as a limit.
- Django already creates indexes for foreign keys (`assignee_id`, `created_by_id`), confirmed with
  `sqlmigrate`. Only the composite `(status, due_date)` index is declared.
- `get_user_model()` lets tasks check users without importing the users feature (ADR 0009).
- simplejwt 5.5.1 returns a 500 when a refresh token belongs to a deleted user (unhandled
  `DoesNotExist`); found by reading its source, now a tested 401.
- DRF turns 401 into 403 for views without authenticators; found in DRF's source before
  writing the login views.
- DRF reads a missing boolean query parameter as `False`; `overdue` would have silently
  filtered every list. `default=None` plus a test.
- drf-spectacular loads Swagger UI / ReDoc from `@latest` by default; pinned instead.
- The manual run created a task due "today" at 21:21 local time, 00:21 UTC the next day, and the
  server rejected it as past. That is the ADR 0007 limit happening for real. The user chose to
  send the browser's time zone (`X-Timezone`). Because the use cases already depended on a
  `Clock` port, the fix was a per-request `ZonedClock` in infrastructure plus header parsing;
  no domain or use case code changed.

- Phase 4: Django 6.1 replaces the `EMAIL_*` settings with `MAILERS` (mistake 29).
- Phase 4: socket timeouts do not bound DNS lookups. Stopping a container in compose removes its
  name, and the default resolver took 8 s to give up (mistake 31, ADR 0005).
- Phase 4: the slim Python image already ships time zone data, which closes the Phase 6
  carry-over about `tzdata`.
- Phase 4: the draft plan wrapped jobs in `transaction.atomic`. Writing the use case showed it
  is not needed: "check, send, record" never needs two statements to commit together, and SMTP
  cannot join a database transaction anyway (ADR 0012).
- Phase 5: TypeScript 7 is out, but typescript-eslint (below 6.1) and openapi-typescript (5.x)
  do not support it, so the frontend uses 5.9.3. Found by reading peer dependencies before installing.
- Phase 5: the user-level `~/.npmrc` points every npm command at a private work registry. A
  project `.npmrc` keeps those URLs out of `package-lock.json` (checked: 328 entries, all
  `registry.npmjs.org`).
- Phase 5: rotating refresh tokens plus React StrictMode's double effects would sign the user
  out at startup; a single shared refresh avoids it (ADR 0013).
- Phase 5: React 19.3's types deprecate `FormEvent` (`SubmitEvent` for forms), flagged by
  typescript-eslint's `no-deprecated`.
- Phase 5: on Windows, Vitest fails with "failed to find the runner" when the shell's drive letter
  is lower case (`c:\`), because modules load twice. Running from `C:\` works (README).
- Phase 5: jsdom has no `<dialog>.showModal()`.
- Phase 5: browsers print every 4xx response in the console, so an expected 401 still shows as an
  error line (PLAN open question).
- Phase 6: a status code can remove a console error. "Nobody is signed in" is not a failure, so
  refresh without a cookie now says 204; a present but bad cookie is still 401.
- Phase 6: exposing the API port next to nginx would let any client send its own
  `X-Forwarded-For` and pick its rate-limit bucket; only nginx is published.
- Phase 6: demo data cannot go through the use cases (past due dates are refused, emails would
  be sent), so the seed writes rows directly, in its own app that nothing imports.
- Phase 7: the index HANDOFF asked for, `(status, due_date)`, cannot serve the default list
  order, so the main page sorted the whole table. `EXPLAIN` on 100,000 rows showed it;
  `(due_date, id)` fixed it, and the partial index HANDOFF suggested was measured and rejected.
- Phase 7: a base image tag can be weeks behind its distro's security fixes. No newer tag
  existed, so the runtime images upgrade their packages at build time.
- After Phase 7: two server rules shaped the browser tests. The login throttle (5 a minute)
  and the rotating refresh token rule out the usual "sign in once, save the session" setup, so
  each spec file signs in once and keeps its page.
- Phase 4: Celery's `send_task` by name keeps the layers clean. Infrastructure publishes a name;
  only the worker imports the job module.

## 6. Edge cases, auth and validation decisions

See ADRs 0003 (JWT), 0005 (Redis down), 0006 (filters), 0007 (due date) and 0008 (errors).

| Case | Decision | Test |
| --- | --- | --- |
| Blank / whitespace title | 400 on `title`; title trimmed; 200 chars max, measured after trimming | `test_rules.py` |
| Past due date | Rejected on create, allowed on update | `test_rules.py`, `test_update_task.py` |
| Unknown or inactive assignee | 400 on `assignee`, not 409 | `test_create_task.py`, `test_update_task.py` |
| "done" sent twice | Keeps the first `completed_at` | `test_task.py`, `test_update_task.py` |
| Assignee edits title | 403, nothing saved | `test_update_task.py` |
| Stranger sends invalid data | 403 before any 400 | `test_update_task.py` |
| Assignee re-sends unchanged fields | Allowed (only real changes count) | `test_update_task.py` |
| Reassign / same assignee / unassign | Notify only a new, non-null assignee | `test_update_task.py` |
| `page_size` 0 or 101, page 0 | 400 on that field; both fields reported together | `test_queries.py` |
| Page past the end | Empty items, real total, no next page | `test_queries.py`, `test_task_find.py` |
| Two users save the same task | Second save gets `ConflictError` (409); first write kept | `test_task_repository.py` |
| Client edits a stale copy | `expected_version` mismatch → 409, nothing saved; 403 still wins | `test_optimistic_locking.py` |
| Email letter case | Stored lowercase (DB check); login with "Carol@Example.com" works | `test_user_model.py` |
| Inactive user logs in | Rejected | `test_user_model.py` |
| Assignee user deleted | Their tasks become unassigned; creators cannot be deleted | `test_task_model.py` |
| Overdue filter and tasks without due date | `overdue=false` includes them | `test_task_find.py` |
| Login failures | Unknown email, wrong password and inactive user: same 401, same message | `test_auth_api.py` |
| Refresh token reused / tampered / expired / deleted user | 401 (never 500) | `test_auth_api.py` |
| Access token expired / tampered / wrong scheme / user deactivated | 401 with `WWW-Authenticate: Bearer` | `test_users_api.py` |
| 401 vs 403 | No token is 401; signed in but not allowed is 403 | `test_tasks_api.py` |
| Rate limits | 6th login, 21st anonymous, 101st signed-in call: 429 with `Retry-After`; separate limits per client IP behind a proxy | `test_throttling.py` |
| Redis down | Login and task list still 200; a warning is logged | `test_throttling.py` |
| `overdue` not sent | No filtering (DRF's default would be `False`) | `test_task_list_api.py` |
| Evening west of UTC | Due "today" accepted and not overdue for a caller sending `X-Timezone: America/Sao_Paulo` at 00:21 UTC; without the header UTC decides | `test_time_zone_api.py` |
| Request rolls back after assigning | No email queued | `test_celery_notifier.py` |
| Job runs after the task was deleted / reassigned / assignee deactivated | Skipped, logged with the reason | `test_notify_assignment.py` |
| Same job delivered twice | One email (key = Celery message id) | `test_notify_assignment.py`, `test_jobs.py` |
| Reassigned A → B → A | A gets two emails (two messages) | `test_notify_assignment.py` |
| Mail server down | Job fails, nothing recorded, so the retry sends | `test_notify_assignment.py`, `test_jobs.py` |
| Digest runs twice the same day | Second run sends nothing; next day sends again | `test_overdue_digest.py` |
| Overdue task with no assignee | Nobody is emailed | `test_overdue_digest.py` |
| Redis down when assigning | 201, task saved, error logged, under 5 s | `test_assignment_notification_api.py` |
| Bad `OVERDUE_DIGEST_CRON` | Startup fails with the variable's name | `test_env.py`, `test_settings.py` |
| Due date shown west of UTC | `"2026-11-12"` shows as 12 Nov in Sao Paulo, not 11 Nov | `dates.test.ts`, suite runs in `America/Sao_Paulo` |
| Hand-edited URL (`status=urgent`, `page=-2`) | Ignored, never sent to the API | `filters.test.ts` |
| Filter changed on page 3 | Back to page 1 | `TaskListPage.test.tsx` |
| Shared link past the last page | "This page is empty" with a way back | `TaskListPage.test.tsx` |
| Parallel 401s | One refresh, then each request retried once | `session.test.ts` |
| Refresh fails mid-session | Login page; cached data cleared | `session.test.ts`, `TaskListPage.test.tsx` |
| Logout when the server is unreachable | Signed out locally anyway | `session.test.ts` |
| Proxy error page (HTML, not JSON) | Generic message with the status, no crash | `errors.test.ts` |
| 429 on login | "Try again in N seconds" from `Retry-After` | `auth.test.tsx` |
| Edit after someone else's change | 409 → message, form reloaded with their version | `TaskFormPage.test.tsx` |
| Non-creator opens the edit URL | Explanation, no form | `TaskFormPage.test.tsx` |
| Assignee / stranger in the list | Edit and Delete disabled; status only for the assignee | `TaskActions.test.tsx` |
| Delete | Confirmation, focus on Cancel; failure keeps the dialog open with the reason | `TaskActions.test.tsx` |
| Signed-out page load | Refresh without a cookie: 204, nothing in the console | `test_auth_api.py`, `session.test.ts`, smoke test |
| Seed on a database with users | Nothing changes | `test_seed_demo.py` |
| Bad `REFRESH_COOKIE_SECURE` value | Startup fails with the variable's name | `test_env.py` |
| Bad `X-Timezone` | Unknown, path-like (`../../etc/passwd`), offset (`UTC+3`), blank or folder (`America`) names give 400 on the header, never 500 | `test_requests.py` |

## 7. Performance and idiomatic quality

- **Query count**: the task list is exactly 2 queries (count + page) for any number of rows,
  asserted with `django_assert_num_queries(2)` over 15 tasks. The domain `Task` holds ids, not
  related objects, so an N+1 cannot happen in the repository.
- **Indexes**: `(due_date, id)` matches the list order, so every page is read from the index
  and stops at the `LIMIT`; `(status, due_date)` serves the status count; Django adds the foreign
  key indexes. Measured on 100,000 tasks, before and after ([explain.md](explain.md), ADR 0015).
  A partial index for overdue tasks was measured and rejected (under 1 ms gained).
- **Constraints in the database**, not only in Python: status, title and `completed_at` rules
  hold even for raw SQL or a future bulk script.
- **Locking**: optimistic, with a single conditional `UPDATE`, so reads never block (ADR 0010).
- **Digest queries**: overdue tasks in 1 query, every recipient in 1 query (`pk__in`), both asserted
  with `django_assert_num_queries`. The sent-log check is one small indexed query per assignee.
- **Frontend bundle**: 319 kB JavaScript, 100 kB gzipped (React, React Router, TanStack Query,
  openapi-fetch and the app). The list keeps the previous page on screen while the next loads.
- **API list**: the number of queries is the same for 3 or 15 tasks (compared with
  `CaptureQueriesContext`): the JWT user lookup, count, page, and the request savepoints.
