from typing import Any

from rest_framework.request import Request

from apps.tasks.application.queries import Page


def paginated(request: Request, page: Page[Any], results: list[Any]) -> dict[str, Any]:
    """The usual {count, next, previous, results} envelope, built from a domain Page."""
    number = page.request.page
    return {
        "count": page.total,
        "next": _link(request, number + 1) if page.has_next else None,
        "previous": _link(request, number - 1) if page.has_previous else None,
        "results": results,
    }


def _link(request: Request, page_number: int) -> str:
    # Relative on purpose: no Host / X-Forwarded-* trust needed behind the proxy.
    query = request.query_params.copy()
    query["page"] = str(page_number)
    return f"{request.path}?{query.urlencode()}"
