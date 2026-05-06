import json
from pathlib import Path

from harbor.core.module_capsule import collect_module_context
from harbor.core.stale import (
    check_l2_readme_stale,
    check_module_derived_views_stale,
)


def _write_index(tmp_path: Path) -> None:
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": {
            "harbor/core/sync.py": {
                "items": [
                    {
                        "id": "harbor.core.sync.SyncEngine.check_status",
                        "qualified_name": "SyncEngine.check_status",
                        "scope": "public",
                        "strictness": "standard",
                    }
                ]
            }
        }
    }
    idx.write_text(json.dumps(payload), encoding="utf-8")


def test_l2_readme_stale_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    result = check_l2_readme_stale("harbor/core")
    assert result.status == "stale"
    assert result.reason == "README.md not found"
    assert result.suggested_command == "harbor docs --module harbor/core --write"


def test_l2_readme_up_to_date_when_content_matches_except_timestamp(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    readme = tmp_path / "harbor" / "core" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        "A\nGenerated At: 2020-01-01T00:00:00Z\nB\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "A\nGenerated At: 2026-01-01T00:00:00Z\nB\n",
    )
    result = check_l2_readme_stale("harbor/core")
    assert result.status == "up_to_date"


def test_l2_readme_stale_when_content_differs(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    readme = tmp_path / "harbor" / "core" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text("OLD\n", encoding="utf-8")
    monkeypatch.setattr("harbor.core.stale.L2Generator.generate", lambda self, module: "NEW\n")
    result = check_l2_readme_stale("harbor/core")
    assert result.status == "stale"
    assert result.reason == "README content mismatch"


def test_l2_readme_unknown_when_no_indexed_records(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    result = check_l2_readme_stale("harbor/unknown")
    assert result.status == "unknown"
    assert result.reason == "no indexed records found for module"
    assert result.suggested_command is None


def test_l2_readme_check_does_not_write_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    readme = tmp_path / "harbor" / "core" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    original = "SAME\nGenerated At: 2020-01-01T00:00:00Z\n"
    readme.write_text(original, encoding="utf-8")
    before = readme.read_text(encoding="utf-8")
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "SAME\nGenerated At: 2026-01-01T00:00:00Z\n",
    )
    _ = check_l2_readme_stale("harbor/core")
    after = readme.read_text(encoding="utf-8")
    assert before == after


def test_check_module_derived_views_stale_returns_both_views(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    monkeypatch.setattr("harbor.core.stale.L2Generator.generate", lambda self, module: "NEW\n")
    summary = check_module_derived_views_stale("harbor/core")
    assert summary.module == "harbor/core"
    assert summary.l2_readme.view == "L2 README"
    assert summary.l2_readme.status == "stale"
    assert summary.module_capsule.view == "Module Capsule"
    assert summary.module_capsule.status == "stale"
    assert summary.module_capsule.reason == "module-card.md not found"

