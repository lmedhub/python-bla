# 0013. Frontend architecture

- Status: accepted (Phase 5)
- Date: 2026-11-13

## Context

HANDOFF section 9 fixes the stack (React, strict TypeScript, Vite, TanStack Query, React Router,
types generated from `openapi.yaml`) and the behavior (token in memory, filters in the URL,
no console warnings). This records the choices made inside those limits.

## Decision

**Versions.** Pinned exactly (`save-exact`), checked against the npm registry on 2026-11-13.
**TypeScript 5.9.3, not 7.0:** typescript-eslint 8.72 supports TypeScript below 6.1, and
openapi-typescript 7.13 declares TypeScript 5. 5.9.3 is the newest version the whole tool chain
supports. React Router 8 needs Node 22.22 or later.

**Registry.** `frontend/.npmrc` sets the public npm registry. `package-lock.json` records
download URLs, so a machine-wide private registry would leak into the lockfile and break CI.

**The API boundary is `src/api/`.**
- `generated/schema.d.ts` is written by openapi-typescript and never edited. Only files in
  `src/api/` import it (`types.ts` for named types, `client.ts` and `session.ts` for `paths`);
  an ESLint rule rejects imports of `generated/` from anywhere outside `src/api/`.
- `client.ts` is the openapi-fetch client; `tasks.ts` and `users.ts` are one function per call;
  `errors.ts` turns the API's single error shape into one `ApiError` class.

**Session (`src/api/session.ts`).**
- The access token is a module variable, never in storage.
- A page load calls `POST /auth/refresh` once: the HttpOnly cookie restores the session.
- Every API call goes through `authorizedFetch`: it adds `Authorization` and `X-Timezone`
  (ADR 0007), and on a 401 refreshes once and retries once.
- **One refresh at a time.** Refresh tokens rotate and are blacklisted after use (ADR 0003).
  Two parallel refreshes, from parallel 401s or from React StrictMode running effects twice,
  would present a used token and sign the user out. All callers share the request in flight.
- If the refresh fails, listeners are told and the app shows the login page.

**State.** Server data lives in TanStack Query; after any change, every `["tasks", ...]` query
is invalidated (no optimistic updates). Filters and page live in the URL (`useSearchParams`).
Local UI state uses `useState`. No global state library.

**Edits.** The edit form sends `version`; a 409 reloads the task and says so (ADR 0010). The
status toggle in the list sends no version, so it does not fail because someone fixed a typo.

**Permissions in the UI** come from the signed-in user and the task (ADR 0011): actions the
user may not take are disabled. The API enforces the same rules.

**UI.** Pages for create and edit (shareable URLs, simpler focus handling). Delete confirmation
uses the native `<dialog>`: the browser traps focus and closes it on Esc; focus starts on
Cancel. One styling method: CSS Modules per component plus one global stylesheet for tokens
and plain elements. No UI kit. Dates are formatted in one module, `src/lib/dates.ts`, in the
browser's language; date-only values are built from their parts, never `new Date("YYYY-MM-DD")`.

**Tests.** Vitest, Testing Library (queries by role and label) and MSW, which answers at the
network level, so tests run the real client, session and refresh code. Tests:
- fail on any `console.error` or `console.warn`, and on any request no handler expected;
- run with `TZ=America/Sao_Paulo`, so a date shown one day early fails here, not for users.

## Consequences

- A signed-out visit makes one `POST /auth/refresh`. It first answered 401, which browsers
  print in the console; since D64 a request with no cookie answers 204 (ADR 0003).
- jsdom does not implement `<dialog>`'s `showModal()`. Tests stub it; the real focus and Esc
  behavior is checked in a real browser.
- `npm audit` reports a moderate advisory in `minimatch`, used by ESLint only; the shipped
  bundle's dependencies have none (`npm audit --omit=dev`).
