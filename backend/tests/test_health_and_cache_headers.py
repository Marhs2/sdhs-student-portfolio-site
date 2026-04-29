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

    def test_public_profiles_response_allows_short_browser_cache(self) -> None:
        client = TestClient(create_app())

        with patch("backend.app.routers.profiles.list_profiles", return_value=[]):
            response = client.get("/api/profiles")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["cache-control"],
            "public, max-age=15, stale-while-revalidate=30",
        )

    def test_public_profiles_support_limit_offset_without_changing_array_contract(self) -> None:
        client = TestClient(create_app())
        page = [{"id": 2, "name": "B"}, {"id": 3, "name": "C"}]

        with patch("backend.app.routers.profiles.list_profiles_page", return_value=(page, False)):
            response = client.get("/api/profiles?limit=2&offset=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), page)
        self.assertEqual(response.headers["x-result-count"], "2")
        self.assertNotIn("x-next-offset", response.headers)

    def test_public_profiles_expose_next_offset_when_more_results_exist(self) -> None:
        client = TestClient(create_app())
        page = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]

        with patch("backend.app.routers.profiles.list_profiles_page", return_value=(page, True)):
            response = client.get("/api/profiles?limit=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), page)
        self.assertEqual(response.headers["x-result-count"], "2")
        self.assertEqual(response.headers["x-next-offset"], "2")


if __name__ == "__main__":
    unittest.main()
