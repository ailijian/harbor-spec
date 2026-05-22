import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
import yaml

import harbor.cli.main as cli_main
from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def _write_index(tmp_path: Path) -> None:
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        json.dumps(
            {
                "files": {
                    "harbor/core/sync.py": {"items": [{"id": "x"}]},
                    "harbor/cli/main.py": {"items": [{"id": "y"}]},
                }
            }
        ),
        encoding="utf-8",
    )


def _write_workspace_config(tmp_path: Path, payload: dict) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def test_project_structure_preview_runs_and_does_not_write(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["project", "structure"])
    assert "# Project Structure" in out
    assert "## Discovery Mode" in out
    assert "## Code Modules" in out
    assert "## Supporting Areas" in out
    assert "## Module Index" not in out
    assert "| Mode | Harbor index |" in out
    assert "| Module | Key Files | L2 README | Canonical Capsule | Docs Export | Skill |" in out
    assert "Preview only. Use --write to update .harbor/views/project-structure.md." in out
    assert not (tmp_path / ".harbor" / "views" / "project-structure.md").exists()
    assert not (tmp_path / "docs" / "harbor" / "project-structure.md").exists()


def test_project_structure_write_updates_canonical_path_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["project", "structure", "--write"])
    target = tmp_path / ".harbor" / "views" / "project-structure.md"
    assert "Updated:" in out
    assert "- .harbor/views/project-structure.md" in out
    assert target.exists()
    assert not (tmp_path / "docs" / "harbor" / "project-structure.md").exists()
    content = target.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert 'view_type: "project_structure"' in content
    assert "# Project Structure" in content


def test_project_structure_repeat_write_keeps_generated_at_when_no_change(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _ = run_cmd(["project", "structure", "--write"])
    target = tmp_path / ".harbor" / "views" / "project-structure.md"
    first = target.read_text(encoding="utf-8")
    _ = run_cmd(["project", "structure", "--write"])
    second = target.read_text(encoding="utf-8")
    assert first == second


def test_project_structure_write_dual_writes_when_docs_export_enabled(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_workspace_config(
        tmp_path,
        {
            "views": {
                "export": {
                    "docs": {
                        "enabled": True,
                        "root": "docs/harbor",
                    }
                }
            }
        },
    )
    out = run_cmd(["project", "structure", "--write"])
    canonical_target = tmp_path / ".harbor" / "views" / "project-structure.md"
    docs_target = tmp_path / "docs" / "harbor" / "project-structure.md"

    assert canonical_target.exists()
    assert docs_target.exists()
    assert "- .harbor/views/project-structure.md" in out
    assert "- docs/harbor/project-structure.md" in out
    assert out.index("- .harbor/views/project-structure.md") < out.index("- docs/harbor/project-structure.md")


def test_project_structure_write_does_not_overwrite_existing_legacy_docs_when_export_disabled(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    legacy_target = tmp_path / "docs" / "harbor" / "project-structure.md"
    legacy_target.parent.mkdir(parents=True, exist_ok=True)
    legacy_target.write_text("legacy-content\n", encoding="utf-8")
    before = legacy_target.read_text(encoding="utf-8")

    out = run_cmd(["project", "structure", "--write"])
    canonical_target = tmp_path / ".harbor" / "views" / "project-structure.md"

    assert canonical_target.exists()
    assert "- .harbor/views/project-structure.md" in out
    assert "- docs/harbor/project-structure.md" not in out
    assert legacy_target.exists()
    assert legacy_target.read_text(encoding="utf-8") == before


def test_project_structure_no_index_is_friendly_and_not_crash_when_no_filesystem_fallback(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_cmd(["project", "structure"])
    assert "No indexed modules found. Generated a metadata-only project structure view." in out
    assert "# Project Structure" in out


def test_project_structure_filesystem_fallback_generates_non_empty_key_areas_and_modules(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "harbor" / "cli").mkdir(parents=True, exist_ok=True)
    (tmp_path / "harbor" / "core").mkdir(parents=True, exist_ok=True)
    (tmp_path / "harbor" / "utils").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "harbor" / "cli" / "main.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (tmp_path / "harbor" / "core" / "a.py").write_text("def a():\n    pass\n", encoding="utf-8")
    (tmp_path / "harbor" / "utils" / "u.py").write_text("def u():\n    pass\n", encoding="utf-8")
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    out = run_cmd(["project", "structure"])
    assert "| harbor/cli |" in out
    assert "| harbor/core |" in out
    assert "| harbor/utils |" in out
    assert "| tests |" in out
    assert "| Mode | Harbor index |" in out
    assert "contract counts may be 0 because no Harbor index records were available" in out
    assert "| - | No indexed files found. | 0 | 0 |" not in out
    assert "No indexed modules found. Generated a metadata-only project structure view." not in out


def test_project_structure_does_not_trigger_other_side_effect_paths(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    calls = {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0}
    monkeypatch.setattr(
        cli_main.L2Generator,
        "write",
        lambda self, module, md, force=False: calls.__setitem__("docs_write", calls["docs_write"] + 1),
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_capsule",
        lambda context: calls.__setitem__("capsule_write", calls["capsule_write"] + 1),
    )
    monkeypatch.setattr(
        cli_main.IndexBuilder,
        "iter_build",
        lambda self, incremental=True: calls.__setitem__("lock", calls["lock"] + 1) or iter([]),
    )
    monkeypatch.setattr(
        cli_main.DiaryManager,
        "log",
        lambda self, **kwargs: calls.__setitem__("log", calls["log"] + 1),
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_skill",
        lambda module: calls.__setitem__("promote", calls["promote"] + 1),
    )
    _ = run_cmd(["project", "structure", "--write"])
    assert calls == {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0}
    assert not (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / "project-rules.md").exists()
    assert not list((tmp_path / ".harbor").glob("*.yaml"))
    assert not (tmp_path / "docs" / "harbor" / "modules").exists()
    assert not (tmp_path / ".agents" / "skills").exists()
