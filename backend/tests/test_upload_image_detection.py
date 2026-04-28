import unittest

from backend.app.routers.uploads import _detect_supported_image_content_type


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


if __name__ == "__main__":
    unittest.main()
