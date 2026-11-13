# 0004. Celery's built-in beat scheduler, not django-celery-beat

- Status: accepted, implemented in Phase 4
- Date: 2026-11-11

## Context

The overdue digest runs daily, on a configurable schedule. django-celery-beat is the
usual way to store schedules in the database.

## Decision

Use Celery's built-in `beat_schedule`, with a crontab read from `OVERDUE_DIGEST_CRON`.

- django-celery-beat 2.9.0 requires `Django<6.1`.
- Worse, adding it does not fail: uv quietly resolves **django-celery-beat 2.1.0**
  (a 2021 release without that upper bound). We saw this in a real `uv pip compile`.
- One job with an env-configured schedule does not need a database-backed scheduler.

## Implementation (Phase 4)

- `OVERDUE_DIGEST_CRON` is a standard 5-field cron expression, default `0 8 * * *`, in UTC
  (`CELERY_TIMEZONE`). `config.env.cron()` checks it with `crontab.from_string`, so a bad
  value stops startup with a clear message instead of failing at night.
- The schedule names the job by its string name; a test checks that the name is a registered job.
- Beat runs as its own compose service, exactly one instance (two would send every digest
  twice, although the digest's sent log would then skip the duplicates, ADR 0012). Its state
  file goes to `/tmp`, because the app user cannot write to the code directory.

## Consequences

- Changing the schedule needs a restart of `beat`, not an admin edit. That is fine for one job.
- One less dependency and no extra migrations.
