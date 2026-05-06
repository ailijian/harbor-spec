import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.l2 import collect_all_indexed_modules, infer_module_from_path


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _empty_status_report():
    return SimpleNamespace(
        drift=[],
        modified=[],
        contract_changed=[],
        untracked=[],
        missing=[],
    )


def test_docs_changed_and_all_args_are_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: [])

    out_changed = run_cmd(["docs", "--changed"])
    out_all = run_cmd(["docs", "--all"])

    assert "No changed modules detected" in out_changed
    assert "No indexed modules found" in out_all


def test_docs_mode_flags_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        run_cmd(["docs", "--module", "harbor/core", "--changed"])
    with pytest.raises(SystemExit):
        run_cmd(["docs", "--changed", "--all"])
    with pytest.raises(SystemExit):
        run_cmd(["docs", "--module", "harbor/core", "--all"])


def test_docs_module_mode_still_works(monkeypatch):
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}")
    out = run_cmd(["docs", "--module", "harbor/core"])
    assert "# Module: harbor/core" in out


def test_infer_module_from_path_supports_windows_and_posix():
    assert infer_module_from_path(r"harbor\core\sync.py") == "harbor/core"
    assert infer_module_from_path("harbor/cli/main.py") == "harbor/cli"
    assert infer_module_from_path("app/schemas/__init__.py") == "app/schemas"


def test_changed_modules_detect_and_generate_each(monkeypatch):
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
        modified=[SimpleNamespace(file_path=r"harbor\cli\main.py")],
        contract_changed=[SimpleNamespace(file_path="harbor/core/index.py")],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    generated = []
    wrote = []

    def _gen(self, module):
        generated.append(module)
        return f"# Module: {module}"

    def _write(self, module, md, force=False):
        wrote.append(module)
        return Path(module) / "README.md"

    monkeypatch.setattr(cli_main.L2Generator, "generate", _gen)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write)

    out = run_cmd(["docs", "--changed"])
    assert "Changed modules detected:" in out
    assert "- harbor/cli" in out
    assert "- harbor/core" in out
    assert "Preview only. Use --write to update files." in out
    assert generated == ["harbor/cli", "harbor/core"]
    assert wrote == []


def test_no_changed_modules_prints_friendly_message(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    out = run_cmd(["docs", "--changed"])
    assert "No changed modules detected" in out


def test_collect_all_indexed_modules_from_index_records(tmp_path: Path):
    idx_path = tmp_path / "l3_index.json"
    payload = {
        "files": {
            "harbor/core/sync.py": {"items": [{"id": "a"}]},
            "harbor/cli/main.py": {"items": [{"id": "b"}]},
            "harbor/empty/skip.py": {"items": []},
        }
    }
    idx_path.write_text(json.dumps(payload), encoding="utf-8")
    modules = collect_all_indexed_modules(index_path=idx_path)
    assert modules == ["harbor/cli", "harbor/core"]


def test_docs_all_preview_does_not_write(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/cli", "harbor/core"])
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}")
    write_calls = {"count": 0}

    def _write(self, module, md, force=False):
        write_calls["count"] += 1
        return Path(module) / "README.md"

    monkeypatch.setattr(cli_main.L2Generator, "write", _write)
    out = run_cmd(["docs", "--all"])
    assert "Generating L2 README for all indexed modules:" in out
    assert "Preview only. Use --write to update files." in out
    assert write_calls["count"] == 0


def test_docs_all_write_updates_each_module(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/cli", "harbor/core"])
    generated = []
    wrote = []

    def _gen(self, module):
        generated.append(module)
        return f"# Module: {module}"

    def _write(self, module, md, force=False):
        wrote.append(module)
        return Path(module) / "README.md"

    monkeypatch.setattr(cli_main.L2Generator, "generate", _gen)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write)
    out = run_cmd(["docs", "--all", "--write"])
    assert "Updated:" in out
    assert "- harbor/cli/README.md" in out
    assert "- harbor/core/README.md" in out
    assert generated == ["harbor/cli", "harbor/core"]
    assert wrote == ["harbor/cli", "harbor/core"]
