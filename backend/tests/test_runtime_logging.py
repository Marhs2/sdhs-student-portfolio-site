import json
import logging
import os
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

import backend.app as app_module
from backend.app import create_app
from backend.app.auth import require_admin
from backend.app.repositories import _execute_query
from backend.app.security_logging import log_security_event


def test_database_startup_does_not_log_service_role_hint() -> None:
    database_source = Path("backend/app/database.py").read_text(encoding="utf-8")

    assert "service_role_hint" not in database_source
    assert "Loaded Supabase backend key role hint" not in database_source


def test_supabase_client_disables_http2() -> None:
    database_source = Path("backend/app/database.py").read_text(encoding="utf-8")
    auth_source = Path("backend/app/auth.py").read_text(encoding="utf-8")
    app_source = Path("backend/app/__init__.py").read_text(encoding="utf-8")

    assert "http2=False" in database_source
    assert "auth_http_client = httpx.Client" in database_source
    assert "connect=1.0" in database_source
    assert 'if "httpx_client" in signature(ClientOptions).parameters' in database_source
    assert 'client_options_kwargs["httpx_client"] = supabase_http_client' in database_source
    assert "def close_supabase_clients" in database_source
    assert "close_supabase_clients()" in app_source
    assert "auth.failure_rate_limited" in app_source
    assert "http.sensitive_mutation_rate_limited" in app_source
    assert ".auth.get_user" not in auth_source
    assert "get_auth_user(credentials.credentials)" in auth_source


def test_transient_supabase_query_is_retried() -> None:
    class Query:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self) -> dict:
            self.calls += 1
            if self.calls == 1:
                raise ConnectionResetError("stream reset")
            return {"data": ["ok"]}

    query = Query()

    assert _execute_query(query, operation="unit.test") == {"data": ["ok"]}
    assert query.calls == 2


def test_security_event_logs_are_structured_json(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="portfolio-security"):
        log_security_event(
            "authorization.test_denied",
            outcome="blocked",
            severity="warning",
            actor_email="student@sdh.hs.kr",
            target_type="profile",
            target_id=7,
            reason="unit_test",
            token="should-not-be-used-by-callers",
        )

    payload = json.loads(caplog.records[-1].message)

    assert payload["event"] == "authorization.test_denied"
    assert payload["outcome"] == "blocked"
    assert payload["actorEmail"] == "student@sdh.hs.kr"
    assert payload["targetId"] == 7
    assert payload["reason"] == "unit_test"
    assert payload["token"] == "[redacted]"


def test_admin_denial_writes_security_log(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="portfolio-security"):
        try:
            require_admin({"id": 3, "email": "student@sdh.hs.kr", "isAdmin": False})
        except HTTPException:
            pass

    payload = json.loads(caplog.records[-1].message)

    assert payload["event"] == "authorization.admin_required"
    assert payload["outcome"] == "blocked"
    assert payload["actorEmail"] == "student@sdh.hs.kr"
    assert payload["actorProfileId"] == 3


def test_api_requests_write_detailed_security_logs(caplog) -> None:
    client = TestClient(create_app())

    with caplog.at_level(logging.INFO, logger="portfolio-security"):
        response = client.get(
            "/api/admin/settings?token=secret-value",
            headers={
                "Origin": "https://portfolio.example",
                "User-Agent": "SecurityLogTest/1.0",
                "X-Forwarded-For": "203.0.113.10",
            },
        )

    assert response.status_code == 401
    events = [json.loads(record.message) for record in caplog.records]
    completed = next(event for event in events if event["event"] == "http.request_completed")
    denied = next(event for event in events if event["event"] == "http.access_denied")

    assert completed["requestId"] == response.headers["x-request-id"]
    assert completed["method"] == "GET"
    assert completed["path"] == "/api/admin/settings"
    assert completed["statusCode"] == 401
    assert completed["origin"] == "https://portfolio.example"
    assert completed["userAgent"] == "SecurityLogTest/1.0"
    assert completed["forwardedFor"] == "203.0.113.10"
    assert completed["query"]["token"] == "[redacted]"
    assert isinstance(completed["durationMs"], int)
    assert denied["requestId"] == completed["requestId"]


def test_repeated_auth_failures_are_rate_limited() -> None:
    app_module._auth_failure_events_by_host.clear()
    client = TestClient(create_app())

    response = None
    for _ in range(app_module.AUTH_FAILURE_LIMIT + 1):
        response = client.get(
            "/api/admin/settings",
            headers={
                "Authorization": "Bearer not-a-jwt",
                "X-Forwarded-For": "198.51.100.20",
            },
        )

    assert response is not None
    assert response.status_code == 429
    assert response.headers["retry-after"] == str(app_module.AUTH_FAILURE_WINDOW_SECONDS)


def test_repeated_sensitive_mutations_are_rate_limited() -> None:
    app_module._sensitive_mutation_events_by_host.clear()
    for _ in range(app_module.SENSITIVE_MUTATION_LIMIT):
        app_module._record_sensitive_mutation("198.51.100.30")
    client = TestClient(create_app())

    response = client.delete(
        "/api/server-admin/profiles/7",
        headers={"X-Forwarded-For": "198.51.100.30"},
    )

    assert response.status_code == 429
    assert response.headers["retry-after"] == str(app_module.SENSITIVE_MUTATION_WINDOW_SECONDS)


def test_student_write_routes_are_sensitive_mutations() -> None:
    request_type = type(
        "Request",
        (),
        {
            "method": "PUT",
            "url": type("Url", (), {"path": "/api/profiles/7/html"})(),
        },
    )

    assert app_module._is_sensitive_mutation_request(request_type())

    request_type.url = type("Url", (), {"path": "/api/portfolio-items/11"})()
    assert app_module._is_sensitive_mutation_request(request_type())


def test_unauthenticated_sensitive_mutations_do_not_consume_mutation_quota() -> None:
    app_module._sensitive_mutation_events_by_host.clear()
    client = TestClient(create_app())

    for _ in range(app_module.SENSITIVE_MUTATION_LIMIT + 1):
        response = client.delete(
            "/api/server-admin/profiles/7",
            headers={"X-Forwarded-For": "198.51.100.31"},
        )

    assert response.status_code == 401
    assert "198.51.100.31" not in app_module._sensitive_mutation_events_by_host


def test_forwarded_for_is_ignored_for_untrusted_direct_clients() -> None:
    request = type(
        "Request",
        (),
        {
            "headers": {"x-forwarded-for": "203.0.113.77"},
            "client": type("Client", (), {"host": "198.51.100.44"})(),
        },
    )()

    assert app_module._client_host_from_request(request) == "198.51.100.44"


def test_forwarded_for_uses_last_untrusted_hop_from_trusted_proxy() -> None:
    request = type(
        "Request",
        (),
        {
            "headers": {"x-forwarded-for": "198.51.100.99, 203.0.113.12"},
            "client": type("Client", (), {"host": "10.0.0.5"})(),
        },
    )()

    assert app_module._client_host_from_request(request) == "203.0.113.12"
