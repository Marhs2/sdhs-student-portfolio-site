from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


DEPARTMENT_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "app" / "department_settings.py"
department_settings_spec = spec_from_file_location(
    "portfolio_backend_department_settings",
    DEPARTMENT_SETTINGS_PATH,
)
department_settings = module_from_spec(department_settings_spec)
assert department_settings_spec.loader is not None
department_settings_spec.loader.exec_module(department_settings)


def test_department_settings_add_and_delete_round_trip(tmp_path, monkeypatch):
    departments_path = tmp_path / "departments.json"
    monkeypatch.setattr(department_settings, "DEPARTMENTS_PATH", departments_path)

    added = department_settings.add_department("AI융합과")
    duplicated = department_settings.add_department(" ai융합과 ")
    deleted = department_settings.delete_department("AI융합과")

    assert "AI융합과" in added
    assert duplicated.count("AI융합과") == 1
    assert "AI융합과" not in deleted
    assert departments_path.exists()
