import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402
from backend.app.auth import get_current_user  # noqa: E402


class AuthContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_context_returns_empty_profile_state_for_new_user(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: {
            "id": "user-1",
            "email": "new@sdh.hs.kr",
        }

        with patch("backend.app.routers.auth.get_profile_by_email", return_value=None):
            response = self.client.get("/api/me/context")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "email": "new@sdh.hs.kr",
                "isAdmin": False,
                "isConfigAdmin": False,
                "profileId": None,
                "hasProfile": False,
            },
        )

    def test_context_allows_configured_admin_without_profile(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: {
            "id": "admin-1",
            "email": "admin@sdh.hs.kr",
        }

        with (
            patch("backend.app.routers.auth.get_profile_by_email", return_value=None),
            patch("backend.app.routers.auth.is_configured_admin_email", return_value=True),
        ):
            response = self.client.get("/api/me/context")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "email": "admin@sdh.hs.kr",
                "isAdmin": True,
                "isConfigAdmin": True,
                "profileId": None,
                "hasProfile": False,
            },
        )

    def test_context_blocks_banned_profile_before_returning_admin_context(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: {
            "id": "banned-admin-1",
            "email": "banned-admin@sdh.hs.kr",
        }

        with (
            patch(
                "backend.app.routers.auth.get_profile_by_email",
                return_value={
                    "id": 9,
                    "email": "banned-admin@sdh.hs.kr",
                    "isAdmin": True,
                    "reviewStatus": "banned",
                },
            ),
            patch("backend.app.routers.auth.is_configured_admin_email", return_value=False),
        ):
            response = self.client.get("/api/me/context")

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
