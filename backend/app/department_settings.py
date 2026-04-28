import json
from pathlib import Path


DEFAULT_DEPARTMENTS = [
    "소프트웨어과",
    "웹콘텐츠과",
    "게임콘텐츠과",
    "시각디자인과",
    "공통",
]
DEPARTMENTS_PATH = Path(__file__).resolve().parents[1] / "data" / "departments.json"


def _normalize_department(value: str) -> str:
    return str(value or "").strip()[:120]


def list_departments() -> list[str]:
    try:
        raw_departments = json.loads(DEPARTMENTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        raw_departments = DEFAULT_DEPARTMENTS

    departments = []
    seen = set()
    for item in raw_departments:
        department = _normalize_department(item)
        key = department.casefold()
        if department and key not in seen:
            departments.append(department)
            seen.add(key)
    return departments or list(DEFAULT_DEPARTMENTS)


def save_departments(departments: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for item in departments:
        department = _normalize_department(item)
        key = department.casefold()
        if department and key not in seen:
            normalized.append(department)
            seen.add(key)

    next_departments = normalized or list(DEFAULT_DEPARTMENTS)
    DEPARTMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEPARTMENTS_PATH.write_text(
        json.dumps(next_departments, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return next_departments


def add_department(name: str) -> list[str]:
    department = _normalize_department(name)
    if not department:
        return list_departments()
    return save_departments([*list_departments(), department])


def delete_department(name: str) -> list[str]:
    target = _normalize_department(name).casefold()
    if not target:
        return list_departments()
    return save_departments(
        [department for department in list_departments() if department.casefold() != target],
    )
