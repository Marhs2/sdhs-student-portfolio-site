import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from pydantic import ValidationError


SCHEMAS_PATH = Path(__file__).resolve().parents[1] / "app" / "schemas.py"
schema_spec = spec_from_file_location("portfolio_backend_schemas", SCHEMAS_PATH)
schema_module = module_from_spec(schema_spec)
assert schema_spec.loader is not None
schema_spec.loader.exec_module(schema_module)
AdminProfileUpdatePayload = schema_module.AdminProfileUpdatePayload
ServerAdminProfileUpdatePayload = schema_module.ServerAdminProfileUpdatePayload


class AdminProfileSchemaTests(unittest.TestCase):
    def test_admin_profile_update_accepts_curation_fields(self) -> None:
        payload = AdminProfileUpdatePayload(
            featuredRank=1,
            reviewStatus="approved",
            isVisible=True,
        )

        self.assertEqual(
            payload.model_dump(exclude_unset=True),
            {
                "featuredRank": 1,
                "reviewStatus": "approved",
                "isVisible": True,
            },
        )

    def test_admin_profile_update_ignores_server_managed_fields(self) -> None:
        payload = AdminProfileUpdatePayload(
            isAdmin=True,
            school="서울디지텍고등학교",
            department="웹솔루션과",
            track="서버",
        )

        self.assertEqual(payload.model_dump(exclude_unset=True), {})

    def test_server_admin_profile_update_accepts_server_managed_fields(self) -> None:
        payload = ServerAdminProfileUpdatePayload(
            isAdmin=True,
            school="서울디지텍고등학교",
            department="웹솔루션과",
            track="서버",
        )

        self.assertEqual(
            payload.model_dump(exclude_unset=True),
            {
                "isAdmin": True,
                "school": "서울디지텍고등학교",
                "department": "웹솔루션과",
                "track": "서버",
            },
        )

    def test_admin_profile_update_rejects_unknown_review_status(self) -> None:
        with self.assertRaises(ValidationError):
            AdminProfileUpdatePayload(reviewStatus="published")

    def test_admin_profile_update_accepts_banned_review_status(self) -> None:
        payload = AdminProfileUpdatePayload(reviewStatus="banned", isVisible=False)

        self.assertEqual(
            payload.model_dump(exclude_unset=True),
            {
                "reviewStatus": "banned",
                "isVisible": False,
            },
        )

    def test_admin_profile_update_rejects_zero_featured_rank(self) -> None:
        with self.assertRaises(ValidationError):
            AdminProfileUpdatePayload(featuredRank=0)


if __name__ == "__main__":
    unittest.main()
