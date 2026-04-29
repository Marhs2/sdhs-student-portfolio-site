import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app.auth import can_view_profile  # noqa: E402
from backend.app.repositories import (  # noqa: E402
    clear_public_cache,
    _filter_public_portfolio_items,
    _get_public_owner_emails,
    list_portfolio_items_by_owner,
    _profile_insert_payload,
    _profile_update_payload,
    is_public_approved_profile,
    list_profiles,
    list_profiles_page,
)


class ProfileVisibilityPolicyTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_public_cache()

    def test_public_profile_list_requires_visible_and_approved(self) -> None:
        profiles = [
            {"id": 1, "job": "프론트엔드", "isVisible": True, "reviewStatus": "approved"},
            {"id": 2, "job": "프론트엔드", "isVisible": True, "reviewStatus": "draft"},
            {"id": 3, "job": "프론트엔드", "isVisible": False, "reviewStatus": "approved"},
        ]

        with patch("backend.app.repositories._select_profiles", return_value=profiles):
            public_profiles = list_profiles()

        self.assertEqual([profile["id"] for profile in public_profiles], [1])

    def test_admin_profile_list_keeps_hidden_and_drafts(self) -> None:
        profiles = [
            {"id": 1, "job": "프론트엔드", "isVisible": True, "reviewStatus": "approved"},
            {"id": 2, "job": "프론트엔드", "isVisible": True, "reviewStatus": "draft"},
            {"id": 3, "job": "프론트엔드", "isVisible": False, "reviewStatus": "approved"},
        ]

        with patch("backend.app.repositories._select_profiles", return_value=profiles):
            admin_profiles = list_profiles(include_hidden=True)

        self.assertEqual([profile["id"] for profile in admin_profiles], [1, 2, 3])

    def test_public_profile_list_uses_short_lived_cache(self) -> None:
        profiles = [
            {"id": 1, "job": "프론트엔드", "isVisible": True, "reviewStatus": "approved"},
        ]

        with patch("backend.app.repositories._select_profiles", return_value=profiles) as select_profiles:
            self.assertEqual([profile["id"] for profile in list_profiles()], [1])
            self.assertEqual([profile["id"] for profile in list_profiles()], [1])

        self.assertEqual(select_profiles.call_count, 1)

    def test_public_profile_page_overfetches_one_row_for_next_offset(self) -> None:
        profiles = [
            {"id": 1, "job": "프론트엔드", "isVisible": True, "reviewStatus": "approved"},
            {"id": 2, "job": "프론트엔드", "isVisible": True, "reviewStatus": "approved"},
            {"id": 3, "job": "프론트엔드", "isVisible": True, "reviewStatus": "approved"},
        ]

        with patch("backend.app.repositories._select_profiles", return_value=profiles) as select_profiles:
            page, has_more = list_profiles_page(limit=2, offset=10)

        self.assertEqual([profile["id"] for profile in page], [1, 2])
        self.assertTrue(has_more)
        self.assertEqual(select_profiles.call_args.kwargs["limit"], 3)
        self.assertEqual(select_profiles.call_args.kwargs["offset"], 10)

    def test_admin_profile_list_bypasses_public_cache(self) -> None:
        profiles = [
            {"id": 1, "job": "프론트엔드", "isVisible": True, "reviewStatus": "approved"},
        ]

        with patch("backend.app.repositories._select_profiles", return_value=profiles) as select_profiles:
            list_profiles(include_hidden=True)
            list_profiles(include_hidden=True)

        self.assertEqual(select_profiles.call_count, 2)

    def test_direct_public_profile_requires_visible_and_approved(self) -> None:
        draft_profile = {
            "id": 2,
            "email": "student@sdh.hs.kr",
            "isVisible": True,
            "reviewStatus": "draft",
        }

        self.assertFalse(can_view_profile(draft_profile, viewer=None))
        self.assertTrue(
            can_view_profile(draft_profile, viewer={"email": "student@sdh.hs.kr"}),
        )
        self.assertTrue(can_view_profile(draft_profile, viewer={"isAdmin": True}))

    def test_public_approved_profile_helper_is_the_single_visibility_gate(self) -> None:
        self.assertTrue(
            is_public_approved_profile(
                {"email": "approved@sdh.hs.kr", "isVisible": True, "reviewStatus": "approved"},
            ),
        )
        self.assertFalse(
            is_public_approved_profile(
                {"email": "draft@sdh.hs.kr", "isVisible": True, "reviewStatus": "draft"},
            ),
        )
        self.assertFalse(
            is_public_approved_profile(
                {"email": "hidden@sdh.hs.kr", "isVisible": False, "reviewStatus": "approved"},
            ),
        )
        self.assertFalse(
            is_public_approved_profile(
                {"email": "banned@sdh.hs.kr", "isVisible": False, "reviewStatus": "banned"},
            ),
        )

    def test_created_profiles_are_public_by_default(self) -> None:
        payload = _profile_insert_payload(
            {
                "name": "New Student",
                "description": "Created during signup",
                "job": "Full Stack",
                "tags": ["vue"],
                "github": "https://github.com/student",
                "imageUrl": "",
            },
            email="student@sdh.hs.kr",
            extended_schema=True,
        )

        self.assertEqual(payload["review_status"], "approved")
        self.assertTrue(payload["is_visible"])

    def test_created_profiles_can_start_private(self) -> None:
        payload = _profile_insert_payload(
            {
                "name": "New Student",
                "description": "Created during signup",
                "job": "Full Stack",
                "tags": ["vue"],
                "github": "https://github.com/student",
                "imageUrl": "",
                "isVisible": False,
            },
            email="student@sdh.hs.kr",
            extended_schema=True,
        )

        self.assertFalse(payload["is_visible"])

    def test_banned_profile_updates_force_private_visibility(self) -> None:
        payload = _profile_update_payload(
            {
                "reviewStatus": "banned",
                "isVisible": True,
            },
            extended_schema=True,
        )

        self.assertEqual(payload["review_status"], "banned")
        self.assertFalse(payload["is_visible"])

    def test_public_portfolio_items_require_public_approved_owner(self) -> None:
        items = [
            {"id": 1, "ownerEmail": "approved@sdh.hs.kr", "title": "Visible project", "tags": []},
            {"id": 2, "ownerEmail": "draft@sdh.hs.kr", "title": "Draft project", "tags": []},
            {"id": 3, "ownerEmail": "hidden@sdh.hs.kr", "title": "Hidden project", "tags": []},
        ]
        public_items = _filter_public_portfolio_items(items, {"approved@sdh.hs.kr"})

        self.assertEqual([item["id"] for item in public_items], [1])
        self.assertNotIn("ownerEmail", public_items[0])

    def test_public_owner_emails_are_cached_for_repeated_public_item_filters(self) -> None:
        profiles = [
            {"email": "approved@sdh.hs.kr", "isVisible": True, "reviewStatus": "approved"},
            {"email": "draft@sdh.hs.kr", "isVisible": True, "reviewStatus": "draft"},
        ]

        with patch("backend.app.repositories._select_profiles", return_value=profiles) as select_profiles:
            self.assertEqual(_get_public_owner_emails(), {"approved@sdh.hs.kr"})
            self.assertEqual(_get_public_owner_emails(), {"approved@sdh.hs.kr"})

        self.assertEqual(select_profiles.call_count, 1)

    def test_public_portfolio_items_by_owner_requires_visible_and_approved_owner(self) -> None:
        with patch("backend.app.repositories._get_public_owner_emails", return_value=set()):
            public_items = list_portfolio_items_by_owner("draft@sdh.hs.kr")

        self.assertEqual(public_items, [])

    def test_public_portfolio_items_by_owner_rechecks_owner_visibility(self) -> None:
        class FakeQuery:
            def eq(self, *_args):
                return self

        rows = [
            {
                "id": 8,
                "title": "Public project",
                "owner": "approved@sdh.hs.kr",
            },
        ]

        with (
            patch("backend.app.repositories._build_portfolio_item_select_query", return_value=FakeQuery()),
            patch(
                "backend.app.repositories._execute_with_missing_column_fallback",
                return_value=SimpleNamespace(data=rows),
            ) as execute_query,
            patch(
                "backend.app.repositories._get_public_owner_emails",
                return_value={"approved@sdh.hs.kr"},
            ) as get_public_owner_emails,
        ):
            public_items = list_portfolio_items_by_owner("approved@sdh.hs.kr")

        self.assertEqual(len(public_items), 1)
        self.assertEqual(public_items[0]["id"], 8)
        self.assertEqual(public_items[0]["title"], "Public project")
        self.assertNotIn("ownerEmail", public_items[0])
        self.assertEqual(get_public_owner_emails.call_count, 1)
        self.assertEqual(execute_query.call_count, 1)


if __name__ == "__main__":
    unittest.main()
