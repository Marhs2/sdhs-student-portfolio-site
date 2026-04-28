import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


NORMALIZATION_PATH = Path(__file__).resolve().parents[1] / "app" / "normalization.py"
normalization_spec = spec_from_file_location("portfolio_backend_normalization", NORMALIZATION_PATH)
normalization_module = module_from_spec(normalization_spec)
assert normalization_spec.loader is not None
normalization_spec.loader.exec_module(normalization_module)
normalize_portfolio_item_record = normalization_module.normalize_portfolio_item_record
normalize_profile_record = normalization_module.normalize_profile_record


class ProfileContractTests(unittest.TestCase):
    def test_normalize_profile_record_exposes_student_metadata(self) -> None:
        record = {
            "id": 7,
            "name": "Kim Minji",
            "des": "Graduation project curator",
            "job": "Frontend Developer",
            "school": "Hongik University",
            "department": "Visual Communication",
            "track": "Interactive Media",
            "tags": ["vue", "branding"],
            "featured_rank": 2,
            "review_status": "approved",
            "is_visible": True,
        }

        normalized = normalize_profile_record(record)

        self.assertEqual(normalized["school"], "Hongik University")
        self.assertEqual(normalized["department"], "Visual Communication")
        self.assertEqual(normalized["track"], "Interactive Media")
        self.assertEqual(normalized["tags"], ["vue", "branding"])
        self.assertEqual(normalized["featuredRank"], 2)
        self.assertEqual(normalized["reviewStatus"], "approved")
        self.assertTrue(normalized["isVisible"])

    def test_normalize_portfolio_item_record_exposes_project_metadata(self) -> None:
        record = {
            "id": 9,
            "title": "Exhibition Kiosk",
            "des": "Interactive kiosk for exhibition guests",
            "project_role": "UI / Motion",
            "skill_tags": ["vue", "figma"],
            "is_featured": True,
            "custom_link_url": "https://demo.example.com",
        }

        normalized = normalize_portfolio_item_record(record)

        self.assertEqual(normalized["contribution"], "UI / Motion")
        self.assertEqual(normalized["tags"], ["vue", "figma"])
        self.assertTrue(normalized["isFeatured"])
        self.assertEqual(normalized["websiteUrl"], "https://demo.example.com")

    def test_normalize_portfolio_item_record_rejects_unsafe_custom_link(self) -> None:
        record = {
            "id": 10,
            "title": "Unsafe Demo",
            "custom_link_url": "javascript:alert(1)",
        }

        normalized = normalize_portfolio_item_record(record)

        self.assertEqual(normalized["websiteUrl"], "")

    def test_normalize_profile_record_hides_email_by_default(self) -> None:
        record = {
            "id": 3,
            "name": "Lee",
            "email": "lee@example.com",
        }

        normalized = normalize_profile_record(record)

        self.assertNotIn("email", normalized)

    def test_normalize_profile_record_treats_legacy_visibility_fields_as_public(self) -> None:
        record = {
            "id": 4,
            "name": "Park",
            "review_status": None,
            "is_visible": None,
        }

        normalized = normalize_profile_record(record)

        self.assertEqual(normalized["reviewStatus"], "approved")
        self.assertTrue(normalized["isVisible"])

    def test_normalize_profile_record_keeps_explicit_private_states(self) -> None:
        record = {
            "id": 5,
            "name": "Choi",
            "review_status": "draft",
            "is_visible": False,
        }

        normalized = normalize_profile_record(record)

        self.assertEqual(normalized["reviewStatus"], "draft")
        self.assertFalse(normalized["isVisible"])


if __name__ == "__main__":
    unittest.main()
