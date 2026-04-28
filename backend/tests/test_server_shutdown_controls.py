import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app


FORBIDDEN_SERVER_CONTROL_PATTERNS = (
    "os._exit",
    "sys.exit",
    "raise SystemExit",
    "subprocess.",
    "os.system",
    "signal.SIGTERM",
    "signal.SIGKILL",
)


def test_dangerous_server_control_paths_are_blocked() -> None:
    client = TestClient(create_app())

    for path in (
        "/api/shutdown",
        "/api/restart",
        "/api/kill",
        "/admin/terminate",
        "/server-stop",
    ):
        response = client.post(path)

        assert response.status_code == 404
        assert response.headers["x-request-id"]


def test_backend_does_not_use_process_termination_primitives() -> None:
    backend_app = Path("backend/app")
    source = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in backend_app.rglob("*.py")
        if "__pycache__" not in path.parts
    )

    for pattern in FORBIDDEN_SERVER_CONTROL_PATTERNS:
        assert pattern not in source
