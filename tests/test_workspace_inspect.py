import re
from pathlib import Path

import pytest

import harbor.core.workspace_inspect as workspace_inspect


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


def test_workspace_inspect_reports_canonical_paths_repo_relative(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "views" / "project-structure.md")

    monkeypatch.setattr(workspace_inspect, "_check_git_ignored", lambda repo_root, rel_path: False)
    report = workspace_inspect.build_workspace_inspect_report(tmp_path)
    payload = workspace_inspect.workspace_inspect_report_to_dict(report)

    assert payload["canonical_paths"]["project_structure_path"] == ".harbor/views/project-structure.md"
    assert payload["canonical_paths"]["l2_metadata_path"] == ".harbor/views/l2/_meta.json"
    assert payload["config"]["active_config"] == ".harbor/config/harbor.yaml"
    assert re.search(r"(?i)[a-z]:[\\/]", str(payload)) is None


def test_workspace_inspect_legacy_detection_roles_and_severity(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "config.yaml")
    _touch(tmp_path / ".harbor" / "l2_meta.json")
    _touch(tmp_path / "specs" / "diary" / "2026-05.jsonl", '{"summary":"legacy"}\n')
    _touch(tmp_path / "docs" / "harbor" / "project-structure.md")

    monkeypatch.setattr(workspace_inspect, "_check_git_ignored", lambda repo_root, rel_path: False)
    report = workspace_inspect.build_workspace_inspect_report(tmp_path)
    rows = {item.path: item for item in report.legacy_paths}

    assert rows[".harbor/config.yaml"].exists is True
    assert rows[".harbor/config.yaml"].role == "legacy config"
    assert rows[".harbor/config.yaml"].severity == "warn"
    assert rows[".harbor/l2_meta.json"].severity == "warn"
    assert rows["specs/diary"].severity == "warn"
    assert rows["docs/harbor"].severity == "info"
    assert rows["docs/harbor/project-structure.md"].severity == "info"


def test_workspace_inspect_git_tracking_policy(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)

    mapping = {
        ".harbor/cache": True,
        ".harbor/views/project-structure.md": False,
        "docs/design": False,
        "docs/harbor": True,
    }
    monkeypatch.setattr(workspace_inspect, "_check_git_ignored", lambda repo_root, rel_path: mapping.get(rel_path, False))
    report = workspace_inspect.build_workspace_inspect_report(tmp_path)
    rows = {item.path: item for item in report.git_tracking}

    assert rows[".harbor/cache"].ignored is True
    assert rows[".harbor/cache"].severity == "pass"
    assert rows[".harbor/views/project-structure.md"].ignored is False
    assert rows[".harbor/views/project-structure.md"].severity == "pass"
    assert rows["docs/design"].ignored is False
    assert rows["docs/design"].severity == "pass"
    assert rows["docs/harbor"].expected == "optional"
    assert rows["docs/harbor"].severity == "info"


def test_workspace_inspect_generated_views_count(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "views" / "project-structure.md")
    _touch(tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md")
    _touch(tmp_path / ".harbor" / "views" / "modules" / "harbor" / "cli" / "module-card.md")
    _touch(tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md")
    _touch(tmp_path / ".harbor" / "diary" / "2026-05.jsonl", '{"summary":"x"}\n')
    _touch(tmp_path / ".harbor" / "reports" / "dogfooding" / "a.md")
    _touch(tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md", "ref\n")

    monkeypatch.setattr(workspace_inspect, "_check_git_ignored", lambda repo_root, rel_path: False)
    report = workspace_inspect.build_workspace_inspect_report(tmp_path)

    assert report.generated_views.project_structure_exists is True
    assert report.generated_views.module_capsule_count == 2
    assert report.generated_views.l2_readme_count == 1
    assert report.generated_views.diary_file_count == 1
    assert report.generated_views.report_file_count == 1
    assert report.generated_views.skill_count == 1


def test_workspace_inspect_json_and_text_do_not_leak_absolute_paths(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "views" / "project-structure.md")
    monkeypatch.setattr(workspace_inspect, "_check_git_ignored", lambda repo_root, rel_path: "unknown")

    report = workspace_inspect.build_workspace_inspect_report(tmp_path)
    payload = workspace_inspect.workspace_inspect_report_to_dict(report)
    text = workspace_inspect.format_workspace_inspect_report(report)

    assert re.search(r"(?i)[a-z]:[\\/]", str(payload)) is None
    assert re.search(r"(?i)[a-z]:[\\/]", text) is None
    assert payload["command"] == "workspace_inspect"
    assert payload["advisory"] is True
    assert payload["writes_files"] is False


def test_workspace_inspect_is_read_only_no_writes(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_workspace_config(tmp_path)
    _touch(tmp_path / ".harbor" / "views" / "project-structure.md")
    monkeypatch.setattr(workspace_inspect, "_check_git_ignored", lambda repo_root, rel_path: False)

    def _forbidden_write(*args, **kwargs):
        raise AssertionError("write_text must not be called")

    monkeypatch.setattr(Path, "write_text", _forbidden_write, raising=False)
    report = workspace_inspect.build_workspace_inspect_report(tmp_path)
    payload = workspace_inspect.workspace_inspect_report_to_dict(report)
    assert payload["writes_files"] is False
    assert payload["advisory"] is True
