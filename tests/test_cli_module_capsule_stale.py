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


def test_module_stale_args_are_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: [])
    out_changed = run_cmd(["module", "stale", "--changed"])
    out_all = run_cmd(["module", "stale", "--all"])
    assert "No changed modules detected" in out_changed
    assert "No indexed modules found" in out_all


def test_module_stale_single_missing_module_card(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["module", "stale", "harbor/core"])
    assert "Module Capsule Status: harbor/core" in out
    assert "- Status: stale" in out
    assert "- Reason: module-card.md not found" in out
    assert "harbor module seal harbor/core --write" in out


def test_module_stale_single_fingerprint_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out_dir = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "module-card.md").write_text("# Module Card: harbor/core\n", encoding="utf-8")
    out = run_cmd(["module", "stale", "harbor/core"])
    assert "- Status: stale" in out
    assert "- Reason: fingerprint missing" in out


def test_module_stale_single_up_to_date(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    run_cmd(["module", "seal", "harbor/core", "--write"])
    out = run_cmd(["module", "stale", "harbor/core"])
    assert "- Status: up to date" in out
    assert "- Fingerprint: " in out


def test_module_stale_single_mismatch(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    run_cmd(["module", "seal", "harbor/core", "--write"])
    card = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md"
    card.write_text(card.read_text(encoding="utf-8").replace("fingerprint:", "fingerprint: deadbeef"), encoding="utf-8")
    out = run_cmd(["module", "stale", "harbor/core"])
    assert "- Status: stale" in out
    assert "- Reason: fingerprint mismatch" in out


def test_module_stale_unknown_module_friendly(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    out = run_cmd(["module", "stale", "harbor/unknown"])
    assert "Module Capsule Status: harbor/unknown" in out
    assert "- Status: stale" in out
    assert "- Reason: no indexed records found for module" in out


def test_module_stale_changed_checks_each_module_and_windows_path(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    run_cmd(["module", "seal", "harbor/core", "--write"])
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path=r"harbor\core\sync.py")],
        modified=[SimpleNamespace(file_path="harbor/cli/main.py")],
        contract_changed=[],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    out = run_cmd(["module", "stale", "--changed"])
    assert "Checking stale Module Capsules for changed modules:" in out
    assert "- harbor/cli: stale" in out
    assert "- harbor/core: up to date" in out
    assert out.index("- harbor/cli") < out.index("- harbor/core")


def test_module_stale_treats_legacy_existing_but_canonical_missing_as_stale(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    legacy = tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "module-card.md").write_text("legacy\n", encoding="utf-8")
    out = run_cmd(["module", "stale", "harbor/core"])
    assert "- Status: stale" in out
    assert "- Reason: module-card.md not found" in out


def test_module_stale_all_checks_all_modules_stable_order(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    run_cmd(["module", "seal", "harbor/core", "--write"])
    out = run_cmd(["module", "stale", "--all"])
    assert "Checking stale Module Capsules for all indexed modules:" in out
    assert "- harbor/cli: stale" in out
    assert "- harbor/core: up to date" in out
    assert out.index("- harbor/cli") < out.index("- harbor/core")


def test_module_stale_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        run_cmd(["module", "stale", "harbor/core", "--changed"])
    with pytest.raises(SystemExit):
        run_cmd(["module", "stale", "harbor/core", "--all"])
    with pytest.raises(SystemExit):
        run_cmd(["module", "stale", "--changed", "--all"])


def test_module_stale_does_not_accept_write():
    with pytest.raises(SystemExit):
        run_cmd(["module", "stale", "harbor/core", "--write"])
