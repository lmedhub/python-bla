# 0006. Validate list filters with a serializer, not django-filter

- Status: accepted (changes a locked decision in HANDOFF.md; agreed on 2026-11-11)
- Date: 2026-11-11

## Context

HANDOFF locked `django-filter`, and also says interfaces must not touch the ORM.
A django-filter `FilterSet` and DRF's paginator both work on querysets inside the view,
so the two rules conflict. HANDOFF's pragmatism clause would allow a queryset-backed page.

## Decision

Keep the layer rule and drop django-filter:

1. A DRF serializer in `interfaces` validates `status`, `due_before`, `due_after`,
   `assignee` (`me` is resolved here), `overdue`, `page` and `page_size`.
2. It builds a plain `TaskFilter` value object (domain) and a page request.
3. The repository (infrastructure) turns `TaskFilter` into `Q` objects and returns a
   `Page` (domain entities plus a total count).
4. Interfaces build the usual `{count, next, previous, results}` envelope.

## Consequences

- Interfaces never see a queryset. The filter logic is tested once, at the repository, against Postgres.
- The OpenAPI parameters come from the serializer via `@extend_schema(parameters=...)`.
- We write the pagination envelope ourselves, about 20 lines, instead of using DRF's paginator.
- One fewer dependency.
