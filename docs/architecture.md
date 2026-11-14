# Architecture

How the pieces fit, from the outside in. The decisions behind each part are in
[docs/adr/](adr/).

## System context

```mermaid
flowchart LR
    user([Team member<br/>browser])
    app[Task Manager]
    mail[(Mail server<br/>Mailpit in Docker)]
    user -- "plans, assigns and completes tasks (HTTPS/HTTP)" --> app
    app -- "assignment emails, daily overdue digest (SMTP)" --> mail
    mail -. "reads email" .-> user
```

## Containers (docker compose)

```mermaid
flowchart LR
    browser([Browser])
    subgraph compose[docker compose]
        web["web<br/>nginx: built React app,<br/>proxies /api"]
        api["api<br/>Django + DRF on gunicorn"]
        worker["worker<br/>Celery"]
        beat["beat<br/>Celery beat"]
        db[("db<br/>PostgreSQL 18")]
        redis[("redis<br/>Redis 8")]
        mailpit["mailpit<br/>SMTP + web UI"]
    end
    browser -- ":8080" --> web
    web -- "/api/*" --> api
    api -- "SQL" --> db
    api -- "throttle counters; queue jobs" --> redis
    beat -- "daily digest job" --> redis
    redis -- "jobs" --> worker
    worker -- "SQL" --> db
    worker -- "SMTP" --> mailpit
    browser -. ":8025" .-> mailpit
```

- **web**: the only entry point to the app and the API (ADR 0014). db, redis and mailpit also
  publish ports, for local tools only. Same origin for the app and the API.
- **api**: migrates, seeds demo data on an empty database, then serves the API.
- **worker / beat**: same image as `api`, different command (ADR 0004, 0012).
- **redis**: the Celery broker and the rate-limit cache. If it is down, requests still succeed
  (ADR 0005).

## Inside the backend: four layers per feature

```mermaid
flowchart TB
    interfaces["interfaces<br/>DRF views, serializers, Celery jobs,<br/>container.py (wiring)"]
    application["application<br/>use cases + ports (Protocols)"]
    domain["domain<br/>Task, rules, errors<br/>(plain Python)"]
    infrastructure["infrastructure<br/>Django models, repositories,<br/>CeleryNotifier, mailer, clocks"]
    interfaces --> application --> domain
    infrastructure --> application
    interfaces -. "container.py only" .-> infrastructure
```

Two features, `tasks` and `users`, plus `core` (health, errors) and `demo` (seed data). The rules
are enforced by import-linter in pre-commit and CI (ADR 0001):

- `domain` and `application` import no framework: no Django, DRF, Celery or Redis.
- `interfaces` reaches `infrastructure` only through `container.py`, the composition root.
- `interfaces` never touches the ORM (ruff TID251; ADR 0001).
- `tasks` reaches `users` only through `users.application`; `users` never imports `tasks`.
- Nothing imports `demo`.

The frontend has the same idea at a smaller scale (ADR 0013): components reach the API only
through `src/api/`, whose types are generated from `openapi.yaml`.

## A request, end to end: assigning a task

What happens when Alice creates a task assigned to Bob.

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser (React)
    participant N as nginx (web)
    participant V as TaskCollectionView (DRF)
    participant U as CreateTask (use case)
    participant R as DjangoTaskRepository
    participant P as Postgres
    participant Q as Redis
    participant W as Celery worker
    participant M as Mailpit
    B->>N: POST /api/v1/tasks {title, assignee: Bob}<br/>Authorization: Bearer …, X-Timezone
    N->>V: proxied, X-Forwarded-For set
    V->>V: JWT auth, rate limit, serializer checks shape
    V->>U: CreateTaskCommand (clock in caller's time zone)
    U->>U: domain rules: title, due date not in the past, Bob is active
    U->>R: add(task)
    R->>P: INSERT (inside the request's transaction)
    U->>U: notifier.task_assigned(task id, Bob's id)
    Note over U: CeleryNotifier registers transaction.on_commit
    V->>P: COMMIT (the view returned, ATOMIC_REQUESTS ends)
    V->>Q: on commit: publish job [task id, Bob's id] (a failure is logged, not raised)
    V-->>N: 201 Task
    N-->>B: 201 Task
    B->>B: invalidate ["tasks"] queries, list refetches
    Q->>W: notify_assignment(task id, Bob's id)
    W->>P: already sent? (SentNotification key)
    W->>P: re-read task and Bob, skip if deleted, reassigned or inactive
    W->>M: email to Bob
    W->>P: record key, so a retry sends nothing
```

Points worth knowing:

- **Errors** at any step become the one error shape `{code, detail, fields}` (ADR 0008, 0011):
  a blank title is a 400 on `title`, an inactive assignee a 400 on `assignee`.
- **Time**: "today" is the caller's date from `X-Timezone` (ADR 0007), so a due date of today
  is valid at 21:00 in Sao Paulo even though UTC is already tomorrow.
- **Transactions**: one per request (`ATOMIC_REQUESTS`). The job is published only after the
  commit, so a rolled-back request sends no email, and the worker always finds the task.
- **Redis down**: the task is still saved and the response is still 201; the lost email is
  logged (ADR 0005).
- **Edits** carry the `version` the client read; a stale one is a 409 (ADR 0010).
- **Session**: on a 401 the frontend refreshes once (one shared refresh) and retries once
  (ADR 0003, 0013).
