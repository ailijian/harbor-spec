import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

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
        }
    }
    idx.write_text(json.dumps(payload), encoding="utf-8")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def test_module_inspect_is_recognized(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["module", "inspect", "harbor/core"])
    assert "Module inspect: harbor/core" in out
    assert "Module: harbor/core" in out
    assert "Indexed contracts:" in out


def test_module_seal_preview_is_recognized_and_no_write(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["module", "seal", "harbor/core"])
    assert "Module seal: harbor/core" in out
    assert "Preview only. Use --write to update module capsule files under .harbor/views/modules/harbor/core." in out
    out_dir = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core"
    assert not out_dir.exists()
    assert not (tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core").exists()


def test_module_seal_write_creates_three_files(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["module", "seal", "harbor/core", "--write"])
    out_dir = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core"
    assert "Updated:" in out
    assert (out_dir / "module-card.md").exists()
    assert (out_dir / "review-checklist.md").exists()
    assert (out_dir / "debug-playbook.md").exists()

    card = (out_dir / "module-card.md").read_text(encoding="utf-8")
    checklist = (out_dir / "review-checklist.md").read_text(encoding="utf-8")
    playbook = (out_dir / "debug-playbook.md").read_text(encoding="utf-8")
    assert card.startswith("---\n")
    assert "fingerprint:" in card
    assert "# Module Card: harbor/core" in card
    assert "## Contract Checks" in checklist
    assert "## First Files to Inspect" in playbook
    assert not (tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "module-card.md").exists()


def test_module_seal_windows_style_path_normalizes_to_nested_dir(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    run_cmd(["module", "seal", r"harbor\core", "--write"])
    out_dir = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core"
    assert out_dir.exists()
    assert (out_dir / "module-card.md").exists()


def test_unknown_module_does_not_crash_and_prints_friendly_message(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out_inspect = run_cmd(["module", "inspect", "harbor/unknown"])
    out_seal = run_cmd(["module", "seal", "harbor/unknown"])
    assert "No indexed records found for module 'harbor/unknown'" in out_inspect
    assert "No indexed records found for module 'harbor/unknown'" in out_seal
