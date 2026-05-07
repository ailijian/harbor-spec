import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.stale import ModuleStaleSummary, ViewStaleResult


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


def _sample_summary(module: str, *, stale: bool = False) -> ModuleStaleSummary:
    status = "stale" if stale else "up_to_date"
    reason = "README content mismatch" if stale else "up to date"
    suggest_docs = f"harbor docs --module {module} --write" if stale else None
    suggest_capsule = f"harbor module seal {module} --write" if stale else None
    return ModuleStaleSummary(
        module=module,
        l2_readme=ViewStaleResult("L2 README", status, reason, suggest_docs),
        l2_readme_export=ViewStaleResult(
            "L2 README Export",
            status,
            ("module README export out of sync" if stale else "up to date"),
            suggest_docs,
        ),
        module_capsule=ViewStaleResult("Module Capsule", status, reason, suggest_capsule),
    )


def test_stale_default_is_changed_scope(monkeypatch):
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
        modified=[],
        contract_changed=[],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    checked = []
    monkeypatch.setattr(
        cli_main,
        "check_module_derived_views_stale",
        lambda module: checked.append(module) or _sample_summary(module),
    )
    out = run_cmd(["stale"])
    assert "Scope: changed modules" in out
    assert checked == ["harbor/core"]


def test_stale_changed_and_all_args_are_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: [])
    out_changed = run_cmd(["stale", "--changed"])
    out_all = run_cmd(["stale", "--all"])
    assert "No changed modules detected" in out_changed
    assert "No indexed modules found" in out_all


def test_stale_module_mode_runs(monkeypatch):
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=True))
    out = run_cmd(["stale", "--module", "harbor/core"])
    assert "Scope: module: harbor/core" in out
    assert "- L2 README: stale" in out
    assert "- Module Capsule: stale" in out
    assert "harbor docs --module harbor/core --write" in out
    assert "harbor module seal harbor/core --write" in out


def test_stale_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        run_cmd(["stale", "--module", "harbor/core", "--changed"])
    with pytest.raises(SystemExit):
        run_cmd(["stale", "--module", "harbor/core", "--all"])
    with pytest.raises(SystemExit):
        run_cmd(["stale", "--changed", "--all"])


def test_stale_changed_checks_both_views(monkeypatch):
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
        modified=[],
        contract_changed=[],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=True))
    out = run_cmd(["stale", "--changed"])
    assert "- L2 README: stale" in out
    assert "- Module Capsule: stale" in out


def test_stale_changed_windows_path_and_stable_order(monkeypatch):
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path=r"harbor\core\sync.py")],
        modified=[SimpleNamespace(file_path="harbor/cli/main.py")],
        contract_changed=[],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_summary(module))
    out = run_cmd(["stale", "--changed"])
    assert out.index("harbor/cli") < out.index("harbor/core")


def test_stale_all_scope_runs(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/cli", "harbor/core"])
    checked = []
    monkeypatch.setattr(
        cli_main,
        "check_module_derived_views_stale",
        lambda module: checked.append(module) or _sample_summary(module),
    )
    out = run_cmd(["stale", "--all"])
    assert "Scope: all indexed modules" in out
    assert checked == ["harbor/cli", "harbor/core"]


def test_stale_advisory_does_not_trigger_write_or_workflow_side_effects(monkeypatch):
    calls = {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0}
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=True))
    monkeypatch.setattr(cli_main.L2Generator, "write", lambda self, module, md, force=False: calls.__setitem__("docs_write", calls["docs_write"] + 1))
    monkeypatch.setattr(cli_main, "write_module_capsule", lambda context: calls.__setitem__("capsule_write", calls["capsule_write"] + 1))
    monkeypatch.setattr(cli_main.IndexBuilder, "iter_build", lambda self, incremental=True: calls.__setitem__("lock", calls["lock"] + 1) or iter([]))
    monkeypatch.setattr(cli_main.DiaryManager, "log", lambda self, **kwargs: calls.__setitem__("log", calls["log"] + 1))
    monkeypatch.setattr(cli_main, "write_module_skill", lambda module: calls.__setitem__("promote", calls["promote"] + 1))
    _ = run_cmd(["stale", "--module", "harbor/core"])
    assert calls == {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0}


def test_stale_reports_all_up_to_date_message(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/core"])
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=False))
    out = run_cmd(["stale", "--all"])
    assert "All derived context views are up to date." in out
