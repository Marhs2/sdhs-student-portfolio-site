import unittest
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)

CONFIG_PATH = Path(__file__).resolve().parents[1] / "app" / "config.py"
config_spec = spec_from_file_location("portfolio_backend_config", CONFIG_PATH)
config_module = module_from_spec(config_spec)
assert config_spec.loader is not None
config_spec.loader.exec_module(config_module)


class LocalOnlySupabaseConfigTests(unittest.TestCase):
    def test_local_only_supabase_allows_local_origins(self) -> None:
        config_module._assert_local_only_supabase_project(
            "https://lbayyiylxjvqhcqejvkr.supabase.co",
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        )

    def test_local_only_supabase_rejects_non_local_origins(self) -> None:
        with self.assertRaises(RuntimeError):
            config_module._assert_local_only_supabase_project(
                "https://lbayyiylxjvqhcqejvkr.supabase.co",
                ["https://test.example.com"],
            )

    def test_other_supabase_projects_can_use_non_local_origins(self) -> None:
        config_module._assert_local_only_supabase_project(
            "https://example.supabase.co",
            ["https://portfolio.example.com"],
        )


if __name__ == "__main__":
    unittest.main()
