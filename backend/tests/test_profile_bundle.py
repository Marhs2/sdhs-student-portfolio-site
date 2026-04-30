import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402
from backend.app.auth import get_optional_profile  # noqa: E402


class ProfileBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_public_profile_bundle_hides_operational_fields(self) -> None:
        profile = {
            "id": 1,
            "name": "Kim",
            "email": "kim@sdh.hs.kr",
            "isAdmin": False,
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
            response = self.client.get("/api/profiles/1/bundle")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["cache-control"],
            "public, max-age=15, stale-while-revalidate=30",
        )
        self.assertEqual(response.json()["profile"]["id"], 1)
        self.assertNotIn("email", response.json()["profile"])
        self.assertNotIn("isAdmin", response.json()["profile"])
        self.assertNotIn("isVisible", response.json()["profile"])
        self.assertNotIn("reviewStatus", response.json()["profile"])
        self.assertEqual(response.json()["html"], "<p>소개</p>")
        self.assertEqual(response.json()["portfolioItems"], [{"id": 7, "title": "Demo"}])

    def test_owner_profile_bundle_keeps_private_management_fields(self) -> None:
        self.app.dependency_overrides[get_optional_profile] = lambda: {
            "email": "kim@sdh.hs.kr",
            "isAdmin": False,
        }
        profile = {
            "id": 1,
            "name": "Kim",
            "email": "kim@sdh.hs.kr",
            "isAdmin": False,
            "isVisible": False,
            "reviewStatus": "draft",
        }

        with (
            patch("backend.app.routers.profiles.get_profile_by_id", return_value=profile.copy()),
            patch("backend.app.routers.profiles.get_profile_html", return_value="<p>작성중</p>"),
            patch(
                "backend.app.routers.profiles.list_portfolio_items_by_owner",
                return_value=[],
            ),
        ):
            response = self.client.get(
                "/api/profiles/1/bundle",
                headers={"Authorization": "Bearer test.token.value"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store, private")
        self.assertEqual(
            response.json()["profile"],
            {
                "id": 1,
                "name": "Kim",
                "email": "kim@sdh.hs.kr",
                "isAdmin": False,
                "isVisible": False,
                "reviewStatus": "draft",
            },
        )

    def test_public_profile_bundle_does_not_fast_path_portfolio_visibility(self) -> None:
        profile = {
            "id": 1,
            "name": "Kim",
            "email": "kim@sdh.hs.kr",
            "isAdmin": False,
            "isVisible": True,
            "reviewStatus": "approved",
        }

        with (
            patch("backend.app.routers.profiles.get_profile_by_id", return_value=profile.copy()),
            patch("backend.app.routers.profiles.get_profile_html", return_value="<p>?뚭컻</p>"),
            patch(
                "backend.app.routers.profiles.list_portfolio_items_by_owner",
                return_value=[],
            ) as list_portfolio_items,
        ):
            response = self.client.get("/api/profiles/1/bundle")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["portfolioItems"], [])
        list_portfolio_items.assert_called_once_with(
            "kim@sdh.hs.kr",
            include_private=False,
        )

    def test_public_profile_detail_hides_operational_fields(self) -> None:
        profile = {
            "id": 1,
            "name": "Kim",
            "email": "kim@sdh.hs.kr",
            "isAdmin": False,
            "isVisible": True,
            "reviewStatus": "approved",
        }

        with patch("backend.app.routers.profiles.get_profile_by_id", return_value=profile.copy()):
            response = self.client.get("/api/profiles/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1, "name": "Kim"})

    def test_public_profile_portfolio_items_do_not_fast_path_visibility(self) -> None:
        profile = {
            "id": 1,
            "name": "Kim",
            "email": "kim@sdh.hs.kr",
            "isAdmin": False,
            "isVisible": True,
            "reviewStatus": "approved",
        }

        with (
            patch("backend.app.routers.profiles.get_profile_by_id", return_value=profile.copy()),
            patch(
                "backend.app.routers.profiles.list_portfolio_items_by_owner",
                return_value=[],
            ) as list_portfolio_items,
        ):
            response = self.client.get("/api/profiles/1/portfolio-items")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        list_portfolio_items.assert_called_once_with(
            "kim@sdh.hs.kr",
            include_private=False,
        )


if __name__ == "__main__":
    unittest.main()
