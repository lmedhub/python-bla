# 0012. Background notifications: at-least-once delivery with a sent log

- Status: accepted (Phase 4)
- Date: 2026-11-13

## Context

Assigning a task sends an email, and a daily job emails each assignee their overdue tasks.
Email is slow and can fail, so it runs in a Celery worker, not in the request. Celery with
Redis delivers a job **at least once**: a retry, or a worker that dies before acknowledging,
runs the same job again. HANDOFF asks for idempotent jobs, retries with backoff, IDs-only
payloads, and a request that still succeeds when Redis is down (ADR 0005).

## Decision

**Sending side (inside the request)**
- The use cases depend on the `Notifier` port. `CeleryNotifier` implements it with
  `transaction.on_commit(..., robust=True)`: a rolled-back request sends nothing, the worker
  always finds the committed task, and a publish error is logged instead of failing the request.
- It publishes by job **name** (`send_task("tasks.notify_assignment", ...)`), so infrastructure
  never imports the job module. The payload is `[task_id, assignee_id]` only.

**Worker side**
- Jobs live in `tasks/interfaces/jobs.py`: like views, they are entry points and only call
  use cases from the composition root.
- `NotifyAssignment` re-reads the task. It sends nothing if the task was deleted, reassigned
  to someone else, or the assignee was deactivated in the meantime.
- **Idempotency: check, send, record.** Every email has a key, stored in `SentNotification`
  (unique column):
  - assignment: `assignment:<Celery message id>`. The id is the same on every retry of one
    job and different for each new assignment, so reassigning A → B → A emails A twice.
  - digest: `digest:<user id>:<date>`, so one digest per person per day however often the
    job runs, and a retried digest skips the people already emailed.
- If the worker crashes after sending but before recording, the retry sends one duplicate.
  No email is ever lost once the job is queued. We accept that trade-off.
- Retries: `autoretry_for=(OSError,)` (smtplib errors and refused connections are
  `OSError`s), exponential backoff with jitter, at most 5 retries. `acks_late=True`, so a
  job is acknowledged only after it finishes.
- No result backend: nothing reads job results.

**Digest**
- `SendOverdueDigests` groups overdue tasks by assignee and sends one email each.
- A scheduled job has no caller, so "today" is the UTC date (unlike requests, ADR 0007).

## Alternatives

- **Wrap check, send and record in one database transaction.** It still cannot make SMTP
  and Postgres commit together, and it holds a transaction open while talking to a mail
  server. It changes nothing important.
- **Redis `SET NX` with an expiry as the sent log.** It needs no migration, but the
  record disappears after the expiry, and Redis is the component most likely to be down.
- **Transactional outbox** (write the notification to a table in the request's transaction;
  a relay publishes it later). It would also survive Redis being down at request time. It is
  the right next step if lost notifications matter. For this scope, the logged loss is
  acceptable (ADR 0005).

## Consequences

- While Redis is down, assignment emails are lost (each one is logged with its task and
  user ids). The task itself is saved.
- A rare duplicate email is possible; a missing one (after queuing) is not.
- `SentNotification` grows by one row per email. A periodic cleanup is a future task.
