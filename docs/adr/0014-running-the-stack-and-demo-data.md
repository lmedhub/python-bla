# 0014. Running the stack: nginx in front, demo data on an empty database

- Status: accepted (Phase 6)
- Date: 2026-11-14

## Context

HANDOFF asks that `docker compose up --build` from a clean clone gives a working app with demo
data, that nginx serves the frontend and proxies `/api` (same origin, no CORS), and that images
run as non-root users.

## Decision

**One entry point.** The `web` service (nginx, `nginxinc/nginx-unprivileged`, non-root, port
8080) serves the built frontend and proxies `/api/` to `api:8000`.
- The browser sees one origin: no CORS, and the refresh cookie (path `/api/v1/auth`) works as in
  development, where Vite does the same proxying.
- `api` has no host port. Every request passes nginx, which sets `X-Forwarded-For`, and Django
  trusts exactly one proxy (`NUM_PROXIES=1`). A published API port would let a client send its
  own `X-Forwarded-For` and dodge the rate limits.
- App routes fall back to `index.html`. Hashed assets are cached for a year; `index.html` is
  revalidated on every load (`no-cache`). The app's pages get a strict Content-Security-Policy (`default-src 'self'`),
  `nosniff` and `Referrer-Policy`. Swagger UI under `/api/` loads its scripts from a CDN, so
  nginx leaves those responses alone.

**Demo data.** `manage.py seed_demo` creates 4 users and 30 tasks covering every status,
overdue (one unassigned), due today, no due date, unassigned, and done in the past.
- It runs only on an empty database (no users): a second run, or a restart, changes nothing.
- It runs at startup only when `SEED_DEMO=true` (set in `.env.example`). A real deployment leaves
  it unset. The password comes from `DEMO_PASSWORD`.
- It writes rows directly, not through the use cases: those refuse past due dates (overdue
  demo tasks need them) and would email every assignee. One transaction, so a failed seed
  leaves nothing half-written.
- It lives in its own small app, `apps/demo`. It may import every feature; import-linter
  forbids any feature (and `config`) from importing it. Inside a feature it would have to
  import another feature's infrastructure.

**Checked in CI.** The `docker` job starts the stack from a clean checkout with
`.env.example`, waits for every healthcheck, checks both images run as non-root, and runs
`scripts/smoke_test.py` through nginx (page, app-route fallback, health, signed-out refresh,
demo login, at least 30 tasks, Swagger UI).

## Consequences

- To use the API directly, go through `http://localhost:8080/api/...`; `runserver` (port 8000)
  is for local development.
- The demo password is in `.env.example` and the README. It protects demo data only.
- `make fresh` (drop the volumes) is how to get the demo data back after changing it.
