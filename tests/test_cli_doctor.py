import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.doctor import DoctorCheckResult, DoctorReport, PASS


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


def _empty_status_report():
    return SimpleNamespace(
        counts={"drift": 0, "modified": 0, "contract_changed": 0, "untracked": 0, "missing": 0},
        drift=[],
        modified=[],
        contract_changed=[],
        untracked=[],
        missing=[],
    )


def _pass_report(scope: str) -> DoctorReport:
    return DoctorReport(
        scope=scope,
        checks=[
            DoctorCheckResult("Config / Index", PASS, ["ok"], []),
            DoctorCheckResult("Workspace Status", PASS, ["ok"], []),
            DoctorCheckResult("DDT Fast Check", PASS, ["ok"], []),
            DoctorCheckResult("Derived Views", PASS, ["ok"], []),
            DoctorCheckResult("Skill References", PASS, ["ok"], []),
        ],
    )


def test_doctor_default_is_changed_scope(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        cli_main.SyncEngine,
        "check_status",
        lambda self: SimpleNamespace(
            counts={"drift": 1, "modified": 0, "contract_changed": 0, "untracked": 0, "missing": 0},
            drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
            modified=[],
            contract_changed=[],
            untracked=[],
            missing=[],
        ),
    )
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: captured.update({"scope": scope, "modules": modules}) or _pass_report(scope),
    )
    monkeypatch.setattr(cli_main, "format_doctor_report", lambda report: f"Scope: {report.scope}")
    out = run_cmd(["doctor"])
    assert "Scope: changed modules" in out
    assert captured["modules"] == ["harbor/core"]


def test_doctor_changed_and_all_args_are_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: [])
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: _pass_report(scope))
    monkeypatch.setattr(cli_main, "format_doctor_report", lambda report: f"Scope: {report.scope}")
    out_changed = run_cmd(["doctor", "--changed"])
    out_all = run_cmd(["doctor", "--all"])
    assert "Scope: changed modules" in out_changed
    assert "Scope: all indexed modules" in out_all


def test_doctor_module_mode_runs(monkeypatch):
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: _pass_report(scope))
    monkeypatch.setattr(cli_main, "format_doctor_report", lambda report: f"Scope: {report.scope}")
    out = run_cmd(["doctor", "--module", "harbor/core"])
    assert "Scope: module: harbor/core" in out


def test_doctor_modes_are_mutually_exclusive():
    code, _, err = run_cmd_with_err(["doctor", "--module", "harbor/core", "--changed"])
    assert code == 2
    assert "--module, --changed, and --all are mutually exclusive." in err
    code, _, err = run_cmd_with_err(["doctor", "--module", "harbor/core", "--all"])
    assert code == 2
    assert "--module, --changed, and --all are mutually exclusive." in err
    code, _, err = run_cmd_with_err(["doctor", "--changed", "--all"])
    assert code == 2
    assert "--module, --changed, and --all are mutually exclusive." in err


def test_doctor_is_advisory_and_does_not_trigger_write_or_llm_paths(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: _pass_report(scope))
    monkeypatch.setattr(cli_main, "format_doctor_report", lambda report: "Harbor Doctor")

    calls = {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0, "semantic": 0}
    monkeypatch.setattr(cli_main.L2Generator, "write", lambda self, module, md, force=False: calls.__setitem__("docs_write", calls["docs_write"] + 1))
    monkeypatch.setattr(cli_main, "write_module_capsule", lambda context: calls.__setitem__("capsule_write", calls["capsule_write"] + 1))
    monkeypatch.setattr(cli_main.IndexBuilder, "iter_build", lambda self, incremental=True: calls.__setitem__("lock", calls["lock"] + 1) or iter([]))
    monkeypatch.setattr(cli_main.DiaryManager, "log", lambda self, **kwargs: calls.__setitem__("log", calls["log"] + 1))
    monkeypatch.setattr(cli_main, "write_module_skill", lambda module: calls.__setitem__("promote", calls["promote"] + 1))
    monkeypatch.setattr(cli_main.SemanticGuard, "audit", lambda self, contract, src, provider: calls.__setitem__("semantic", calls["semantic"] + 1))

    _ = run_cmd(["doctor"])
    assert calls == {"docs_write": 0, "capsule_write": 0, "lock": 0, "log": 0, "promote": 0, "semantic": 0}
