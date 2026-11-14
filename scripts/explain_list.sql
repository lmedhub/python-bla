-- Query plans for the task list on realistic data. Evidence for docs/explain.md.
--
-- Run it against a scratch database that has the migrations applied and no data, never
-- against the app's database: it inserts 50 users and 100,000 tasks. docs/explain.md has
-- the commands.
--
-- The queries are the SQL that DjangoTaskRepository.find() and list_overdue() send,
-- captured with CaptureQueriesContext, with "today" fixed at 2026-11-14 so runs compare.
-- SELECT * stands for Django's explicit list of every column; the plan is the same.

\set ON_ERROR_STOP on
\pset pager off

-- Fixed seed: the same rows on every run.
SELECT setseed(0.42);

INSERT INTO users_user (password, email, name, is_active)
SELECT '!', 'user' || n || '@example.com', 'User ' || n, true
FROM generate_series(1, 50) AS n;

-- About 40% todo, 25% in progress, 35% done. Due dates spread over a year around
-- "today", 10% with no due date. 20% unassigned. User ids are 1-50 in a fresh database.
INSERT INTO tasks_task (
    title, description, status, due_date, created_by_id, assignee_id,
    completed_at, version, created_at, updated_at
)
SELECT
    'Task ' || n,
    '',
    status,
    CASE WHEN random() < 0.10 THEN NULL
         ELSE DATE '2026-11-14' + (floor(random() * 365) - 182)::int END,
    1 + floor(random() * 50)::int,
    CASE WHEN random() < 0.20 THEN NULL ELSE 1 + floor(random() * 50)::int END,
    CASE WHEN status = 'done' THEN TIMESTAMPTZ '2026-11-01 12:00+00' END,
    1,
    TIMESTAMPTZ '2026-01-01 12:00+00',
    TIMESTAMPTZ '2026-01-01 12:00+00'
FROM (
    SELECT n, CASE WHEN r < 0.40 THEN 'todo' WHEN r < 0.65 THEN 'in_progress' ELSE 'done' END
    FROM (SELECT n, random() AS r FROM generate_series(1, 100000) AS n) AS draws
) AS rows (n, status);

-- Up-to-date statistics, as autovacuum would have after a while.
VACUUM ANALYZE users_user;
VACUUM ANALYZE tasks_task;

SELECT status, count(*), count(due_date) AS with_due_date, count(assignee_id) AS assigned
FROM tasks_task GROUP BY status ORDER BY status;

\echo '=== 1. Default list, page 1 ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT * FROM tasks_task
ORDER BY due_date ASC NULLS LAST, id ASC LIMIT 10;

\echo '=== 2. Default list, page 500 of 100 ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT * FROM tasks_task
ORDER BY due_date ASC NULLS LAST, id ASC LIMIT 100 OFFSET 49900;

\echo '=== 3. Count for pagination, no filter ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT COUNT(*) FROM tasks_task;

\echo '=== 4. status=in_progress ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT * FROM tasks_task WHERE status = 'in_progress'
ORDER BY due_date ASC NULLS LAST, id ASC LIMIT 10;

\echo '=== 5. Count, status=in_progress ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT COUNT(*) FROM tasks_task WHERE status = 'in_progress';

\echo '=== 6. due_after=2026-11-01, due_before=2026-11-30 ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT * FROM tasks_task
WHERE due_date >= DATE '2026-11-01' AND due_date <= DATE '2026-11-30'
ORDER BY due_date ASC NULLS LAST, id ASC LIMIT 10;

\echo '=== 7. assignee=7 ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT * FROM tasks_task WHERE assignee_id = 7
ORDER BY due_date ASC NULLS LAST, id ASC LIMIT 10;

\echo '=== 8. overdue=true ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT * FROM tasks_task
WHERE due_date < DATE '2026-11-14' AND NOT (status = 'done')
ORDER BY due_date ASC NULLS LAST, id ASC LIMIT 10;

\echo '=== 9. Count, overdue=true ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT COUNT(*) FROM tasks_task
WHERE due_date < DATE '2026-11-14' AND NOT (status = 'done');

\echo '=== 10. Overdue digest (all rows, no limit) ==='
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT * FROM tasks_task
WHERE due_date < DATE '2026-11-14' AND NOT (status = 'done')
ORDER BY due_date ASC NULLS LAST, id ASC;
