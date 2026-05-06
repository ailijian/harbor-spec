import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_help(argv):
    out = StringIO()
    err = StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        sys.argv = ["harbor"] + argv + ["--help"]
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def test_pyproject_version_and_description_are_release_ready():
    pyproject_text = (_repo_root() / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    desc_match = re.search(r'^description\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)

    assert version_match is not None
    assert re.match(r"^\d+\.\d+\.\d+$", version_match.group(1))

    assert desc_match is not None
    description = desc_match.group(1)
    assert "v1.0.2 reference implementation" not in description


def test_readme_contains_release_key_commands():
    readme_zh = (_repo_root() / "README.md").read_text(encoding="utf-8")
    required = [
        "harbor finish --sync-context",
        "harbor stale",
        "harbor doctor",
        "harbor module promote-skill",
    ]
    for phrase in required:
        assert phrase in readme_zh


def test_readme_en_contains_release_key_commands():
    readme_en = (_repo_root() / "README.en.md").read_text(encoding="utf-8")
    required = [
        "harbor finish --sync-context",
        "harbor stale",
        "harbor doctor",
        "harbor module promote-skill",
    ]
    for phrase in required:
        assert phrase in readme_en


def test_release_notes_include_unreleased_v130_track():
    release_text = (_repo_root() / "RELEASE.md").read_text(encoding="utf-8")
    assert "Unreleased / v1.3.0 - Workflow & Module Capsule Update" in release_text


def test_help_recognizes_core_release_commands():
    help_targets = [
        [],
        ["finish"],
        ["docs"],
        ["module"],
        ["stale"],
        ["doctor"],
    ]

    for argv in help_targets:
        code, out, err = _run_help(argv)
        assert code == 0
        assert "usage: harbor" in out
        assert err == ""
