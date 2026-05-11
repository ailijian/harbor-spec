import json
import re
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.doctor import DoctorCheckResult, DoctorReport, FAIL, PASS, SKIP, WARN
from harbor.core.stale import ModuleStaleSummary, ViewStaleResult


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


@pytest.fixture(autouse=True)
def _disable_change_window_writes(monkeypatch):
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", lambda *args, **kwargs: None)


def run_cmd(argv):
    out = StringIO()
    code = 0
    with redirect_stdout(out):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, out.getvalue()


def _stale_summary(module: str, *, l2="up_to_date", export="up_to_date", capsule="up_to_date"):
    return ModuleStaleSummary(
        module=module,
        l2_readme=ViewStaleResult("L2 README", l2, "l2 reason", f"harbor docs --module {module} --write"),
        l2_readme_export=ViewStaleResult("L2 README Export", export, "export reason", f"harbor docs --module {module} --write"),
        module_capsule=ViewStaleResult("Module Capsule", capsule, "capsule reason", f"harbor module seal {module} --write"),
    )


def test_stale_ci_pass_no_canonical_stale(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/core"])
    monkeypatch.setattr(
        cli_main,
        "check_module_derived_views_stale",
        lambda module: _stale_summary(module, l2="up_to_date", export="stale", capsule="up_to_date"),
    )
    code, out = run_cmd(["stale", "--all", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["command"] == "stale"
    assert payload["ci"] is True
    assert payload["status"] == "pass"
    assert payload["writes_files"] is False
    assert payload["exit_code"] == 0
    assert "ci_failures" in payload and "advisory" in payload
    assert "failures" not in payload


def test_stale_ci_fail_on_canonical_l2_stale(monkeypatch):
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _stale_summary(module, l2="stale"))
    code, _ = run_cmd(["stale", "--module", "harbor/core", "--ci"])
    assert code == 1


def test_stale_ci_fail_on_module_capsule_stale(monkeypatch):
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _stale_summary(module, capsule="stale"))
    code, _ = run_cmd(["stale", "--module", "harbor/core", "--ci"])
    assert code == 1


def test_stale_ci_export_stale_is_advisory_only(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "check_module_derived_views_stale",
        lambda module: _stale_summary(module, l2="up_to_date", export="stale", capsule="up_to_date"),
    )
    code, out = run_cmd(["stale", "--module", "harbor/core", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["status"] == "pass"
    assert payload["ci_failures"] == []
    assert any(item.get("view") == "l2_readme_export" for item in payload["advisory"])


def test_stale_ci_json_single_object_and_no_abs_path(monkeypatch):
    abs_module = "C:/tmp/harbor/core"
    monkeypatch.setattr(
        cli_main,
        "check_module_derived_views_stale",
        lambda module: _stale_summary(abs_module, l2="stale", capsule="up_to_date"),
    )
    code, out = run_cmd(["stale", "--module", "harbor/core", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    assert re.search(r"(?i)[a-z]:[\\/]", out) is None
    assert payload["ci"] is True
    assert payload["writes_files"] is False


def test_doctor_ci_warn_only_is_pass(monkeypatch):
    report = DoctorReport(
        scope="changed modules",
        checks=[
            DoctorCheckResult("Workspace Status", WARN, ["Changed records detected: 2"], ["harbor checkpoint"]),
            DoctorCheckResult("Derived Views", WARN, ["legacy advisory"], ["harbor stale"]),
            DoctorCheckResult("Skill References", SKIP, ["optional skill dir missing"], []),
            DoctorCheckResult("DDT Fast Check", WARN, ["Violations: 2"], []),
            DoctorCheckResult("Config / Index", PASS, ["ok"], []),
        ],
    )
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: report)
    code, out = run_cmd(["doctor", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 0
    assert payload["status"] == "pass"
    assert payload["ci_failures"] == []


def test_ci_mode_i18n_labels_follow_language(monkeypatch):
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _stale_summary(module))
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: DoctorReport(scope=scope, checks=[DoctorCheckResult("Config / Index", PASS, ["ok"], [])]),
    )

    monkeypatch.setenv("HARBOR_LANGUAGE", "zh")
    _, zh_checkpoint = run_cmd(["checkpoint", "--ci"])
    _, zh_stale = run_cmd(["stale", "--module", "harbor/core", "--ci"])
    _, zh_doctor = run_cmd(["doctor", "--module", "harbor/core", "--ci"])
    zh_text = "\n".join([zh_checkpoint, zh_stale, zh_doctor])
    assert "CI 模式已启用" in zh_text
    assert "CI 门禁：" in zh_text
    assert "建议下一步：" in zh_text
    assert "写入文件: false" in zh_text or "写入文件：false" in zh_text
    assert "CI mode enabled" not in zh_text
    assert "Suggested next steps" not in zh_text
    assert "Blocking failures" not in zh_text

    monkeypatch.setenv("HARBOR_LANGUAGE", "en")
    _, en_checkpoint = run_cmd(["checkpoint", "--ci"])
    _, en_stale = run_cmd(["stale", "--module", "harbor/core", "--ci"])
    _, en_doctor = run_cmd(["doctor", "--module", "harbor/core", "--ci"])
    en_text = "\n".join([en_checkpoint, en_stale, en_doctor])
    assert "CI mode enabled" in en_text
    assert "CI gate" in en_text
    assert "Suggested next steps" in en_text


def test_doctor_ci_fail_on_fail_check(monkeypatch):
    report = DoctorReport(
        scope="changed modules",
        checks=[
            DoctorCheckResult("Config / Index", FAIL, ["Index/database unavailable"], ["harbor lock"]),
            DoctorCheckResult("Workspace Status", WARN, ["changed"], []),
        ],
    )
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: report)
    code, _ = run_cmd(["doctor", "--ci"])
    assert code == 1


def test_doctor_ci_json_single_object_and_no_abs_path(monkeypatch):
    report = DoctorReport(
        scope="module:C:/tmp/harbor/core",
        checks=[
            DoctorCheckResult("Config / Index", FAIL, ["C:/tmp/harbor/core missing"], ["harbor stale"]),
        ],
    )
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: report)
    code, out = run_cmd(["doctor", "--module", "harbor/core", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    assert re.search(r"(?i)[a-z]:[\\/]", out) is None
    assert payload["ci"] is True
    assert payload["writes_files"] is False
    assert "failures" not in payload


def test_ci_next_steps_excludes_accept_log_lock(monkeypatch):
    report = DoctorReport(
        scope="changed modules",
        checks=[
            DoctorCheckResult(
                "Config / Index",
                FAIL,
                ["broken"],
                ["harbor accept", "harbor log", "harbor lock", "harbor stale"],
            )
        ],
    )
    monkeypatch.setattr(cli_main, "build_doctor_report", lambda scope, modules: report)
    code, out = run_cmd(["doctor", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert code == 1
    assert all(not step.startswith("harbor accept") for step in payload["next_steps"])
    assert all(not step.startswith("harbor log") for step in payload["next_steps"])
    assert all(not step.startswith("harbor lock") for step in payload["next_steps"])


def test_ci_mode_no_write_regression(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    targets = [
        tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md",
        tmp_path / ".harbor" / "diary" / "2026-05.jsonl",
        tmp_path / ".harbor" / "config" / "harbor.yaml",
        tmp_path / "docs" / "harbor" / "project-structure.md",
        tmp_path / "specs" / "diary" / "2025-12.jsonl",
    ]
    for path in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"seed::{path.name}", encoding="utf-8")
    before = {p.as_posix(): (p.read_text(encoding="utf-8"), p.stat().st_mtime_ns) for p in targets}

    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _stale_summary(module))
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: DoctorReport(scope=scope, checks=[DoctorCheckResult("Config / Index", PASS, ["ok"], [])]),
    )
    stale_code, _ = run_cmd(["stale", "--module", "harbor/core", "--ci"])
    doctor_code, _ = run_cmd(["doctor", "--module", "harbor/core", "--ci"])
    after = {p.as_posix(): (p.read_text(encoding="utf-8"), p.stat().st_mtime_ns) for p in targets}

    assert stale_code == 0
    assert doctor_code == 0
    assert before.keys() == after.keys()
    for key in before:
        assert before[key][0] == after[key][0]
