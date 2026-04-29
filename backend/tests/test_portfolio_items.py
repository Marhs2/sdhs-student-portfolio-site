import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app import create_app  # noqa: E402
from backend.app.routers.portfolio_items import delete_portfolio_item_route  # noqa: E402


class PortfolioItemRouteTests(unittest.TestCase):
    def test_direct_public_item_hides_owner_email(self) -> None:
        client = TestClient(create_app())

        with (
            patch(
                "backend.app.routers.portfolio_items.get_portfolio_item_by_id",
                return_value={"id": 7, "title": "Demo", "ownerEmail": "student@sdh.hs.kr"},
            ),
            patch(
                "backend.app.routers.portfolio_items.get_profile_by_email",
                return_value={"email": "student@sdh.hs.kr", "isVisible": True, "reviewStatus": "approved"},
            ),
        ):
            response = client.get("/api/portfolio-items/7")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("ownerEmail", response.json())

    def test_direct_public_item_blocks_draft_owner(self) -> None:
        client = TestClient(create_app())

        with (
            patch(
                "backend.app.routers.portfolio_items.get_portfolio_item_by_id",
                return_value={"id": 7, "title": "Demo", "ownerEmail": "student@sdh.hs.kr"},
            ),
            patch(
                "backend.app.routers.portfolio_items.get_profile_by_email",
                return_value={"email": "student@sdh.hs.kr", "isVisible": True, "reviewStatus": "draft"},
            ),
        ):
            response = client.get("/api/portfolio-items/7")

        self.assertEqual(response.status_code, 404)

    def test_public_portfolio_items_support_limit_offset_headers(self) -> None:
        client = TestClient(create_app())
        page = [{"id": 2, "title": "B"}]

        with patch("backend.app.routers.portfolio_items.list_portfolio_items_page", return_value=(page, True)):
            response = client.get("/api/portfolio-items?limit=1&offset=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), page)
        self.assertEqual(response.headers["x-result-count"], "1")
        self.assertEqual(response.headers["x-next-offset"], "2")

    def test_delete_missing_item_uses_readable_error_message(self) -> None:
        with patch("backend.app.routers.portfolio_items.delete_portfolio_item", return_value=False):
            with self.assertRaises(HTTPException) as raised:
                delete_portfolio_item_route(
                    404,
                    profile={"id": 1, "email": "admin@sdh.hs.kr", "isAdmin": True},
                )

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "포트폴리오 항목을 찾을 수 없습니다.")


if __name__ == "__main__":
    unittest.main()
