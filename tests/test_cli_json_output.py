import json
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.doctor import DoctorCheckResult, DoctorReport, PASS, SKIP, WARN
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


def _sample_stale_summary(module: str, *, stale: bool = True) -> ModuleStaleSummary:
    l2_status = "stale" if stale else "up_to_date"
    export_status = "stale" if stale else "up_to_date"
    capsule_status = "stale" if stale else "up_to_date"
    return ModuleStaleSummary(
        module=module,
        l2_readme=ViewStaleResult(
            view="L2 README",
            status=l2_status,
            reason=("README content mismatch" if stale else "up to date"),
            suggested_command=(f"harbor docs --module {module} --write" if stale else None),
        ),
        l2_readme_export=ViewStaleResult(
            view="L2 README Export",
            status=export_status,
            reason=("module README export out of sync" if stale else "up to date"),
            suggested_command=(f"harbor docs --module {module} --write" if stale else None),
        ),
        module_capsule=ViewStaleResult(
            view="Module Capsule",
            status=capsule_status,
            reason=("fingerprint mismatch" if stale else "up to date"),
            suggested_command=(f"harbor module seal {module} --write" if stale else None),
        ),
    )


def _sample_doctor_report(scope: str) -> DoctorReport:
    return DoctorReport(
        scope=scope,
        checks=[
            DoctorCheckResult("Config / Index", PASS, ["Index is readable."], []),
            DoctorCheckResult("Workspace Status", WARN, ["Changed records detected: 3"], ["harbor checkpoint", "harbor finish"]),
            DoctorCheckResult("Skill References", SKIP, [".agents/skills not found"], []),
        ],
    )


def test_stale_json_output_has_required_fields_and_no_extra_text(monkeypatch):
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_stale_summary(module, stale=True))
    out = run_cmd(["stale", "--module", "harbor/core", "--format", "json"])
    payload = json.loads(out)

    assert payload["command"] == "stale"
    assert payload["scope"] == "module:harbor/core"
    assert payload["status"] == "warn"
    assert set(payload.keys()) == {"command", "scope", "status", "summary", "modules", "advisory", "writes_files"}
    assert payload["advisory"] is True
    assert payload["writes_files"] is False
    view_names = [v["view"] for v in payload["modules"][0]["views"]]
    assert "l2_readme_export" in view_names
    assert "specs/diary" not in out
    assert ".harbor/diary" not in out
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def test_stale_json_scope_for_module_and_deterministic_content(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/core", "harbor/cli"])
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_stale_summary(module, stale=(module == "harbor/core")))

    out1 = run_cmd(["stale", "--all", "--format", "json"])
    out2 = run_cmd(["stale", "--all", "--format", "json"])
    payload = json.loads(out1)

    assert payload["scope"] == "all"
    assert payload["summary"]["modules_checked"] == 2
    assert out1 == out2


def test_doctor_json_output_has_required_fields_and_summary(monkeypatch):
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: _sample_doctor_report(scope))
    out = run_cmd(["doctor", "--format", "json"])
    payload = json.loads(out)

    assert payload["command"] == "doctor"
    assert payload["scope"] == "changed"
    assert payload["status"] == "warn"
    assert set(payload.keys()) == {"command", "scope", "status", "checks", "summary", "advisory", "writes_files"}
    assert payload["summary"] == {"pass": 1, "warn": 1, "fail": 0, "skip": 1}
    assert payload["advisory"] is True
    assert payload["writes_files"] is False
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def test_doctor_json_scope_for_module(monkeypatch):
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: _sample_doctor_report(scope))
    out = run_cmd(["doctor", "--module", "harbor/core", "--format", "json"])
    payload = json.loads(out)
    assert payload["scope"] == "module:harbor/core"


def test_default_text_output_for_stale_and_doctor_is_unchanged(monkeypatch):
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_stale_summary(module, stale=True))
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: _sample_doctor_report(scope))
    monkeypatch.setattr(cli_main, "format_doctor_report", lambda report: f"Scope: {report.scope}")

    stale_out = run_cmd(["stale", "--module", "harbor/core"])
    doctor_out = run_cmd(["doctor", "--module", "harbor/core"])

    assert "Scope: module: harbor/core" in stale_out
    assert "Scope: module: harbor/core" in doctor_out


def test_invalid_format_values_return_argparse_error():
    code_stale, _, err_stale = run_cmd_with_err(["stale", "--format", "yaml"])
    code_doctor, _, err_doctor = run_cmd_with_err(["doctor", "--format", "xml"])

    assert code_stale == 2
    assert code_doctor == 2
    assert "invalid choice" in err_stale
    assert "invalid choice" in err_doctor


def test_json_output_does_not_include_absolute_paths(monkeypatch):
    abs_module = "C:/tmp/harbor/core"
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_stale_summary(abs_module, stale=True))
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: DoctorReport(
            scope=scope,
            checks=[
                DoctorCheckResult(
                    "Derived Views",
                    WARN,
                    [f"{abs_module} stale: fingerprint mismatch"],
                    [f"harbor module seal {abs_module} --write"],
                )
            ],
        ),
    )

    stale_out = run_cmd(["stale", "--module", "harbor/core", "--format", "json"])
    doctor_out = run_cmd(["doctor", "--module", "harbor/core", "--format", "json"])

    assert re.search(r"(?i)[a-z]:[\\/]", stale_out) is None
    assert re.search(r"(?i)[a-z]:[\\/]", doctor_out) is None


def test_doctor_json_derived_view_detail_keeps_unknown_semantics(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: DoctorReport(
            scope=scope,
            checks=[
                DoctorCheckResult(
                    "Derived Views",
                    WARN,
                    ["tests/fixtures_sqlite L2 README unknown: no indexed records found for module"],
                    [],
                )
            ],
        ),
    )
    out = run_cmd(["doctor", "--module", "tests/fixtures_sqlite", "--format", "json"])
    payload = json.loads(out)
    details = payload["checks"][0]["details"]
    assert any("unknown: no indexed records found for module" in item for item in details)
    assert all("stale: no indexed records found for module" not in item for item in details)


def test_doctor_json_includes_legacy_diary_advisory(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: DoctorReport(
            scope=scope,
            checks=[
                DoctorCheckResult(
                    "Derived Views",
                    WARN,
                    [
                        "workspace layout/project memory advisory: legacy diary storage detected at specs/diary (not a derived view freshness signal)",
                        "canonical diary path: .harbor/diary",
                        "new diary entries are written to .harbor/diary",
                        "no automatic cleanup or migration is performed for specs/diary",
                    ],
                    [],
                )
            ],
        ),
    )
    out = run_cmd(["doctor", "--module", "harbor/core", "--format", "json"])
    payload = json.loads(out)
    details = payload["checks"][0]["details"]
    assert any("workspace layout/project memory advisory" in item for item in details)
    assert any("specs/diary" in item for item in details)
    assert any(".harbor/diary" in item for item in details)
    assert re.search(r"(?i)[a-z]:[\\/]", out) is None
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
