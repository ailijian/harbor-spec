from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import re
import sys

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


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


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


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", text)


def test_should_render_progress_only_for_interactive_text():
    tty_stream = _TTYStringIO()
    non_tty_stream = StringIO()

    assert should_render_progress(output_format="text", ci=False, stream=tty_stream) is True
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
