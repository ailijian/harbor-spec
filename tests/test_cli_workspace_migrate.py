import json
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def run_cmd_with_err(argv):
    out = StringIO()
    err = StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def _write_workspace_fixture(tmp_path: Path) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n  - harbor/**\n", encoding="utf-8")


def test_cli_workspace_migrate_text_exit_0_and_contains_required_lines(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _write_workspace_fixture(tmp_path)
    out = run_cmd(["workspace", "migrate", "--dry-run"])
    assert "Harbor Workspace Migrate (Dry-run)" in out
    assert "Safety notice: dry-run only, no files changed." in out
    assert "No files were changed." in out
    assert "This command only prints a migration plan." in out


def test_cli_workspace_migrate_json_single_object(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _write_workspace_fixture(tmp_path)
    out = run_cmd(["workspace", "migrate", "--dry-run", "--format", "json"])
    payload = json.loads(out)

    assert set(payload.keys()) == {
        "command",
        "mode",
        "writes_files",
        "summary",
        "plan_items",
        "advisory",
        "next_steps",
    }
    assert payload["command"] == "workspace_migrate"
    assert payload["mode"] == "dry_run"
    assert payload["writes_files"] is False
    assert re.search(r"(?i)[a-z]:[\\/]", out) is None
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def test_cli_workspace_migrate_without_dry_run_fails(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _write_workspace_fixture(tmp_path)
    code, out, err = run_cmd_with_err(["workspace", "migrate"])
    assert code != 0
    assert out == ""
    assert "only --dry-run is supported in this version" in err


def test_cli_workspace_migrate_invalid_format_argparse_error(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _write_workspace_fixture(tmp_path)
    code, _, err = run_cmd_with_err(["workspace", "migrate", "--dry-run", "--format", "yaml"])
    assert code == 2
    assert "invalid choice" in err


def test_cli_workspace_migrate_no_write_regression(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _write_workspace_fixture(tmp_path)
    calls = {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0, "cfg_write": 0}
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
    monkeypatch.setattr(
        cli_main,
        "write_workspace_config",
        lambda repo_root, data: calls.__setitem__("cfg_write", calls["cfg_write"] + 1),
    )

    _ = run_cmd(["workspace", "migrate", "--dry-run"])
    assert calls == {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0, "cfg_write": 0}
