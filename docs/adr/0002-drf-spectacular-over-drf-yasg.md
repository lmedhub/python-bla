# 0002. drf-spectacular for the OpenAPI schema

- Status: accepted
- Date: 2026-11-11

## Context

The frontend types are generated from the API schema, so the schema is a contract.
The common options are drf-yasg and drf-spectacular.

## Decision

Use **drf-spectacular** (0.30.0).

- It produces OpenAPI 3.x. drf-yasg only produces Swagger 2.0, and has been
  close to unmaintained for a while.
- `openapi-typescript` expects OpenAPI 3.
- `spectacular --validate` checks the output against the OpenAPI spec, which CI can run.

## Consequences

- drf-spectacular 0.30.0 declares Django up to 6.0, while we use 6.1. A smoke test
  (`spectacular --validate` on Django 6.1.3) passed. The schema drift check in CI
  (added in Phase 3) catches regressions.
