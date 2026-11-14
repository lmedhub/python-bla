# Query plans for the task list

Evidence for the list endpoint's indexes (HANDOFF §4). Short version: the default list sorted
the whole table on every request. One index on `(due_date, id)` fixed that. A partial index for
"overdue" was measured and **not** added.

## How to reproduce

The script inserts 100,000 tasks, so it runs against a throwaway Postgres, never the app's:

```bash
docker run -d --rm --name tm-explain -e POSTGRES_PASSWORD=explain -e POSTGRES_DB=explain \
  -p 55432:5432 postgres:18-alpine
cd backend
POSTGRES_PORT=55432 POSTGRES_DB=explain POSTGRES_USER=postgres POSTGRES_PASSWORD=explain \
  uv run python manage.py migrate --settings=config.settings.test
docker exec -i tm-explain psql -U postgres -d explain -X < ../scripts/explain_list.sql
docker stop tm-explain
```

[`scripts/explain_list.sql`](../scripts/explain_list.sql) seeds 50 users and 100,000 tasks with
a fixed random seed (40% todo, 25% in progress, 35% done; 10% without a due date; 20%
unassigned; due dates over a year around "today"), runs `VACUUM ANALYZE`, then runs
`EXPLAIN (ANALYZE, BUFFERS)` on the SQL that `DjangoTaskRepository` sends. That SQL was captured
from the real `find()` and `list_overdue()` with `CaptureQueriesContext`.

Full output: [before](explain-before.txt) and [after](explain-after.txt). PostgreSQL 18.6, warm
cache, one run each on a laptop: read the timings as orders of magnitude, not benchmarks.

## Results

Every list request runs two queries: the page and a `COUNT(*)` for the total.

| # | Query | Before | After |
| --- | --- | --- | --- |
| 1 | Default list, page 1 | Seq Scan + top-N sort, **14.7 ms** | Index Scan `due_date_id`, **0.04 ms** |
| 2 | Default list, page 500 (OFFSET 49,900) | Seq Scan + sort spilled to disk (8.7 MB), **83.8 ms** | Index Scan, **23.0 ms** |
| 3 | `COUNT(*)`, no filter | Index Only Scan, 9.3 ms | same |
| 4 | `status=in_progress` | Index Scan `status_due_date` + incremental sort, 0.15 ms | Index Scan `due_date_id`, 0.09 ms |
| 5 | `COUNT(*)`, `status=in_progress` | Index Only Scan `status_due_date`, 2.7 ms | same |
| 6 | `due_after` / `due_before` (one month) | Bitmap scan of 7,300 rows + sort, 3.5 ms | Index Scan `due_date_id`, 0.07 ms |
| 7 | `assignee=7` | Bitmap scan `assignee_id` of 1,569 rows + sort, 1.4 ms | Index Scan `due_date_id`, 0.53 ms |
| 8 | `overdue=true` | Bitmap scan of 44,767 rows + sort, 11.8 ms | Index Scan `due_date_id`, 0.09 ms |
| 9 | `COUNT(*)`, `overdue=true` | Index Only Scan `status_due_date`, 5.3 ms | same |
| 10 | Overdue digest (28,853 rows, no limit) | Bitmap scan + sort in memory, 26.2 ms | same |

## Reading

- **The default order had no matching index.** The list orders by
  `due_date ASC NULLS LAST, id`. The old `(status, due_date)` index starts with `status`, so it
  cannot give that order without a status filter, and Postgres read all 100,000 rows to return
  10. The model comment said that index "serves the default list order"; that was wrong.
- **`(due_date, id)` matches the order exactly.** A B-tree is ascending with NULLs last by
  default, the same as the `ORDER BY`. Postgres reads the first rows of the index and stops at the
  `LIMIT`. Filtered pages (status, assignee, overdue) use the same index and skip rows that do not
  match, which is cheap while matches are common.
- **`id` in the index is what removes the sort.** With `due_date` alone, ties would still need a
  sort on `id`. The index costs about 3 MB here.
- **`(status, due_date)` stays.** The status `COUNT(*)` reads it without touching the table
  (Index Only Scan), and HANDOFF asks for it.
- **The partial index was not worth it.** On top of `(due_date, id)`,
  `CREATE INDEX ... ON tasks_task (due_date, id) WHERE status <> 'done'` gave overdue page 1
  0.07 ms (no gain), the overdue count 4.0 ms instead of 4.9 ms, and the daily digest 21.8 ms
  instead of 26.4 ms. That is not worth 2 MB and another index to update on every write.
- A regression test checks the plan, not only that the index exists:
  `test_the_default_order_reads_the_due_date_index_instead_of_sorting` takes the SQL that `find()`
  sends and checks that Postgres reads `tasks_due_date_id_idx` with no Sort step.

## What is still linear

- **`COUNT(*)` reads every matching row** (9 ms for 100,000). It runs on every list request so
  the page can show a total. At millions of rows, the options are an estimate from the planner's
  statistics, or "has next page" without a total.
- **Deep pages cost more** (23 ms at offset 49,900): `OFFSET` still walks the skipped rows.
  Keyset pagination (`WHERE (due_date, id) > (last_due_date, last_id)`) would make every page
  cost the same, but it changes the API (no jumping to page N). Nobody pages 500 deep in this
  app.
- Migration `0003` uses a plain `AddIndex`, which blocks writes to the table while the index
  builds. That is fine for this table's size. On a large production table it would be
  `AddIndexConcurrently` in a non-atomic migration.
