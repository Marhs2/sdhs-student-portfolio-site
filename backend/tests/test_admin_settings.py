import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402
from backend.app.auth import require_admin, require_server_admin  # noqa: E402


class AdminSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_admin_settings_requires_authentication(self) -> None:
        response = self.client.get("/api/admin/settings")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_settings_returns_operational_admin_context(self) -> None:
        self.app.dependency_overrides[require_admin] = lambda: {
            "email": "admin@sdh.hs.kr",
            "isAdmin": True,
        }

        response = self.client.get("/api/admin/settings")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["allowedEmailDomain"], "sdh.hs.kr")
        self.assertEqual(payload["currentAdminEmail"], "admin@sdh.hs.kr")
        self.assertIn(payload["currentAdminSource"], {"profile", "environment"})
        self.assertGreater(payload["maxUploadBytes"], 0)
        self.assertNotIn("configuredAdminEmails", payload)
        self.assertNotIn("allowedOrigins", payload)
        self.assertNotIn("allowedOriginRegex", payload)
        self.assertNotIn("imageBucket", payload)

    def test_server_settings_exposes_admin_managed_departments(self) -> None:
        self.app.dependency_overrides[require_server_admin] = lambda: {
            "email": "owner@sdh.hs.kr",
            "isAdmin": True,
            "isConfigAdmin": True,
        }

        response = self.client.get("/api/server-admin/settings")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("departments", payload)
        self.assertNotIn("currentAdminEmail", payload)
        self.assertNotIn("configuredAdminEmails", payload)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertIn("소프트웨어과", payload["departments"])


if __name__ == "__main__":
    unittest.main()
