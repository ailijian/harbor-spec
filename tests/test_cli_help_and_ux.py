import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def run_cmd(argv):
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


def run_help(argv):
    code, out, err = run_cmd(argv + ["--help"])
    assert code == 0
    return out, err


def test_workflow_help_exposes_start_checkpoint_finish_accept():
    out_start, _ = run_help(["start"])
    out_checkpoint, _ = run_help(["checkpoint"])
    out_finish, _ = run_help(["finish"])
    out_accept, _ = run_help(["accept"])

    assert "Workflow facade" in out_start
    assert "Workflow facade" in out_checkpoint
    assert "--sync-context" in out_finish
    assert "semantic alias of harbor lock" in out_accept


def test_doctor_help_lists_changed_all_and_module_flags():
    out_doctor, _ = run_help(["doctor"])
    assert "--changed" in out_doctor
    assert "--all" in out_doctor
    assert "--module" in out_doctor
    assert "--format" in out_doctor
    assert "--ci" in out_doctor


def test_stale_help_lists_changed_all_module_and_format_flags():
    out_stale, _ = run_help(["stale"])
    assert "--changed" in out_stale
    assert "--all" in out_stale
    assert "--module" in out_stale
    assert "--format" in out_stale
    assert "--ci" in out_stale


def test_docs_help_lists_changed_all_and_write_flags():
    out_docs, _ = run_help(["docs"])
    assert "--changed" in out_docs
    assert "--all" in out_docs
    assert "--write" in out_docs


def test_module_help_lists_inspect_seal_stale_and_promote_skill():
    out_module, _ = run_help(["module"])
    assert "inspect" in out_module
    assert "seal" in out_module
    assert "stale" in out_module
    assert "promote-skill" in out_module


def test_project_help_lists_structure_and_structure_help_lists_write():
    out_project, _ = run_help(["project"])
    out_structure, _ = run_help(["project", "structure"])
    assert "structure" in out_project
    assert "--write" in out_structure


def test_project_structure_preview_message_uses_resolved_canonical_path(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code, out, err = run_cmd(["project", "structure"])
    assert code == 0
    assert err == ""
    assert "Preview only. Use --write to update .harbor/views/project-structure.md." in out


def test_docs_modes_error_message_is_friendly_and_clear():
    code, _, err = run_cmd(["docs", "--module", "harbor/core", "--changed"])
    assert code == 2
    assert "--module, --changed, and --all are mutually exclusive." in err

    code, _, err = run_cmd(["docs", "--changed", "--all"])
    assert code == 2
    assert "--module, --changed, and --all are mutually exclusive." in err


def test_module_seal_modes_error_message_is_friendly_and_clear():
    code, _, err = run_cmd(["module", "seal", "--changed", "--all"])
    assert code == 2
    assert "module seal modes are mutually exclusive" in err


def test_module_stale_modes_error_message_is_friendly_and_clear():
    code, _, err = run_cmd(["module", "stale", "--changed", "--all"])
    assert code == 2
    assert "module stale modes are mutually exclusive" in err


def test_readme_and_readme_en_include_key_new_command_phrases():
    root = Path(__file__).resolve().parents[1]
    readme_zh = (root / "README.md").read_text(encoding="utf-8")
    readme_en = (root / "README.en.md").read_text(encoding="utf-8")

    required_phrases = [
        "finish --sync-context",
        "harbor doctor",
        "module promote-skill",
        "docs --changed",
        "module stale",
        "project structure --write",
    ]

    for phrase in required_phrases:
        assert phrase in readme_zh
        assert phrase in readme_en
