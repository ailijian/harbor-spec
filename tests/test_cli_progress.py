from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import re
import sys
from types import SimpleNamespace

import pytest
from rich.console import Console

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.console_output import build_cli_progress, should_render_progress
from harbor.core.doctor import DoctorCheckResult, DoctorReport, PASS
from harbor.core.generated_verify import (
    GeneratedArtifactVerification,
    GeneratedVerificationReport,
    ModuleGeneratedVerification,
    ProjectGeneratedVerification,
)
from harbor.core.stale import ModuleStaleSummary, ViewStaleResult


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")
    for key in (
        "CI",
        "GITHUB_ACTIONS",
        "TF_BUILD",
        "BUILD_BUILDID",
        "TEAMCITY_VERSION",
    ):
        monkeypatch.delenv(key, raising=False)


class _TTYStringIO(StringIO):
    def isatty(self):
        return True


def _run_cmd(argv):
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


def _sample_report(scope: str) -> GeneratedVerificationReport:
    return GeneratedVerificationReport(
        scope=scope,
        project=ProjectGeneratedVerification(
            artifacts=[
                GeneratedArtifactVerification(
                    artifact="project_structure",
                    status="up_to_date",
                    path=".harbor/views/project-structure.md",
                )
            ]
        ),
        modules=[
            ModuleGeneratedVerification(
                module="harbor/core",
                artifacts=[
                    GeneratedArtifactVerification(
                        artifact="canonical_l2_readme",
                        module="harbor/core",
                        status="up_to_date",
                        path=".harbor/views/l2/harbor/core/README.md",
                    )
                ],
            )
        ],
        status="pass",
        summary={
            "modules_checked": 1,
            "artifacts_checked": 2,
            "up_to_date": 2,
            "failures": 0,
            "missing": 0,
            "disabled": 0,
            "blocked": 0,
            "unknown": 0,
            "repair_commands": 0,
        },
        repair_commands=[],
        writes_files=False,
    )


def _sample_stale_summary(module: str) -> ModuleStaleSummary:
    return ModuleStaleSummary(
        module=module,
        l2_readme=ViewStaleResult("L2 README", "up_to_date", "up to date", None),
        l2_readme_export=ViewStaleResult("L2 README Export", "up_to_date", "up to date", None),
        module_capsule=ViewStaleResult("Module Capsule", "up_to_date", "up to date", None),
    )


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", text)


def test_should_render_progress_only_for_interactive_text():
    tty_stream = _TTYStringIO()
    non_tty_stream = StringIO()

    assert should_render_progress(output_format="text", ci=False, stream=tty_stream) is True
    assert should_render_progress(
        output_format="text",
        ci=False,
        stream=tty_stream,
        env={"GITHUB_ACTIONS": "true"},
    ) is False
    assert should_render_progress(output_format="json", ci=False, stream=tty_stream) is False
    assert should_render_progress(output_format="text", ci=True, stream=tty_stream) is False
    assert should_render_progress(output_format="text", ci=False, stream=non_tty_stream) is False


def test_progress_reporter_emits_phase_lines_and_does_not_swallow_errors():
    stream = _TTYStringIO()
    reporter = build_cli_progress(
        output_format="text",
        console=Console(file=stream, force_terminal=True, width=120),
        interactive=True,
    )

    reporter.phase(current=1, total=2, label="Collecting status")
    with pytest.raises(RuntimeError, match="boom"):
        with reporter.status("Running validation"):
            raise RuntimeError("boom")

    rendered = _strip_ansi(stream.getvalue())
    assert "Phase 1/2: Collecting status" in rendered
    assert "Running validation" in rendered


def test_verify_generated_text_mode_shows_progress_on_stderr_when_interactive(monkeypatch):
    monkeypatch.setattr(cli_main, "build_generated_verification_report", lambda scope, modules: _sample_report(scope))

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["verify-generated", "--module", "harbor/core"])

    assert code == 0
    assert "Scope: module: harbor/core" in out
    assert "generated context" in _strip_ansi(err).lower()


def test_verify_generated_json_mode_keeps_stdout_clean_even_when_progress_forced(monkeypatch):
    monkeypatch.setattr(cli_main, "build_generated_verification_report", lambda scope, modules: _sample_report(scope))

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["verify-generated", "--module", "harbor/core", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert payload["command"] == "verify-generated"
    assert payload["scope"] == "module:harbor/core"
    assert "generated context" not in _strip_ansi(err).lower()
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def test_checkpoint_text_mode_does_not_leak_progress_i18n_keys(monkeypatch):
    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["checkpoint"])

    rendered = _strip_ansi(err)
    assert code == 0
    assert "Harbor Checkpoint:" in out
    assert "cli.progress.label." not in rendered
    assert "Phase 1/4: Collecting Harbor status" in rendered
    assert "Phase 4/4: Loading preview findings" in rendered


