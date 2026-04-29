import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app.auth import get_current_profile  # noqa: E402


class BannedAuthPolicyTests(unittest.TestCase):
    def test_banned_profile_cannot_enter_authenticated_surfaces(self) -> None:
        with (
            patch(
                "backend.app.auth.get_profile_by_email",
                return_value={
                    "id": 9,
                    "email": "banned@sdh.hs.kr",
                    "reviewStatus": "banned",
                    "isAdmin": False,
                },
            ),
            patch("backend.app.auth.is_configured_admin_email", return_value=False),
        ):
            with self.assertRaises(HTTPException) as context:
                get_current_profile({"email": "banned@sdh.hs.kr"})

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
