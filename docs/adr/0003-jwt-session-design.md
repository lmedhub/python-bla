# 0003. JWT session design

- Status: accepted (implemented in Phase 3 and 5)
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

## Consequences

- A page reload loses the access token. The app calls `/auth/refresh` on start to get a new one.
- simplejwt 5.5.1 (July 2025) declares Django up to 5.2. A smoke test on Django 6.1.3
  passed: login, rotate, reuse of an old token rejected (401), blacklist on logout.
  The Phase 3 auth tests (expired, tampered, blacklisted) guard against regressions.
- `SECRET_KEY` must be 50+ characters. PyJWT warns about short HMAC keys, and settings
  fail at startup if the key is short.
