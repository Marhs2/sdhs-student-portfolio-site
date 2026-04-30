import ast
import unittest
from pathlib import Path


APP_INIT_PATH = Path(__file__).resolve().parents[1] / "app" / "__init__.py"


class CorsPolicyTests(unittest.TestCase):
    def test_cors_preflight_allows_delete_requests(self) -> None:
        module = ast.parse(APP_INIT_PATH.read_text(encoding="utf-8"))
        allow_methods = []

        for node in ast.walk(module):
            if not isinstance(node, ast.keyword) or node.arg != "allow_methods":
                continue
            if isinstance(node.value, ast.List):
                allow_methods = [
                    item.value
                    for item in node.value.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                ]

        self.assertTrue("*" in allow_methods or "DELETE" in allow_methods)

    def test_cors_preflight_cache_is_enabled(self) -> None:
        module = ast.parse(APP_INIT_PATH.read_text(encoding="utf-8"))
        max_age = None

        for node in ast.walk(module):
            if not isinstance(node, ast.keyword) or node.arg != "max_age":
                continue
            if isinstance(node.value, ast.Constant):
                max_age = node.value.value

        self.assertGreaterEqual(max_age, 600)


if __name__ == "__main__":
    unittest.main()
