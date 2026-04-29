import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402
from backend.app.auth import require_server_admin  # noqa: E402


class ServerAdminProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)
        self.app.dependency_overrides[require_server_admin] = lambda: {
            "id": 1,
            "email": "owner@sdh.hs.kr",
            "isAdmin": True,
            "isConfigAdmin": True,
        }

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_server_admin_can_delete_profile(self) -> None:
        with patch("backend.app.routers.server_admin_profiles.delete_profile", return_value=True) as delete_profile:
            response = self.client.delete("/api/server-admin/profiles/7")

        self.assertEqual(response.status_code, 204)
        delete_profile.assert_called_once_with(7)

    def test_server_admin_delete_returns_not_found_for_missing_profile(self) -> None:
        with patch("backend.app.routers.server_admin_profiles.delete_profile", return_value=False):
            response = self.client.delete("/api/server-admin/profiles/404")

        self.assertEqual(response.status_code, 404)

    def test_server_admin_profile_list_keeps_admin_flag(self) -> None:
        with patch(
            "backend.app.routers.server_admin_profiles.list_admin_profiles",
            return_value=[
                {
                    "id": 7,
                    "name": "Admin",
                    "reviewStatus": "approved",
                    "isVisible": True,
                    "isAdmin": True,
                },
            ],
        ):
            response = self.client.get("/api/server-admin/profiles")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()[0]["isAdmin"])


if __name__ == "__main__":
    unittest.main()
