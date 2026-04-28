import base64
import json
from time import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.auth import (
    get_current_profile,
    get_current_user,
    is_allowed_school_email,
    require_server_admin,
)


def _jwt_segment(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _valid_test_jwt(*, email: str = "student@sdh.hs.kr", expires_in: int = 3600) -> str:
    header = _jwt_segment({"alg": "RS256", "typ": "JWT"})
    payload = _jwt_segment(
        {
            "sub": "user-1",
            "email": email,
            "exp": int(time()) + expires_in,
        },
    )
    return f"{header}.{payload}.signature"


class AuthDomainTests(unittest.TestCase):
    def test_allows_only_sdh_school_domain(self) -> None:
        self.assertTrue(is_allowed_school_email("student@sdh.hs.kr"))
        self.assertTrue(is_allowed_school_email(" Student@SDH.HS.KR "))
        self.assertFalse(is_allowed_school_email("student@gmail.com"))
        self.assertFalse(is_allowed_school_email("student@evil-sdh.hs.kr"))
        self.assertFalse(is_allowed_school_email(""))

    def test_rejects_authenticated_non_school_email(self) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=_valid_test_jwt(email="student@gmail.com"),
        )
        user = SimpleNamespace(id="user-1", email="student@gmail.com")

        with patch(
            "backend.app.auth.get_auth_user",
            return_value={"id": user.id, "email": user.email},
        ):
            with self.assertRaises(HTTPException) as context:
                get_current_user(credentials)

        self.assertEqual(context.exception.status_code, 403)

    def test_rejects_malformed_token_before_remote_validation(self) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="not-a-jwt",
        )

        with patch("backend.app.auth.get_auth_user") as get_auth_user:
            with self.assertRaises(HTTPException) as context:
                get_current_user(credentials)

        self.assertEqual(context.exception.status_code, 401)
        get_auth_user.assert_not_called()

    def test_rejects_expired_token_before_remote_validation(self) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=_valid_test_jwt(expires_in=-60),
        )

        with patch("backend.app.auth.get_auth_user") as get_auth_user:
            with self.assertRaises(HTTPException) as context:
                get_current_user(credentials)

        self.assertEqual(context.exception.status_code, 401)
        get_auth_user.assert_not_called()

    def test_auth_network_failure_returns_service_unavailable(self) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=_valid_test_jwt(),
        )

        with patch(
            "backend.app.auth.get_auth_user",
            side_effect=httpx.ConnectError("broken pipe"),
        ):
            with self.assertRaises(HTTPException) as context:
                get_current_user(credentials)

        self.assertEqual(context.exception.status_code, 503)

    def test_configured_admin_email_can_access_without_profile(self) -> None:
        with (
            patch("backend.app.auth.get_profile_by_email", return_value=None),
            patch("backend.app.auth.is_configured_admin_email", return_value=True),
        ):
            profile = get_current_profile({"id": "admin-1", "email": "admin@sdh.hs.kr"})

        self.assertTrue(profile["isAdmin"])
        self.assertTrue(profile["isConfigAdmin"])
        self.assertEqual(profile["email"], "admin@sdh.hs.kr")

    def test_server_admin_requires_environment_admin_source(self) -> None:
        with self.assertRaises(HTTPException) as context:
            require_server_admin({"email": "db-admin@sdh.hs.kr", "isAdmin": True})

        self.assertEqual(context.exception.status_code, 403)

    def test_server_admin_allows_configured_admin_source(self) -> None:
        profile = require_server_admin(
            {"email": "admin@sdh.hs.kr", "isAdmin": True, "isConfigAdmin": True},
        )

        self.assertEqual(profile["email"], "admin@sdh.hs.kr")


if __name__ == "__main__":
    unittest.main()
