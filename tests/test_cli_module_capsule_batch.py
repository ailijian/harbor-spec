import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


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
            },
            "harbor/core/l2.py": {
                "items": [
                    {
                        "id": "harbor.core.l2.L2Generator.generate",
                        "qualified_name": "L2Generator.generate",
                        "scope": "public",
                        "strictness": "standard",
                    }
                ]
            },
            "harbor/cli/main.py": {
                "items": [
                    {
                        "id": "harbor.cli.main.main",
                        "qualified_name": "main",
                        "scope": "public",
                        "strictness": "standard",
                    }
                ]
            },
            "harbor/empty/skip.py": {"items": []},
        }
    }
    idx.write_text(json.dumps(payload), encoding="utf-8")


def _empty_status_report():
    return SimpleNamespace(
        drift=[],
        modified=[],
        contract_changed=[],
        untracked=[],
        missing=[],
    )


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def test_module_seal_changed_and_all_args_are_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: [])

    out_changed = run_cmd(["module", "seal", "--changed"])
    out_all = run_cmd(["module", "seal", "--all"])

    assert "No changed modules detected" in out_changed
    assert "No indexed modules found" in out_all


def test_module_seal_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        run_cmd(["module", "seal", "harbor/core", "--changed"])
    with pytest.raises(SystemExit):
        run_cmd(["module", "seal", "harbor/core", "--all"])
    with pytest.raises(SystemExit):
        run_cmd(["module", "seal", "--changed", "--all"])


def test_module_inspect_and_single_seal_behavior_unchanged(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)

    out_inspect = run_cmd(["module", "inspect", "harbor/core"])
    out_single = run_cmd(["module", "seal", "harbor/core"])

    assert "Module inspect: harbor/core" in out_inspect
    assert "Module seal: harbor/core" in out_single
    assert "Preview only. Use --write to update module capsule files." in out_single


def test_module_seal_changed_dedup_sort_and_windows_path_preview(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path=r"harbor\core\sync.py")],
        modified=[SimpleNamespace(file_path="harbor/core/l2.py")],
        contract_changed=[SimpleNamespace(file_path="harbor/cli/main.py")],
        untracked=[SimpleNamespace(file_path="harbor/core/new_file.py")],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)

    out = run_cmd(["module", "seal", "--changed"])
    assert "Changed modules detected:" in out
    assert "- harbor/cli" in out
    assert "- harbor/core" in out
    assert out.index("- harbor/cli") < out.index("- harbor/core")
    assert "Preview only. Use --write to update module capsule files." in out

    out_dir = tmp_path / "docs" / "harbor" / "modules"
    assert not out_dir.exists()


def test_module_seal_changed_no_modules_friendly_and_no_write(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())

    out = run_cmd(["module", "seal", "--changed"])
    assert "No changed modules detected. Module capsules are up to date." in out
    assert not (tmp_path / "docs").exists()


def test_module_seal_all_discovers_indexed_modules_only_and_stable_order(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)

    out = run_cmd(["module", "seal", "--all"])
    assert "Generating Module Capsules for all indexed modules:" in out
    assert "- harbor/cli" in out
    assert "- harbor/core" in out
    assert "- harbor/empty" not in out
    assert out.index("- harbor/cli") < out.index("- harbor/core")
    assert "Preview only. Use --write to update module capsule files." in out
    assert not (tmp_path / "docs").exists()


def test_module_seal_all_none_friendly(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: [])
    out = run_cmd(["module", "seal", "--all"])
    assert "No indexed modules found. Nothing to seal." in out


def test_module_seal_changed_write_creates_three_files_per_module(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
        modified=[SimpleNamespace(file_path="harbor/cli/main.py")],
        contract_changed=[],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)

    out = run_cmd(["module", "seal", "--changed", "--write"])
    assert "Updated:" in out

    expected = [
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "module-card.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "review-checklist.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "debug-playbook.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "cli" / "module-card.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "cli" / "review-checklist.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "cli" / "debug-playbook.md",
    ]
    for p in expected:
        assert p.exists()
        assert p.as_posix().replace(str(tmp_path).replace("\\", "/") + "/", "") in out


def test_module_seal_all_write_creates_three_files_per_module(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)

    out = run_cmd(["module", "seal", "--all", "--write"])
    assert "Updated:" in out

    expected = [
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "module-card.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "review-checklist.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "debug-playbook.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "cli" / "module-card.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "cli" / "review-checklist.md",
        tmp_path / "docs" / "harbor" / "modules" / "harbor" / "cli" / "debug-playbook.md",
    ]
    for p in expected:
        assert p.exists()
        assert p.as_posix().replace(str(tmp_path).replace("\\", "/") + "/", "") in out
