import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
import shutil
import subprocess
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
        assert "Detected stack:" in out
        assert "Default scan roots:" in out
        assert "Auto-excluded:" in out
        assert "harbor config list" in out
        assert "node_modules/**" not in out
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
        assert "检测到：技术栈" in out
        assert "默认扫描范围：" in out
        assert "已自动排除：" in out
        assert ".venv/**" not in out
        assert "venv/**" not in out
        cfg_path = tmp_path / ".harbor" / "config" / "harbor.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        assert not (tmp_path / ".harbor" / "config.yaml").exists()
        excludes = cfg.get("exclude_paths", [])
        assert ".venv/**" in excludes or "venv/**" in excludes
        assert cfg.get("language") == "zh"
    finally:
        os.chdir(old)


def test_real_harbor_init_writes_config_without_dangerous_py_excludes(tmp_path: Path):
    harbor_cmd = shutil.which("harbor")
    if not harbor_cmd:
        return
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.py\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    proc = subprocess.run(
        [
            harbor_cmd,
            "init",
            "--language",
            "zh",
            "--project",
            "new",
            "--governance",
            "--no-governance-docs",
            "--no-llm",
            "--update-gitignore",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        encoding="utf-8",
        text=True,
    )
    cfg = yaml.safe_load((tmp_path / ".harbor" / "config" / "harbor.yaml").read_text(encoding="utf-8")) or {}
    excludes = cfg.get("exclude_paths", [])
    assert "*.py" not in excludes
    assert "**/*.py" not in excludes
    assert "警告：skip exclude pattern '*.py'" in proc.stdout


def test_harbor_wrapper_output_matches_python_module(tmp_path: Path):
    harbor_cmd = shutil.which("harbor")
    if not harbor_cmd:
        return
    args = [
        "init",
        "--language",
        "zh",
        "--project",
        "new",
        "--governance",
        "--no-governance-docs",
        "--no-llm",
        "--update-gitignore",
        "--dry-run",
    ]
    wrap = subprocess.run(
        [harbor_cmd] + args,
        cwd=tmp_path,
        check=True,
        capture_output=True,
        encoding="utf-8",
        text=True,
    )
    mod = subprocess.run(
        [sys.executable, "-m", "harbor.cli.main"] + args,
        cwd=tmp_path,
        check=True,
        capture_output=True,
        encoding="utf-8",
        text=True,
    )
    for marker in ["检测到：技术栈", "默认扫描范围", "已自动排除", "完整配置可稍后运行：harbor config list"]:
        assert marker in wrap.stdout
        assert marker in mod.stdout


def test_real_harbor_init_is_encoding_safe_under_cp1252(tmp_path: Path):
    harbor_cmd = shutil.which("harbor")
    if not harbor_cmd:
        return
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)

    proc = subprocess.run(
        [
            harbor_cmd,
            "init",
            "--language",
            "zh",
            "--project",
            "new",
            "--governance",
            "--no-governance-docs",
            "--no-llm",
            "--update-gitignore",
        ],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
        env=env,
    )

    assert proc.returncode == 0
    assert "UnicodeEncodeError" not in proc.stdout
    assert "UnicodeEncodeError" not in proc.stderr


def test_real_harbor_init_dry_run_is_encoding_safe_under_cp1252(tmp_path: Path):
    harbor_cmd = shutil.which("harbor")
    if not harbor_cmd:
        return
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"

    proc = subprocess.run(
        [
            harbor_cmd,
            "init",
            "--language",
            "zh",
            "--project",
            "new",
            "--governance",
            "--no-governance-docs",
            "--no-llm",
            "--update-gitignore",
            "--dry-run",
        ],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
        env=env,
    )

    assert proc.returncode == 0
    assert "UnicodeEncodeError" not in proc.stdout
    assert "UnicodeEncodeError" not in proc.stderr
