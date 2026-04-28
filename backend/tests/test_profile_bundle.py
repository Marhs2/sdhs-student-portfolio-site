import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402


class ProfileBundleTests(unittest.TestCase):
    def test_profile_bundle_returns_detail_payload_in_one_request(self) -> None:
        app = create_app()
        client = TestClient(app)
        profile = {
            "id": 1,
            "name": "Kim",
            "email": "kim@sdh.hs.kr",
            "isVisible": True,
            "reviewStatus": "approved",
        }

        with (
            patch("backend.app.routers.profiles.get_profile_by_id", return_value=profile.copy()),
            patch("backend.app.routers.profiles.get_profile_html", return_value="<p>소개</p>"),
            patch(
                "backend.app.routers.profiles.list_portfolio_items_by_owner",
                return_value=[{"id": 7, "title": "Demo"}],
            ),
        ):
            response = client.get("/api/profiles/1/bundle")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["profile"]["id"], 1)
        self.assertNotIn("email", response.json()["profile"])
        self.assertEqual(response.json()["html"], "<p>소개</p>")
        self.assertEqual(response.json()["portfolioItems"], [{"id": 7, "title": "Demo"}])


if __name__ == "__main__":
    unittest.main()
