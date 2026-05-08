import os
import unittest

from pathlib import Path

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")

from backend.app.routers.uploads import (
    _detect_supported_image_content_type,
    _profile_image_file_name,
    _profile_image_file_path,
    _profile_image_public_url,
)


class UploadImageDetectionTests(unittest.TestCase):
    def test_detects_supported_image_signatures(self) -> None:
        self.assertEqual(
            _detect_supported_image_content_type(b"\xff\xd8\xff\xe0\x00\x10JFIF"),
            "image/jpeg",
        )
        self.assertEqual(
            _detect_supported_image_content_type(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            ),
            "image/png",
        )
        self.assertEqual(
            _detect_supported_image_content_type(b"RIFF\x24\x00\x00\x00WEBPVP8 "),
            "image/webp",
        )

    def test_rejects_unknown_signature(self) -> None:
        self.assertEqual(_detect_supported_image_content_type(b"not an image"), "")

    def test_profile_image_file_name_uses_safe_server_generated_stem(self) -> None:
        self.assertEqual(
            _profile_image_file_name(".webp", stem="abc123"),
            "abc123.webp",
        )

    def test_profile_image_file_name_rejects_unsafe_input(self) -> None:
        with self.assertRaises(ValueError):
            _profile_image_file_name("../evil", stem="abc123")
        with self.assertRaises(ValueError):
            _profile_image_file_name(".webp", stem="../user")

    def test_profile_image_file_path_stays_under_upload_root(self) -> None:
        self.assertEqual(
            _profile_image_file_path(Path("/uploads"), "abc123.webp"),
            Path("/uploads/profiles/abc123.webp").resolve(),
        )

    def test_profile_image_public_url_uses_relative_upload_path(self) -> None:
        self.assertEqual(
            _profile_image_public_url("abc123.webp", version_ms=123),
            "/uploads/profiles/abc123.webp?v=123",
        )


if __name__ == "__main__":
    unittest.main()
