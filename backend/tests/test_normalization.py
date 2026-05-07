import unittest

from backend.app.normalization import clean_github_url, clean_http_url, clean_rich_html, clean_youtube_url, normalize_job


class NormalizationTests(unittest.TestCase):
    def test_normalize_job_maps_legacy_value(self) -> None:
        self.assertEqual(normalize_job("frontenddeveloper"), "프론트엔드")

    def test_clean_rich_html_removes_scripts(self) -> None:
        cleaned = clean_rich_html('<div>Hello</div><script>alert("x")</script>')
        self.assertEqual(cleaned, "<div>Hello</div>")

    def test_clean_rich_html_removes_active_content_and_dangerous_urls(self) -> None:
        cleaned = clean_rich_html(
            """
            <section onclick="alert(1)" style="background:url(javascript:alert(1))">
              <iframe srcdoc="<script>alert(1)</script>"></iframe>
              <a href="javascript:alert(1)">link</a>
              <img src="data:text/html,<script>alert(1)</script>" onerror="alert(1)">
              <p>Safe</p>
            </section>
            """,
        )

        self.assertNotIn("onclick", cleaned.lower())
        self.assertNotIn("style=", cleaned.lower())
        self.assertNotIn("<iframe", cleaned.lower())
        self.assertNotIn("javascript:", cleaned.lower())
        self.assertNotIn("data:text/html", cleaned.lower())
        self.assertNotIn("<img", cleaned.lower())
        self.assertIn("<p>Safe</p>", cleaned)

    def test_clean_rich_html_rejects_obfuscated_javascript_urls(self) -> None:
        cleaned = clean_rich_html(
            '<a href="java&#x73;cript:alert(1)">encoded</a>'
            '<a href="java\tscript:alert(1)">control</a>'
            '<a href="https://example.com/profile">safe</a>'
        )

        self.assertNotIn("javascript:", cleaned.lower())
        self.assertIn("<a>encoded</a>", cleaned)
        self.assertIn("<a>control</a>", cleaned)
        self.assertIn('href="https://example.com/profile"', cleaned)
        self.assertIn('rel="noopener noreferrer nofollow"', cleaned)

    def test_url_cleaners_reject_dangerous_or_wrong_hosts(self) -> None:
        self.assertEqual(clean_http_url("javascript:alert(1)"), "")
        self.assertEqual(clean_http_url("https://example.com/image.png"), "https://example.com/image.png")
        self.assertEqual(clean_github_url("https://github.com/student"), "https://github.com/student")
        self.assertEqual(clean_github_url("https://evil.example/student"), "")
        self.assertEqual(clean_youtube_url("https://youtu.be/abc123"), "https://youtu.be/abc123")
        self.assertEqual(clean_youtube_url("https://vimeo.com/abc123"), "")

    def test_clean_http_url_allows_local_upload_paths(self) -> None:
        self.assertEqual(
            clean_http_url("/uploads/profiles/student-1.webp?v=123"),
            "/uploads/profiles/student-1.webp?v=123",
        )
        self.assertEqual(clean_http_url("/api/admin/settings"), "")
        self.assertEqual(clean_http_url("//evil.example/avatar.webp"), "")


if __name__ == "__main__":
    unittest.main()
