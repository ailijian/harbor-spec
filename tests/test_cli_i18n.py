import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stderr, redirect_stdout
import sys

from harbor.cli.main import main




def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def run_cmd_with_err(argv):
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


def test_config_list_zh(tmp_path: Path):
    cfg_dir = tmp_path / ".harbor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "config.yaml").write_text(
        "schema_version: '1.0.2'\nprofile: enforce_l3\ncode_roots:\n  - harbor/**\nexclude_paths:\n  - .git/**\nlanguage: zh\n",
        encoding="utf-8",
    )
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_cmd(["config", "list"])
        assert "Harbor 配置" in out
        assert "language" in out
        assert "zh" in out
    finally:
        os.chdir(old)


def test_canonical_config_language_wins_over_legacy(tmp_path: Path):
    harbor_dir = tmp_path / ".harbor"
    (harbor_dir / "config").mkdir(parents=True, exist_ok=True)
    (harbor_dir / "config" / "harbor.yaml").write_text(
        "schema_version: '1.3.0'\nprofile: enforce_l3\ncode_roots:\n  - harbor/**\nexclude_paths:\n  - .git/**\nlanguage: zh\n",
        encoding="utf-8",
    )
    (harbor_dir / "config.yaml").write_text(
        "schema_version: '1.0.2'\nprofile: enforce_l3\ncode_roots:\n  - harbor/**\nexclude_paths:\n  - .git/**\nlanguage: en\n",
        encoding="utf-8",
    )
    old = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_cmd(["config", "list"])
        assert "Harbor 配置" in out
        assert "zh" in out
    finally:
        os.chdir(old)


def test_checkpoint_format_error_uses_zh_i18n(tmp_path: Path):
    old = Path.cwd()
    old_env = os.environ.get("HARBOR_LANGUAGE")
    try:
        os.environ["HARBOR_LANGUAGE"] = "zh"
        os.chdir(tmp_path)
        code, _, err = run_cmd_with_err(["checkpoint", "--format", "json"])
        assert code == 2
        assert "--format 仅适用于 CI 模式。" in err
    finally:
        if old_env is None:
            os.environ.pop("HARBOR_LANGUAGE", None)
        else:
            os.environ["HARBOR_LANGUAGE"] = old_env
        os.chdir(old)
