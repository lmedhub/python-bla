# 0007. Due date: not in the past on create, free on update

- Status: accepted
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

## Consequences

- Rules live in `apps/tasks/domain/rules.py` (`check_due_date_on_create`) and are tested
  without Django or a real clock.
- Known limit: near midnight, a user far from UTC can see "today" rejected (UTC is already
  tomorrow) or be allowed "yesterday". Fixing this needs the user's time zone. That is out of
  scope for now, and listed in the README's known limits.
