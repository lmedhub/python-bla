# 0003. JWT session design

- Status: accepted. Backend in Phase 3, frontend in Phase 5; amended in Phase 6 (no cookie → 204)
- Date: 2026-11-11

## Context

The brief asks for JWT. Tokens in `localStorage` can be stolen by any XSS.
nginx serves the frontend and the API from the same origin.

## Decision

- **Access token**: short lived, kept **in memory** in the frontend only.
- **Refresh token**: rotated on every use, old one blacklisted
  (`djangorestframework-simplejwt` with `token_blacklist`). Sent as a cookie:
  `HttpOnly; SameSite=Strict; Path=/api/v1/auth`. `Secure` comes from settings
  (on in prod). Browsers treat `http://localhost` as secure, so the demo still works.
- Thin custom login, refresh and logout views wrap simplejwt's serializers, because
  simplejwt's own views read the refresh token from the body, not a cookie.
- **CSRF**: the only cookie-authenticated endpoints are refresh and logout. `SameSite=Strict`
  plus the same origin blocks cross-site requests, so no CSRF token is added.
- **One in-flight refresh** in the frontend. Rotation makes a refresh token single-use,
  so two parallel refreshes (two 401s at once, or React StrictMode running the
  "restore session" effect twice) would log the user out. All callers wait on one promise.

## Implementation notes (Phase 3)

- Refresh returns `{access, user}`, like login (ADR 0011).
- simplejwt 5.5.1 raises `User.DoesNotExist` (a 500) when the refresh token belongs to a deleted
  user. `RefreshView` turns it into a 401, and a test covers it.
- With no authenticators, DRF turns 401 into 403. The login, refresh and logout views return a
  `Bearer` challenge themselves to keep 401.
- simplejwt annotates `Token(token=...)` as `Token | None` but takes the encoded string. There is one
  targeted `type: ignore[arg-type]` with a comment.

## Amendment (Phase 6): no cookie is 204, not 401

- `POST /auth/refresh` **without any refresh cookie** answers `204 No Content`: nobody is
  signed in, which is the normal state of a first visit. A cookie that is present but expired,
  tampered or blacklisted is still `401`.
- Why: the frontend calls refresh on every page load to restore a session. Browsers print every
  4xx response in the console, so each signed-out visit showed an error line, and HANDOFF asks
  for no console errors. The status code now says what happened: no session, not a failure.
- The frontend already treated an empty answer as "no session"; only its tests changed.

## Consequences

- A page reload loses the access token. The app calls `/auth/refresh` on start to get a new one.
- simplejwt 5.5.1 (July 2025) declares Django up to 5.2. A smoke test on Django 6.1.3
  passed: login, rotate, reuse of an old token rejected (401), blacklist on logout.
  The Phase 3 auth tests (expired, tampered, blacklisted) guard against regressions.
- `SECRET_KEY` must be 50+ characters. PyJWT warns about short HMAC keys, and settings
  fail at startup if the key is short.
