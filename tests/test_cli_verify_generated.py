import json
import sys
from contextlib import redirect_stdout
from io import StringIO

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.generated_verify import (
    GeneratedArtifactVerification,
    GeneratedVerificationReport,
    ModuleGeneratedVerification,
    ProjectGeneratedVerification,
)


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _run_cmd_with_exit_code(argv):
    buf = StringIO()
    code = 0
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, buf.getvalue()


def _sample_report(scope: str, *, failed: bool = False) -> GeneratedVerificationReport:
    status = "fail" if failed else "pass"
    module_status = "fail" if failed else "up_to_date"
    reason = "l2_body_mismatch" if failed else None
    return GeneratedVerificationReport(
        scope=scope,
        project=ProjectGeneratedVerification(
            artifacts=[
                GeneratedArtifactVerification(
                    artifact="project_structure",
                    status="up_to_date",
                    path=".harbor/views/project-structure.md",
                ),
                GeneratedArtifactVerification(
                    artifact="l2_meta",
                    status="up_to_date",
                    path=".harbor/views/l2/_meta.json",
                ),
            ]
        ),
        modules=[
            ModuleGeneratedVerification(
                module="harbor/core",
                artifacts=[
                    GeneratedArtifactVerification(
                        artifact="canonical_l2_readme",
                        module="harbor/core",
                        status=module_status,
                        reason=reason,
                        path=".harbor/views/l2/harbor/core/README.md",
                        suggested_command=("harbor docs --module harbor/core --write" if failed else None),
                    )
                ],
            )
        ],
        status=status,
        summary={
            "modules_checked": 1,
            "artifacts_checked": 3,
            "up_to_date": 2 if failed else 3,
            "failures": 1 if failed else 0,
            "missing": 0,
            "disabled": 0,
            "blocked": 0,
            "unknown": 0,
            "repair_commands": 1 if failed else 0,
        },
        repair_commands=(["harbor docs --module harbor/core --write"] if failed else []),
        writes_files=False,
    )


def test_verify_generated_default_is_changed_scope(monkeypatch):
    rep = type(
        "StatusReport",
        (),
        {"drift": [type("Entry", (), {"file_path": "harbor/core/sample.py"})()], "modified": [], "contract_changed": [], "untracked": [], "missing": []},
    )()
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    monkeypatch.setattr(cli_main, "build_generated_verification_report", lambda scope, modules: _sample_report(scope))

    out = run_cmd(["verify-generated"])

    assert "Scope: changed modules" in out
    assert "Status: PASS" in out


def test_verify_generated_module_mode_runs(monkeypatch):
    monkeypatch.setattr(cli_main, "build_generated_verification_report", lambda scope, modules: _sample_report(scope, failed=True))

    out = run_cmd(["verify-generated", "--module", "harbor/core"])

    assert "Scope: module: harbor/core" in out
    assert "- canonical L2 README: fail" in out
    assert "harbor docs --module harbor/core --write" in out


def test_verify_generated_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        run_cmd(["verify-generated", "--module", "harbor/core", "--changed"])
    with pytest.raises(SystemExit):
        run_cmd(["verify-generated", "--module", "harbor/core", "--all"])
    with pytest.raises(SystemExit):
        run_cmd(["verify-generated", "--changed", "--all"])


def test_verify_generated_json_output_has_required_fields(monkeypatch):
    monkeypatch.setattr(cli_main, "build_generated_verification_report", lambda scope, modules: _sample_report(scope, failed=True))

    out = run_cmd(["verify-generated", "--module", "harbor/core", "--format", "json"])
    payload = json.loads(out)

    assert payload["command"] == "verify-generated"
    assert payload["scope"] == "module:harbor/core"
    assert payload["status"] == "fail"
    assert payload["writes_files"] is False
    assert "project" in payload
    assert "modules" in payload
    assert "repair_commands" in payload
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def test_verify_generated_ci_json_uses_ci_failures_and_exit_code(monkeypatch):
    monkeypatch.setattr(cli_main, "build_generated_verification_report", lambda scope, modules: _sample_report(scope, failed=True))

    code, out = _run_cmd_with_exit_code(["verify-generated", "--module", "harbor/core", "--ci", "--format", "json"])
    payload = json.loads(out)

    assert code == 1
    assert payload["command"] == "verify-generated"
    assert payload["ci"] is True
    assert payload["status"] == "fail"
    assert "ci_failures" in payload
    assert payload["summary"]["ci_failures"] == 1
