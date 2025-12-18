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


def test_env_language_overrides_config(tmp_path: Path):
    cfg_dir = tmp_path / ".harbor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "config.yaml").write_text(
        "schema_version: '1.0.2'\nprofile: enforce_l3\ncode_roots:\n  - harbor/**\nexclude_paths:\n  - .git/**\nlanguage: en\n",
        encoding="utf-8",
    )
    old = Path.cwd()
    old_env = os.environ.get("HARBOR_LANGUAGE")
    try:
        os.environ["HARBOR_LANGUAGE"] = "zh"
        os.chdir(tmp_path)
        out = run_cmd(["config", "list"])
        assert "Harbor 配置" in out
        assert "language" in out
        assert "en" in out  # 配置仍显示 en，但输出语言为中文
    finally:
        if old_env is None:
            os.environ.pop("HARBOR_LANGUAGE", None)
        else:
            os.environ["HARBOR_LANGUAGE"] = old_env
        os.chdir(old)
