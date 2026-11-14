# 0016. Browser tests with Playwright

- Status: accepted
- Date: 2026-11-14

## Context

The API tests call Django through its test client, and the frontend tests fake the API with
MSW. Nothing automated checked that the built frontend and the real API work together in a
browser, or that the console stays clean (HANDOFF §9 and §13). That was checked by hand with a
throwaway script in Phases 5 and 7. jsdom also has no `<dialog>`, so the delete dialog's focus
and Esc were never tested automatically.

## Decision

- Playwright Test (`@playwright/test`, dev dependency), in `frontend/e2e/`. It runs against the
  whole stack through nginx, as a user would reach it, not the Vite dev server.
- CI runs it in the `docker` job, after the smoke test, on the stack that job already started from
  a clean checkout. On failure the report and traces are kept for 7 days.
- Chromium only. The app uses nothing that differs between engines; Firefox and WebKit would add CI
  time without testing anything new.
- Every test fails on a console warning, a console error or an uncaught exception.
- Each spec file signs in once and shares one page across its tests, run in order:
  - login allows 5 a minute per IP, and the run signs in 3 times (plus 1 for the smoke test);
  - the refresh token rotates on every use, so a saved session (Playwright's `storageState`)
    would be rejected the second time it is used.
- Tests create their own task (unique title, due date far from the seeded ones) and delete it.
  Seeded tasks are only read.
- Swagger UI's "Authorize" is not covered: its markup is not ours and changes between versions.

Why not Cypress: Playwright runs headless Chromium from one package, with no app-side setup,
and its role and label locators match the Testing Library queries the unit tests already use.

## Consequences

- About 1–2 minutes more in the `docker` job (Chromium download and 13 tests in about 10 s).
- Tests in one file depend on each other (create, then edit, then delete). A failure skips the
  rest of that file instead of reporting unrelated failures.
- Running the suite twice within a minute hits the login throttle (429). The Makefile says so.
- No coverage of the Mailpit email or the Celery beat digest from the browser; the backend tests
  cover those.
