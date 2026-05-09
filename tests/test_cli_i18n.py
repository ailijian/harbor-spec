import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stderr, redirect_stdout
import sys

from rich.console import Console
from rich.prompt import Prompt

from harbor.cli.main import main
from harbor.core.init_wizard import InitWizard, InitWizardOptions




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


def test_init_provider_prompt_i18n_text(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    def _yes_no(self, prompt_text, default):
        return "scan roots" in prompt_text

    zh_stream = StringIO()
    zh_asks = iter(["1", ""])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(zh_asks)))
    monkeypatch.setattr(InitWizard, "_ask_yes_no", _yes_no)
    InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="zh",
            project="new",
            governance=False,
            governance_docs=False,
            llm=True,
            update_gitignore=False,
        ),
        console=Console(file=zh_stream, force_terminal=False),
    ).run()
    zh_out = zh_stream.getvalue()
    assert "请选择 LLM 服务商（使用 ↑/↓ 选择，Enter 确认；也可输入编号或名称）" in zh_out

    en_stream = StringIO()
    en_asks = iter(["1", ""])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(en_asks)))
    InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="en",
            project="new",
            governance=False,
            governance_docs=False,
            llm=True,
            update_gitignore=False,
        ),
        console=Console(file=en_stream, force_terminal=False),
    ).run()
    en_out = en_stream.getvalue()
    assert "Choose LLM provider (use ↑/↓ and Enter, or type number/name):" in en_out
