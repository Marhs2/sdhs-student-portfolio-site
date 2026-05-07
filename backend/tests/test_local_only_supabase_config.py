import unittest
import sys
import types
from unittest.mock import patch
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

    def test_split_supabase_settings_use_auth_and_db_projects(self) -> None:
        config_module.get_settings.cache_clear()

        with patch.dict(
            "os.environ",
            {
                "SUPABASE_AUTH_URL": "https://auth-project.supabase.co",
                "SUPABASE_AUTH_SERVICE_ROLE_KEY": "auth-service-role",
                "SUPABASE_DB_URL": "http://127.0.0.1:54321",
                "SUPABASE_DB_SERVICE_ROLE_KEY": "db-service-role",
                "PORTFOLIO_ALLOWED_ORIGINS": "http://127.0.0.1:5173",
            },
            clear=True,
        ):
            settings = config_module.get_settings()

        self.assertEqual(settings.supabase_auth_url, "https://auth-project.supabase.co")
        self.assertEqual(settings.supabase_auth_service_role_key, "auth-service-role")
        self.assertEqual(settings.supabase_db_url, "http://127.0.0.1:54321")
        self.assertEqual(settings.supabase_db_service_role_key, "db-service-role")

    def test_split_supabase_settings_fall_back_to_legacy_project(self) -> None:
        config_module.get_settings.cache_clear()

        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://legacy-project.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "legacy-service-role",
                "PORTFOLIO_ALLOWED_ORIGINS": "http://127.0.0.1:5173",
            },
            clear=True,
        ):
            settings = config_module.get_settings()

        self.assertEqual(settings.supabase_auth_url, "https://legacy-project.supabase.co")
        self.assertEqual(settings.supabase_auth_service_role_key, "legacy-service-role")
        self.assertEqual(settings.supabase_db_url, "https://legacy-project.supabase.co")
        self.assertEqual(settings.supabase_db_service_role_key, "legacy-service-role")

    def test_local_only_guard_checks_auth_project_not_local_db_project(self) -> None:
        config_module.get_settings.cache_clear()

        with patch.dict(
            "os.environ",
            {
                "SUPABASE_AUTH_URL": "https://lbayyiylxjvqhcqejvkr.supabase.co",
                "SUPABASE_AUTH_SERVICE_ROLE_KEY": "auth-service-role",
                "SUPABASE_DB_URL": "http://127.0.0.1:54321",
                "SUPABASE_DB_SERVICE_ROLE_KEY": "db-service-role",
                "PORTFOLIO_ALLOWED_ORIGINS": "https://portfolio.example.com",
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                config_module.get_settings()

    def tearDown(self) -> None:
        config_module.get_settings.cache_clear()


if __name__ == "__main__":
    unittest.main()
