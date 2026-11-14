"""Checks a running stack from the outside, through nginx, like a browser would.

Usage: python scripts/smoke_test.py [base URL]   (default http://localhost:8080)
Reads DEMO_PASSWORD from the environment. Standard library only, so it runs anywhere.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"


def request(method: str, path: str, body: dict | None = None, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310 (our own URL)
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"{'ok  ' if condition else 'FAIL'} {name}{f'  ({detail})' if detail and not condition else ''}")
    if not condition:
        sys.exit(1)


status, page = request("GET", "/")
check("the app's page is served", status == 200 and '<div id="root">' in page, str(status))

status, page = request("GET", "/tasks/1/edit")
check("app routes fall back to index.html", status == 200 and '<div id="root">' in page, str(status))

status, body = request("GET", "/api/v1/health")
check("health is ok", status == 200 and json.loads(body)["status"] == "ok", body)

status, _ = request("POST", "/api/v1/auth/refresh")
check("a signed-out refresh is 204, not an error", status == 204, str(status))

password = os.environ.get("DEMO_PASSWORD", "")
status, body = request(
    "POST", "/api/v1/auth/login", {"email": "alice@example.com", "password": password}
)
check("a demo user can sign in", status == 200, f"{status} {body}")
token = json.loads(body)["access"]

status, body = request("GET", "/api/v1/tasks?page_size=100", token=token)
count = json.loads(body).get("count", 0) if status == 200 else 0
check("demo tasks are seeded", count >= 30, f"{status}, count={count}")

status, page = request("GET", "/api/v1/docs")
check("Swagger UI is served", status == 200 and "swagger" in page.lower(), str(status))
