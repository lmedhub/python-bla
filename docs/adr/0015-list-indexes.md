# 0015. Indexes for the task list

- Status: accepted
- Date: 2026-11-14

## Context

HANDOFF asks for `(status, due_date)`, `assignee_id` and `created_by_id` indexes, and a partial
index only if `EXPLAIN` shows a benefit. In Phase 7 the list queries were measured on 100,000
tasks ([explain.md](../explain.md)). The default list (no filter, the page the app opens on)
read the whole table and sorted it: 14.7 ms for page 1, 84 ms with a sort spilled to disk for a
deep page. No index matched its order, `due_date ASC NULLS LAST, id`.

## Decision

- Add `tasks_due_date_id_idx` on `(due_date, id)`. It matches the order exactly, so every page
  (filtered or not) is read from the index and stops at the `LIMIT`.
- Keep the HANDOFF indexes. `(status, due_date)` still serves the status `COUNT(*)` as an
  index-only scan. The two foreign key indexes come with Django's `ForeignKey`.
- No partial index for overdue tasks: with `(due_date, id)` in place it saved under 1 ms on the
  count and about 5 ms on the once-a-day digest.
- A test checks the query plan of the SQL `find()` sends, so a change to the order or the index
  that breaks the match fails CI.

## Consequences

- Default page 1: 14.7 ms → 0.04 ms. Overdue page 1: 11.8 ms → 0.09 ms.
- About 3 MB more index per 100,000 tasks, and one more index to update on each write.
- `COUNT(*)` and deep `OFFSET` pages are still linear. Documented in explain.md; keyset
  pagination is the next step if it ever matters.
