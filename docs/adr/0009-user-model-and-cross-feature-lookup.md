# 0009. Custom user model, lowercase emails, and how tasks checks users

- Status: accepted
- Date: 2026-11-12

## Context

- HANDOFF wants a custom user model with email login, in the first migration.
- Emails must be unique regardless of letter case.
- Tasks must check that an assignee is an active user. HANDOFF says features talk only through
  each other's `application` layer, and that wiring lives in each feature's own `interfaces/`.
  Nothing is allowed to give tasks a ready-made users repository, so the two rules conflict.

## Decision

**User model** (`apps/users/infrastructure/models.py`):

- `AbstractBaseUser` with `email` (unique, `USERNAME_FIELD`), `name` and `is_active`.
  No `PermissionsMixin`: there is no admin, and no groups or permissions are needed.
- Emails are **stored lowercase**:
  - `normalize_email()` (domain) trims and lowercases the address;
  - the manager uses it on create and on login lookup (`get_by_natural_key`);
  - a check constraint `email = lower(email)` makes the database reject anything else.
  With every stored email lowercase, the ordinary unique index is already case-insensitive.
  No second functional index and no `iexact` lookups are needed.
- `users.0001` is the first migration (`AUTH_USER_MODEL = "users.User"`).

**Cross-feature lookup** (option "b", chosen 2026-11-12):

- `tasks.infrastructure.DjangoUserDirectory` implements the tasks port `UserDirectory` with
  `get_user_model().objects.filter(pk=..., is_active=True).exists()`.
- `get_user_model()` resolves the model from `AUTH_USER_MODEL`, the same indirection the task
  foreign keys use. Tasks never imports any users module, and the import-linter contracts
  stay unchanged.

## Consequences

- The meaning of "active" (the `is_active` flag) appears in two places: users and this adapter.
  It is one boolean, and both are covered by tests.
- Test factories use the string `"users.User"`, so tasks tests can create users without importing
  users' infrastructure.
- The alternative, letting the tasks wiring import the users wiring, would have needed an
  exception in the contracts.
