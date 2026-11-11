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
| TDD | Tests committed red first (`test:`), then the code (`feat:`). Red output: 4 `ModuleNotFoundError`s |
| Coverage | `--cov-fail-under=90` in `addopts`, so every run enforces it |
| Architecture | `lint-imports` 5/5 kept, then **negative tests**: a deliberate `import django` in `tasks.domain` and an interfaces→infrastructure import were both reported BROKEN, then reverted |
| ORM ban | Ruff TID251 negative test: `from django.db import models` in `interfaces/` is flagged |
| Types | `mypy --strict` with django-stubs and DRF stubs |
| Behavior | Health endpoint checked by hand against the real stack, with Redis then Postgres stopped: `200 ok` → `200 degraded` → `503 down` → `200 ok` |
| Makefile | `make -n` in a Linux container (no make on the Windows dev machine) |

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

## 5. Findings that changed the plan

- django-celery-beat silently resolves to an old version on Django 6.1 (ADR 0004).
- PyJWT warns on HMAC keys under 32 bytes, so settings now require a 50+ character `SECRET_KEY`.
- With `ATOMIC_REQUESTS`, Django connects to the database before the view runs, so a DB outage
  would give a 500 from the health check. The health route opts out, and a test without DB
  access guards it.
- import-linter cannot forbid `django.db` (a subpackage of an external package), so ruff TID251 does it.
- import-linter's cache once reported a violation that had already been reverted (a false
  BROKEN). Pre-commit runs it with `--no-cache`.

## 6. Edge cases, auth and validation decisions

See ADRs 0003 (JWT), 0005 (Redis down) and 0006 (filters). Later phases add rows here.

## 7. Performance and idiomatic quality

To be filled from Phase 2 (query counts with `django_assert_num_queries`, `EXPLAIN` evidence).
