import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402


class HealthAndCacheHeaderTests(unittest.TestCase):
    def test_health_endpoint_is_fast_and_public(self) -> None:
        client = TestClient(create_app())

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertIn("camera=()", response.headers["permissions-policy"])
        self.assertTrue(response.headers["x-request-id"])

    def test_public_profiles_response_disables_browser_cache(self) -> None:
        client = TestClient(create_app())

        with patch("backend.app.routers.profiles.list_profiles", return_value=[]):
            response = client.get("/api/profiles")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["cache-control"],
            "no-cache, no-store, must-revalidate",
        )


if __name__ == "__main__":
    unittest.main()
