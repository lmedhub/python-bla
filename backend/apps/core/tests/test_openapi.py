from typing import Any

import pytest
import yaml
from django.core.management import call_command
from drf_spectacular.generators import SchemaGenerator

PUBLIC_OPERATIONS = {
    ("/api/v1/auth/login", "post"),
    ("/api/v1/auth/refresh", "post"),
    ("/api/v1/auth/logout", "post"),
    ("/api/v1/health", "get"),
}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    generated: dict[str, Any] = SchemaGenerator().get_schema(request=None, public=True)
    return generated


def operations(schema: dict[str, Any]):
    for path, item in schema["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                yield path, method, operation


def test_generates_a_valid_schema_without_warnings(tmp_path):
    # --fail-on-warn turns every drf-spectacular warning (guessed types, enum name
    # clashes, unannotated views) into a failure.
    target = tmp_path / "openapi.yaml"

    call_command("spectacular", "--validate", "--fail-on-warn", "--file", str(target))

    assert yaml.safe_load(target.read_text())["openapi"].startswith("3.")


def test_task_status_is_one_named_enum(schema):
    components = schema["components"]["schemas"]

    assert components["TaskStatus"]["enum"] == ["todo", "in_progress", "done"]
    assert "StatusEnum" not in components


def test_declares_the_bearer_scheme(schema):
    assert schema["components"]["securitySchemes"]["jwtAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }


def test_public_operations_need_no_token(schema):
    for path, method, operation in operations(schema):
        if (path, method) in PUBLIC_OPERATIONS:
            assert operation.get("security") in (None, [], [{}]), (path, method)


def test_protected_operations_document_401_and_429(schema):
    for path, method, operation in operations(schema):
        if (path, method) in PUBLIC_OPERATIONS or path.startswith(
            ("/api/v1/schema", "/api/v1/docs", "/api/v1/redoc")
        ):
            continue
        assert {"401", "429"} <= set(operation["responses"]), (path, method)


def test_every_client_error_uses_the_shared_error_shape(schema):
    for path, method, operation in operations(schema):
        for status_code, response in operation["responses"].items():
            if status_code.startswith("4"):
                ref = response["content"]["application/json"]["schema"]["$ref"]
                assert ref == "#/components/schemas/Error", (path, method, status_code)


def test_the_task_list_documents_its_query_parameters(schema):
    operation = schema["paths"]["/api/v1/tasks"]["get"]
    parameters = {p["name"] for p in operation["parameters"] if p["in"] == "query"}

    assert parameters == {
        "status",
        "due_after",
        "due_before",
        "assignee",
        "overdue",
        "page",
        "page_size",
    }


@pytest.mark.django_db  # every request runs in a transaction (ATOMIC_REQUESTS)
def test_the_schema_endpoint_serves_it(api_client):
    response = api_client.get("/api/v1/schema", {"format": "json"})

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Task Manager API"


@pytest.mark.django_db
def test_swagger_ui_and_redoc_load_pinned_assets(api_client):
    swagger = api_client.get("/api/v1/docs").content.decode()
    redoc = api_client.get("/api/v1/redoc").content.decode()

    assert "swagger-ui-dist@5.34.0" in swagger
    assert "redoc@2.5.4" in redoc
    assert "@latest" not in swagger + redoc


def test_task_endpoints_document_the_time_zone_header(schema):
    for path, method, operation in operations(schema):
        if not path.startswith("/api/v1/tasks") or method == "delete":
            continue
        headers = {p["name"] for p in operation.get("parameters", []) if p["in"] == "header"}
        assert "X-Timezone" in headers, (path, method)
