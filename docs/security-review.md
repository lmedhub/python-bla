# Security review (Phase 7)

What was checked on 2026-11-14, what changed, and what is accepted. Everything below was run
against a clean clone of the stack (`docker compose up --build`), not read from config.

## Changed

| Finding | Fix | Evidence |
| --- | --- | --- |
| The nginx image (`nginx-unprivileged:1.31.7-alpine`, last rebuilt 2026-10-19) had 13 HIGH/CRITICAL findings with Alpine fixes (brotli, curl, expat, libxslt, musl, zlib) | `apk upgrade` in the runtime stage, then back to uid 101 | Trivy 0.76.1: 13 → **0** |
| The Python image (`python:3.12.16-slim-trixie`, the newest 3.12 tag) had 2 HIGH zlib findings with a Debian fix | `apt-get upgrade` in the runtime stage, before the app user is created | Trivy: the zlib findings are gone |
| `check --deploy` W002: Swagger UI and ReDoc (served by Django, not covered by nginx's CSP) could be framed | Django's `XFrameOptionsMiddleware` (`DENY`) | Test `test_swagger_ui_and_redoc_refuse_to_be_framed`; header seen through nginx |

## Accepted, with the reason

- **47 HIGH findings left in the Python image** (11 CVEs): util-linux, ncurses, SQLite, systemd
  libraries, acl, perl-base. Debian marks them "affected" or "fix deferred": there is no fixed
  package to install. The vulnerable code is not reachable from the app: no SQLite (Postgres
  only), no mount/nsenter, no systemd-homed, no terminal input, no tar parsing. The containers run
  as non-root users. Re-scan when Debian ships fixes; a distroless base is the bigger step.
- **`check --deploy` W003 (no CSRF middleware)**: the API authenticates with a bearer header,
  which a browser never adds by itself. The only cookie-authenticated endpoints are refresh and
  logout, and the cookie is `SameSite=Strict` on the same origin (ADR 0003).
- **W004 / W008 (no HSTS, no HTTPS redirect)**: TLS ends in front of the stack (an AWS load
  balancer in an ECS-style deployment), which is where the redirect and HSTS belong. The demo runs
  on plain `http://localhost`, where both would break it.
- **`npm audit`: 9 moderate**, all from `minimatch` under ESLint and typescript-eslint (dev
  only). `npm audit --omit=dev` finds 0. typescript-eslint 8.72.2 still depends on the affected
  `minimatch`; npm's suggested fix is a downgrade, so nothing is changed.
- **Swagger UI and ReDoc are public**, as HANDOFF's API table lists them. They show the API's
  shape, no data; every data call still needs a token.
- **The demo password is in `.env.example`** on purpose; it protects demo data only.

## Verified, no change needed

| Area | Result |
| --- | --- |
| Refresh cookie | `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=86400` (seen on a real login) |
| Tokens | Access 5 min in memory; refresh rotated on every use, old one blacklisted (ADR 0003) |
| Login | One message for unknown email, wrong password and inactive user; Django's backend hashes even for an unknown email, so timing does not tell either |
| Throttling | Login 5/min per client IP (nginx forwards it, `NUM_PROXIES=1`): 429, `Retry-After`, the shared error shape (seen live) |
| App pages (nginx) | `Content-Security-Policy: default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`, `nosniff`, `Referrer-Policy: same-origin`, `server_tokens off` |
| API (Django) | `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: same-origin`, `Cross-Origin-Opener-Policy` |
| Settings | Prod has `DEBUG = False`; `SECRET_KEY` (50+ chars) and `ALLOWED_HOSTS` are required, or the app refuses to start (tested) |
| Secrets | `.env` is ignored and was never committed; `.env.example` holds local-only values |
| Containers | API, worker and beat run as uid 10001, nginx as uid 101; code is owned by root, so the app user cannot change it; `api` has no host port |
| Python dependencies | Trivy reports 0 findings in the installed packages |

## How to repeat the scans

```bash
docker build --pull -t tm-scan-backend backend && docker build --pull -t tm-scan-web frontend
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.76.1 \
  image --scanners vuln --severity HIGH,CRITICAL tm-scan-backend   # then tm-scan-web
cd frontend && npm audit && npm audit --omit=dev
```
