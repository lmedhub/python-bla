# 0008. Shared domain errors, one HTTP status each

- Status: accepted (the HTTP mapping is implemented in Phase 3)
- Date: 2026-11-12

## Context

Use cases must report "bad input", "not allowed" and "does not exist" without knowing about
HTTP. HANDOFF also wants one error shape for every response.

## Decision

Exceptions in `apps/core/domain/errors.py`, a small shared kernel that imports nothing:

| Exception | HTTP | Notes |
| --- | --- | --- |
| `InvalidInputError(fields)` | 400 | `fields` maps an API field name to messages, e.g. `{"assignee": [...]}` |
| `PermissionDeniedError` | 403 | |
| `NotFoundError` | 404 | |
| `ConflictError` | 409 | Added by ADR 0010 (stale `version`) |

- Names end in `Error` (ruff N818). They avoid `ValidationError` and `PermissionDenied`,
  because Django and DRF already use those names, and the Phase 3 error handler imports both sets.
- On update, **permission is checked before validation**. Someone who may not edit a task
  gets 403, never a 400 that describes what would have been valid.
- An unknown or inactive assignee is `InvalidInputError` on `assignee` (400), not a conflict (409).

## Consequences

- One DRF exception handler (Phase 3) maps these exceptions to the shared error shape.
- Use cases report only the first failing rule, in the order title, then due date, then
  assignee. DRF serializer validation in Phase 3 still reports all field-type errors at once.
