# 0005. Degrade, don't fail, when Redis is down

- Status: accepted (health check done in Phase 0; the rest in Phases 3 and 4)
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

## Consequences

- While Redis is down there is no rate limiting and no notifications. Both are logged.
  Failing closed would turn a cache outage into a full API outage.
- Measured in Phase 0 against a real stopped container: the health check answers in about
  2 s with Redis down, and about 5 s with the database down. Slow, but bounded.
