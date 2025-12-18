import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
import sys

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
        out = run_cmd(["init", "--force"])
        assert ("Detected Node.js" in out) or ("检测到 Node.js" in out)
        assert ("Auto-configured excludes:" in out) or ("自动配置排除" in out)
        assert "node_modules" in out
        assert ("Auto-detected code roots:" in out) or ("自动探测的代码根" in out)
        cfg = (tmp_path / ".harbor" / "config.yaml").read_text(encoding="utf-8")
        assert "node_modules/**" in cfg
    finally:
        os.chdir(old)


def test_init_detects_django(tmp_path: Path):
    (tmp_path / "manage.py").write_text("", encoding="utf-8")
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_cmd(["init", "--force"])
        assert ("Detected Python(Django)" in out) or ("检测到 Python(Django)" in out)
        assert ("Auto-detected code roots:" in out) or ("自动探测的代码根" in out)
        cfg = (tmp_path / ".harbor" / "config.yaml").read_text(encoding="utf-8")
        assert ".venv/**" in cfg or "venv/**" in cfg
    finally:
        os.chdir(old)
