import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
import sys

import yaml

from harbor.cli.main import main


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def test_init_detects_node(tmp_path: Path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_cmd(
            [
                "init",
                "--force",
                "--language",
                "en",
                "--project",
                "existing",
                "--no-governance",
                "--no-governance-docs",
                "--no-llm",
                "--no-update-gitignore",
            ]
        )
        assert "Detected code roots:" in out
        assert "Detected excludes:" in out
        cfg_path = tmp_path / ".harbor" / "config" / "harbor.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        assert not (tmp_path / ".harbor" / "config.yaml").exists()
        assert "node_modules/**" in cfg.get("exclude_paths", [])
        assert cfg.get("language") == "en"
    finally:
        os.chdir(old)


def test_init_detects_django(tmp_path: Path):
    (tmp_path / "manage.py").write_text("", encoding="utf-8")
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_cmd(
            [
                "init",
                "--force",
                "--language",
                "zh",
                "--project",
                "existing",
                "--no-governance",
                "--no-governance-docs",
                "--no-llm",
                "--no-update-gitignore",
            ]
        )
        assert "Detected code roots:" in out
        cfg_path = tmp_path / ".harbor" / "config" / "harbor.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        assert not (tmp_path / ".harbor" / "config.yaml").exists()
        excludes = cfg.get("exclude_paths", [])
        assert ".venv/**" in excludes or "venv/**" in excludes
        assert cfg.get("language") == "zh"
    finally:
        os.chdir(old)
