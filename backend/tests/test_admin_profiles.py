import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402
from backend.app.auth import require_admin  # noqa: E402


class AdminProfileRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)
        self.app.dependency_overrides[require_admin] = lambda: {
            "id": 1,
            "email": "admin@sdh.hs.kr",
            "isAdmin": True,
        }

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_regular_admin_profile_list_hides_admin_flag(self) -> None:
        with patch(
            "backend.app.routers.admin_profiles.list_admin_profiles",
            return_value=[
                {
                    "id": 7,
                    "name": "Admin",
                    "reviewStatus": "approved",
                    "isVisible": True,
                    "isAdmin": True,
                },
                {
                    "id": 8,
                    "name": "Student",
                    "reviewStatus": "review",
                    "isVisible": False,
                    "isAdmin": False,
                },
            ],
        ):
            response = self.client.get("/api/admin/profiles")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], 7)
        self.assertNotIn("isAdmin", response.json()[0])
        self.assertNotIn("isAdmin", response.json()[1])

    def test_regular_admin_profile_update_hides_admin_flag(self) -> None:
        with patch(
            "backend.app.routers.admin_profiles.update_profile",
            return_value={
                "id": 8,
                "name": "Student",
                "reviewStatus": "approved",
                "isVisible": True,
                "isAdmin": False,
            },
        ):
            response = self.client.put(
                "/api/admin/profiles/8",
                json={"reviewStatus": "approved", "isVisible": True},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 8)
        self.assertNotIn("isAdmin", response.json())


if __name__ == "__main__":
    unittest.main()
