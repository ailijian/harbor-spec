import hashlib
import json
import re
from pathlib import Path

import pytest

import harbor.core.workspace_migrate as workspace_migrate


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def _write_workspace_config(tmp_path: Path) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n  - harbor/**\n", encoding="utf-8")


def _touch(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fingerprint_tree(root: Path) -> str:
    hasher = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def test_workspace_migrate_dry_run_no_writes(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "config.yaml")
    _touch(tmp_path / ".harbor" / "l2_meta.json")
    _touch(tmp_path / "specs" / "diary" / "2026-05.jsonl", '{"summary":"legacy"}\n')
    _touch(tmp_path / "docs" / "harbor" / "index.md", "x\n")
    _touch(tmp_path / "harbor" / "core" / "README.md", "# core\n")
    _touch(tmp_path / "harbor" / "core" / "sync.py", "def x():\n    return 1\n")

    before = _fingerprint_tree(tmp_path)
    report = workspace_migrate.build_workspace_migrate_dry_run_report(tmp_path)
    payload = workspace_migrate.workspace_migrate_report_to_dict(report)
    _ = workspace_migrate.format_workspace_migrate_report(report)
    after = _fingerprint_tree(tmp_path)

    assert before == after
    assert payload["writes_files"] is False
    assert payload["mode"] == "dry_run"


def test_workspace_migrate_legacy_config_plan_item(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "config.yaml")

    report = workspace_migrate.build_workspace_migrate_dry_run_report(tmp_path)
    rows = {item.id: item for item in report.plan_items}
    item = rows["legacy_config"]
    assert item.status == "detected"
    assert item.action == "manual_review"
    assert item.automatic is False
    assert item.source == ".harbor/config.yaml"
    assert item.target == ".harbor/config/harbor.yaml"


def test_workspace_migrate_legacy_l2_metadata_plan_item(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "l2_meta.json")

    report = workspace_migrate.build_workspace_migrate_dry_run_report(tmp_path)
    rows = {item.id: item for item in report.plan_items}
    item = rows["legacy_l2_metadata"]
    assert item.status == "detected"
    assert item.action == "manual_review"
    assert item.automatic is False
    assert item.source == ".harbor/l2_meta.json"
    assert item.target == ".harbor/views/l2/_meta.json"


def test_workspace_migrate_legacy_diary_plan_item_high_risk(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / "specs" / "diary" / "2026-05.jsonl", '{"summary":"legacy"}\n')

    report = workspace_migrate.build_workspace_migrate_dry_run_report(tmp_path)
    rows = {item.id: item for item in report.plan_items}
    item = rows["legacy_diary"]
    assert item.status == "detected"
    assert item.action == "manual_merge_required"
    assert item.risk == "high"
    assert item.automatic is False
    assert "must be merged/deduped" in item.reason


def test_workspace_migrate_docs_export_plan_item_no_action(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / "docs" / "harbor" / "project-structure.md", "# x\n")

    report = workspace_migrate.build_workspace_migrate_dry_run_report(tmp_path)
    rows = {item.id: item for item in report.plan_items}
    item = rows["docs_export"]
    assert item.status == "detected"
    assert item.action == "no_action"
    assert item.automatic is False
    assert "optional export" in item.reason


def test_workspace_migrate_module_readme_export_items(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / "harbor" / "core" / "README.md", "# core\n")
    _touch(tmp_path / "harbor" / "core" / "sync.py", "def check_status():\n    return {}\n")
    _touch(tmp_path / "docs" / "x" / "README.md", "# doc\n")

    report = workspace_migrate.build_workspace_migrate_dry_run_report(tmp_path)
    module_items = [item for item in report.plan_items if item.category == "module_readme_export"]
    assert any(item.source == "harbor/core/README.md" for item in module_items)
    target_rows = [item for item in module_items if item.source == "harbor/core/README.md"]
    assert len(target_rows) == 1
    assert target_rows[0].action == "no_action"
    assert target_rows[0].automatic is False
    assert target_rows[0].target == ".harbor/views/l2/harbor/core/README.md"
    assert all(not item.source.startswith("docs/") for item in module_items)


def test_workspace_migrate_json_has_no_absolute_paths(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "config.yaml")
    _touch(tmp_path / "harbor" / "core" / "README.md", "# core\n")
    _touch(tmp_path / "harbor" / "core" / "sync.py", "def check_status():\n    return {}\n")

    report = workspace_migrate.build_workspace_migrate_dry_run_report(tmp_path)
    payload = workspace_migrate.workspace_migrate_report_to_dict(report)
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)

    assert re.search(r"(?i)[a-z]:[\\/]", dumped) is None
    assert payload["writes_files"] is False
