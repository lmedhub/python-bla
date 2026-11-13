# 0005. Degrade, don't fail, when Redis is down

- Status: accepted. Health check in Phase 0; throttles in Phase 3; notifications in Phase 4 (done)
- Date: 2026-11-11

## Context

Redis is both the Celery broker and the throttle cache. HANDOFF requires that a request
still succeeds, without hanging, when Redis is down.

## Decision

- **Timeouts everywhere**: Redis cache and client use 1 s connect/read timeouts;
  Postgres uses `connect_timeout=3`.
- **Notifications** are enqueued with `transaction.on_commit(..., robust=True)`. By default
  an exception in an on_commit callback reaches the client *after* the data is committed,
  which would turn a saved task into a 500. `robust=True` logs and swallows it.
  The publish uses a short broker timeout and no publish retry.
- **Throttles fail open**: if the cache raises, the request is allowed and a warning is logged.
- **Health**: `GET /api/v1/health` returns 200 `"degraded"` when only Redis is down,
  and 503 `"down"` when the database is down.

## Notifications (Phase 4)

- Broker settings: `broker_connection_timeout=1`, `socket_connect_timeout=1`,
  `task_publish_retry=False`. A failed publish raises at once, `robust=True` logs it, and
  the request returns its normal response.
- **DNS matters as much as sockets.** In Docker, a stopped Redis container's name stops
  resolving. The default resolver then waits about 8 s per lookup, and socket timeouts do
  not cover name lookups. Measured with the real stack, Redis stopped:

  | | Default resolver | `dns_opt: [timeout:1, attempts:1]` |
  | --- | --- | --- |
  | `POST /tasks` with an assignee (throttle check + publish) | 16.1 s | 2.1 s |
  | `GET /health` | 8.0 s | 1.0 s |

  The backend services in compose now use those resolver options. The automated tests use a
  closed port on `127.0.0.1`, which has no DNS step, so they could not catch this.
- Logging goes to stdout at INFO for every logger (`LOGGING` in base settings). Without it,
  Django prints its own errors, including the failed `on_commit` publish, only when `DEBUG` is on.
- After Redis comes back, the worker reconnects by itself (checked by hand).

## Consequences

- While Redis is down there is no rate limiting and no notifications. Both are logged.
  Failing closed would turn a cache outage into a full API outage.
- Measured in Phase 0 against a real stopped container: the health check answers in about
  2 s with Redis down, and about 5 s with the database down. Slow, but bounded.
