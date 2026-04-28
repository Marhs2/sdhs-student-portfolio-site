import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from pydantic import ValidationError


SCHEMAS_PATH = Path(__file__).resolve().parents[1] / "app" / "schemas.py"
schema_spec = spec_from_file_location("portfolio_backend_schemas", SCHEMAS_PATH)
schema_module = module_from_spec(schema_spec)
assert schema_spec.loader is not None
schema_spec.loader.exec_module(schema_module)
ProfilePayload = schema_module.ProfilePayload


def build_profile_payload(**overrides):
    payload = {
        "name": "테스트 학생",
        "description": "프로필 생성 동의 테스트",
        "job": "Full Stack",
        "school": "서울디지텍고등학교",
        "department": "웹솔루션과",
        "tags": ["vue"],
        "github": "https://github.com/example",
        "imageUrl": "",
    }
    payload.update(overrides)
    return payload


class ProfileCreationConsentTests(unittest.TestCase):
    def test_profile_creation_requires_checked_consent(self) -> None:
        with self.assertRaises(ValidationError):
            ProfilePayload(**build_profile_payload())

        with self.assertRaises(ValidationError):
            ProfilePayload(**build_profile_payload(createProfileConsent=False))

    def test_profile_creation_accepts_checked_consent(self) -> None:
        payload = ProfilePayload(**build_profile_payload(createProfileConsent=True))

        self.assertTrue(payload.createProfileConsent)

    def test_profile_creation_accepts_private_visibility(self) -> None:
        payload = ProfilePayload(
            **build_profile_payload(createProfileConsent=True, isVisible=False)
        )

        self.assertFalse(payload.isVisible)

    def test_profile_creation_ignores_admin_managed_taxonomy(self) -> None:
        payload = ProfilePayload(**build_profile_payload(createProfileConsent=True))
        dumped = payload.model_dump()

        self.assertNotIn("school", dumped)
        self.assertNotIn("department", dumped)
        self.assertNotIn("track", dumped)


if __name__ == "__main__":
    unittest.main()
