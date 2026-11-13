# 0011. API conventions

- Status: accepted
- Date: 2026-11-12

## Context

Phase 3 builds the HTTP layer. Several small choices shape every endpoint and the frontend
that consumes them. They are recorded together here.

## Decision

1. **Serializers check types; the domain checks rules.** A PATCH title is accepted by the
   serializer even if blank, so the domain can answer 403 to someone who may not edit before
   it answers 400 (ADR 0008).
2. **Error codes are a closed list** (`invalid_input`, `parse_error`, `not_authenticated`,
   `permission_denied`, `not_found`, `method_not_allowed`, `conflict`, `throttled`, ...),
   published as the `ErrorCode` enum. Clients switch on `code`, never on `detail`.
3. **Optimistic locking from clients**: PATCH takes an optional `version` field (the version
   the client last read). A mismatch is 409 `conflict` (ADR 0010). A header (`If-Match`) was
   the alternative; a body field is simpler and visible in OpenAPI.
4. **No per-task permission flags in responses.** A task looks the same to every caller.
   Login and refresh return the user, the frontend keeps it in memory, and derives
   "may edit / may change status / may delete" from `created_by` and `assignee`. The API still
   enforces every rule. (User feedback, 2026-11-12: per-task flags mixed UI concerns into the
   resource.)
5. **Refresh answers like login** (`{access, user}`), so a page reload restores the session
   with one call.
6. **Pagination links are relative** (`/api/v1/tasks?page=2&status=todo`). They work behind any
   proxy without trusting `Host` / `X-Forwarded-*` headers.
7. **Users are ids in task responses** (`created_by`, `assignee`). Names come from `GET /users`,
   which the assignee picker loads anyway. The list cannot have an N+1 problem.
8. **`is_overdue` comes from the server's clock**, so all clients agree.
9. **OpenAPI is strict**: generated with `--validate --fail-on-warn`, committed as
   `openapi.yaml`, and CI fails when it is out of date. Swagger UI and ReDoc load **pinned**
   asset versions (drf-spectacular's default is `@latest`).

## Consequences

- The frontend repeats two comparisons (`created_by == me`, `assignee == me`). That logic
  is tiny and lives in one tested helper.
- Clients that never send `version` get "last write wins" for their own edits. Two writes
  racing at the same moment still get a 409 from the database check.
