import os
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from harbor.cli.main import main


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _starter_targets(root: Path):
    return [
        root / "AGENTS.md",
        root / ".harbor" / "rules" / "role-rules.md",
        root / ".harbor" / "rules" / "project-rules-guide.md",
        root / ".harbor" / "policy.yaml",
        root / ".harbor" / "safety.yaml",
    ]


def test_init_dry_run_with_full_flags_writes_nothing(tmp_path: Path):
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_cmd(
            [
                "init",
                "--dry-run",
                "--language",
                "zh",
                "--project",
                "new",
                "--governance",
                "--no-governance-docs",
                "--no-llm",
                "--no-update-gitignore",
            ]
        )
        assert "dry-run" in out
        for p in _starter_targets(tmp_path):
            assert not p.exists()
        assert not (tmp_path / ".harbor" / "rules" / "project-rules.md").exists()
    finally:
        os.chdir(old)


def test_init_governance_creates_starter_files_without_project_rules(tmp_path: Path):
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        run_cmd(
            [
                "init",
                "--language",
                "en",
                "--project",
                "existing",
                "--governance",
                "--no-governance-docs",
                "--no-llm",
                "--no-update-gitignore",
            ]
        )
        for p in _starter_targets(tmp_path):
            assert p.exists()
        assert not (tmp_path / ".harbor" / "rules" / "project-rules.md").exists()
        assert not (tmp_path / "docs" / "harbor").exists()
    finally:
        os.chdir(old)


def test_init_existing_files_are_skipped_unless_force(tmp_path: Path):
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        custom_agents = tmp_path / "AGENTS.md"
        custom_agents.write_text("custom", encoding="utf-8")
        run_cmd(
            [
                "init",
                "--language",
                "en",
                "--project",
                "existing",
                "--governance",
                "--no-governance-docs",
                "--no-llm",
                "--no-update-gitignore",
            ]
        )
        assert custom_agents.read_text(encoding="utf-8") == "custom"
        run_cmd(
            [
                "init",
                "--force",
                "--language",
                "en",
                "--project",
                "existing",
                "--governance",
                "--no-governance-docs",
                "--no-llm",
                "--no-update-gitignore",
            ]
        )
        assert "harbor-spec:managed" in custom_agents.read_text(encoding="utf-8")
    finally:
        os.chdir(old)
