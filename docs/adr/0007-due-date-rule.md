# 0007. Due date: not in the past on create, free on update

- Status: accepted, amended 2026-11-13 ("today" is the caller's date, see below)
- Date: 2026-11-12

## Context

HANDOFF asks us to decide whether `due_date` may be in the past, and to record the decision.

## Decision

- **On create**, `due_date` must be today or later. A new task that is already overdue is
  almost always a typo. The error is a field error on `due_date` (400).
- **On update**, any date is allowed, including a past one, and the date can be cleared.
  An existing task becomes overdue on its own over time. Editing its title or description
  must not force the user to change its due date too.
- "Today" is the **UTC** date from the `Clock` port (`clock.today()`), never `date.today()`.
  Ruff's DTZ rules reject `date.today()` in code.

## Amendment (2026-11-13): "today" is the caller's date

The known limit below happened during the Phase 3 manual run. At 21:21 in Sao Paulo (00:21 UTC
the next day), creating a task due "today" was rejected as past, and tasks would also turn
overdue about 3 hours early every evening.

- The client sends its IANA time zone in an **`X-Timezone`** header (e.g. `America/Sao_Paulo`).
  Without it, UTC is used. An unknown or malformed name is a 400 on `X-Timezone`.
- The interfaces layer builds a `ZonedClock` for the request. `now()` is the same instant;
  `today()` is that instant's date in the caller's zone.
- **Domain and use cases did not change.** They already asked the `Clock` port for `today()`.
  The create rule, `is_overdue` and the `overdue` filter all follow the caller's zone.

## Consequences

- Rules live in `apps/tasks/domain/rules.py` (`check_due_date_on_create`) and are tested
  without Django or a real clock.
- ~~Known limit: near midnight, users far from UTC see the wrong "today".~~ Fixed by the
  amendment above. What remains: clients that do not send `X-Timezone` get UTC, and two users
  in different zones can see different `is_overdue` values for the same task. That is correct,
  because overdue is relative to the viewer's day.
