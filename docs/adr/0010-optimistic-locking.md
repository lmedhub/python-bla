# 0010. Optimistic locking and transaction boundaries for tasks

- Status: accepted (API exposure decided in Phase 3)
- Date: 2026-11-12

## Context

Two people can edit the same task. Without protection, the second save silently overwrites the
first ("lost update"). The user asked for optimistic locking plus database transactions,
instead of "last write wins".

## Decision

- `Task.version` (domain) and a `version` column, starting at 1.
- **In the database, one statement**:
  `UPDATE tasks_task SET ..., version = version + 1 WHERE id = %s AND version = %s`.
  If it matches zero rows, someone else saved (or deleted) the task first, and the repository
  raises `ConflictError` (409). No row lock is held between the read and the write.
- **In the use case**: `UpdateTaskCommand.expected_version` (optional). If the client edited an
  older copy, `UpdateTask` raises `ConflictError` before saving. Permission is still checked
  first, so a 403 always wins over a 409.
- **Transactions**:
  - HTTP requests: one transaction per request (`ATOMIC_REQUESTS=True`), so a failure after the
    write rolls the write back.
  - Celery tasks and management commands are not HTTP requests. They wrap their work in
    `transaction.atomic()` in their phases (4 and 6).
- `updated_at` / `created_at` come from the `Clock` port, so the version and timestamp tests are exact.

## Consequences

- No row locks and no `select_for_update`: reads never block, and a conflict costs one retry
  for the user.
- Phase 3 decides how a client sends `expected_version` (a `version` field in PATCH, or `If-Match`).
- Delete is not version-checked: deleting a task someone just edited is still a delete.