def test_stale_text_mode_shows_progress_on_stderr_when_interactive(monkeypatch):
    monkeypatch.setattr(
        cli_main.SyncEngine,
        "check_status",
        lambda self: SimpleNamespace(
            drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
            modified=[],
            contract_changed=[],
            untracked=[],
            missing=[],
        ),
    )
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_stale_summary(module))

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["stale"])

    rendered = _strip_ansi(err)
    assert code == 0
    assert "All derived context views are up to date." in out
    assert "Phase 1/2:" in rendered
    assert "Phase 2/2:" in rendered
    assert "cli.progress.label." not in rendered


def test_stale_all_text_mode_shows_progress_on_stderr_when_interactive(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda prefer_fresh_source=True: ["harbor/core", "tests"])
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_stale_summary(module))

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["stale", "--all"])

    rendered = _strip_ansi(err)
    assert code == 0
    assert "Scope: all indexed modules" in out
    assert "Phase 1/2:" in rendered
    assert "Phase 2/2:" in rendered
    assert "cli.progress.label." not in rendered


def test_stale_ci_json_keeps_stdout_clean_even_when_progress_forced(monkeypatch):
    monkeypatch.setattr(
        cli_main.SyncEngine,
        "check_status",
        lambda self: SimpleNamespace(
            drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
            modified=[],
            contract_changed=[],
            untracked=[],
            missing=[],
        ),
    )
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _sample_stale_summary(module))

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["stale", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert payload["command"] == "stale"
    assert "Resolving stale scope" not in _strip_ansi(err)
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def test_doctor_text_mode_shows_multi_stage_progress_on_stderr_when_interactive(monkeypatch):
    def _sample_doctor_report(scope: str, modules, on_phase_start=None):
        for phase_name in ("config_index", "workspace_status", "ddt_fast", "derived_views", "skill_refs"):
            if on_phase_start is not None:
                on_phase_start(phase_name)
        return DoctorReport(
            scope=scope,
            checks=[DoctorCheckResult("Config / Index", PASS, ["ok"], [])],
        )

    monkeypatch.setattr(
        cli_main.SyncEngine,
        "check_status",
        lambda self: SimpleNamespace(
            counts={
                "drift": 1,
                "modified": 0,
                "contract_changed": 0,
                "contract_gap": 0,
                "skipped_no_contract": 0,
                "contract_parse_error": 0,
                "untracked": 0,
                "missing": 0,
            },
            drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
            modified=[],
            contract_changed=[],
            contract_gap=[],
            skipped_no_contract=[],
            contract_parse_error=[],
            untracked=[],
            missing=[],
        ),
    )
    monkeypatch.setattr(cli_main, "build_doctor_report", _sample_doctor_report)

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["doctor"])

    rendered = _strip_ansi(err)
    assert code == 0
    for current in range(1, 7):
        assert f"Phase {current}/6:" in rendered
    assert "Scope: changed modules" in out
    assert "cli.progress.label." not in rendered


def test_doctor_all_text_mode_shows_multi_stage_progress_on_stderr_when_interactive(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda prefer_fresh_source=True: ["harbor/core"])

    def _sample_doctor_report(scope: str, modules, on_phase_start=None):
        for phase_name in ("config_index", "workspace_status", "ddt_fast", "derived_views", "skill_refs"):
            if on_phase_start is not None:
                on_phase_start(phase_name)
        return DoctorReport(
            scope=scope,
            checks=[DoctorCheckResult("Config / Index", PASS, ["ok"], [])],
        )

    monkeypatch.setattr(cli_main, "build_doctor_report", _sample_doctor_report)

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["doctor", "--all"])

    rendered = _strip_ansi(err)
    assert code == 0
    assert "Scope: all indexed modules" in out
    assert "Phase 1/6:" in rendered
    assert "Phase 6/6:" in rendered
    assert "cli.progress.label." not in rendered


def test_doctor_ci_json_keeps_stdout_single_object_when_progress_forced(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "build_doctor_report",
        lambda scope, modules: DoctorReport(
            scope=scope,
            checks=[DoctorCheckResult("Config / Index", PASS, ["ok"], [])],
        ),
    )

    def _force_progress(**kwargs):
        return build_cli_progress(
            console=Console(file=sys.stderr, force_terminal=True, width=120),
            interactive=True,
            **kwargs,
        )

    monkeypatch.setattr(cli_main, "build_cli_progress", _force_progress)

    code, out, err = _run_cmd(["doctor", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert payload["command"] == "doctor"
    assert "doctor report" not in _strip_ansi(err).lower()
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
