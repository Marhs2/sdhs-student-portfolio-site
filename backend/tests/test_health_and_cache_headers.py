import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402
from backend.app.config import get_settings  # noqa: E402


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

        with patch(
            "backend.app.routers.profiles.list_profiles",
            return_value=[
                {
                    "id": 1,
                    "name": "Public",
                    "isVisible": True,
                    "reviewStatus": "approved",
                    "isAdmin": False,
                    "email": "public@sdh.hs.kr",
                },
            ],
        ):
            response = client.get("/api/profiles")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["cache-control"],
            "public, max-age=15, stale-while-revalidate=30",
        )
        self.assertEqual(response.json(), [{"id": 1, "name": "Public"}])

    def test_public_profiles_support_limit_offset_without_changing_array_contract(self) -> None:
        client = TestClient(create_app())
        page = [
            {
                "id": 2,
                "name": "B",
                "isVisible": True,
                "reviewStatus": "approved",
                "email": "b@sdh.hs.kr",
            },
            {
                "id": 3,
                "name": "C",
                "isVisible": True,
                "reviewStatus": "approved",
                "isAdmin": False,
            },
        ]

        with patch("backend.app.routers.profiles.list_profiles_page", return_value=(page, False)):
            response = client.get("/api/profiles?limit=2&offset=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": 2, "name": "B"}, {"id": 3, "name": "C"}])
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

    def test_rejects_spoofable_shared_vercel_origin_regex(self) -> None:
        previous = os.environ.get("PORTFOLIO_ALLOWED_ORIGIN_REGEX")
        os.environ["PORTFOLIO_ALLOWED_ORIGIN_REGEX"] = (
            r"https://sdhs-student-portfolio-site-[a-z0-9-]+\.vercel\.app"
        )
        get_settings.cache_clear()

        try:
            with self.assertRaises(RuntimeError):
                get_settings()
        finally:
            if previous is None:
                os.environ.pop("PORTFOLIO_ALLOWED_ORIGIN_REGEX", None)
            else:
                os.environ["PORTFOLIO_ALLOWED_ORIGIN_REGEX"] = previous
            get_settings.cache_clear()


if __name__ == "__main__":
    unittest.main()
