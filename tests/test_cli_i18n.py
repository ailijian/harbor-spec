import json
import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stderr, redirect_stdout
import sys
from datetime import datetime, timezone

import harbor.core.log_draft as log_draft
from rich.console import Console
from rich.prompt import Prompt

from harbor.cli.main import main
from harbor.core.change_window import write_change_window_snapshot
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
    monkeypatch.setattr("harbor.core.init_prompt._is_interactive", lambda _interactive=None: True)
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: None)
    def _yes_no(self, prompt_text, default):
        return ("scan roots" in prompt_text) or ("扫描范围" in prompt_text)

    zh_stream = StringIO()
    zh_asks = iter(["1", "1", ""])
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
    assert "请选择 LLM 服务商" in zh_out
    assert "Invalid input" not in zh_out

    en_stream = StringIO()
    en_asks = iter(["1", "1", ""])
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
    assert "Choose LLM provider" in en_out
    assert "输入无效" not in en_out


def test_log_write_non_interactive_requires_yes_uses_zh_i18n(tmp_path: Path):
    harbor_state = tmp_path / ".harbor" / "state" / "log"
    harbor_state.mkdir(parents=True, exist_ok=True)
    (harbor_state / "latest-draft.json").write_text(
        "{\n"
        '  "schema_version": "1.0",\n'
        '  "kind": "diary_draft",\n'
        '  "summary": "摘要",\n'
        '  "why": "原因"\n'
        "}\n",
        encoding="utf-8",
    )
    old = Path.cwd()
    old_env = os.environ.get("HARBOR_LANGUAGE")
    try:
        os.environ["HARBOR_LANGUAGE"] = "zh"
        os.chdir(tmp_path)
        code, out, err = run_cmd_with_err(["log", "write"])
        assert code == 1
        assert out == ""
        assert "非交互环境执行 `harbor log write` 必须显式传入 `--yes`。" in err
    finally:
        if old_env is None:
            os.environ.pop("HARBOR_LANGUAGE", None)
        else:
            os.environ["HARBOR_LANGUAGE"] = old_env
        os.chdir(old)


def test_log_draft_next_actions_use_zh_i18n(monkeypatch, tmp_path: Path):
    old = Path.cwd()
    old_env = os.environ.get("HARBOR_LANGUAGE")
    try:
        os.environ["HARBOR_LANGUAGE"] = "zh"
        os.chdir(tmp_path)
        write_change_window_snapshot(
            "checkpoint",
            repo_root=tmp_path,
            timestamp=datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
            git_head="abc123",
            workspace_dirty=True,
            changed_files=[{"path": "harbor/core/log_draft.py", "status": "M"}],
            summary={"status": "pass"},
            validation={"command": "checkpoint"},
        )
        monkeypatch.setattr(
            log_draft,
            "collect_git_workspace_state",
            lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
        )

        code, out, err = run_cmd_with_err(["log", "draft"])

        assert code == 0
        assert "下一步：" in out
        assert "写入正式 Diary（需要确认）：harbor log write" in out
        assert "非交互显式写入：harbor log write --yes" in out
        assert "已更新 latest draft cache" in err
    finally:
        if old_env is None:
            os.environ.pop("HARBOR_LANGUAGE", None)
        else:
            os.environ["HARBOR_LANGUAGE"] = old_env
        os.chdir(old)


def test_log_draft_insufficient_evidence_uses_zh_i18n_without_next_actions(monkeypatch, tmp_path: Path):
    old = Path.cwd()
    old_env = os.environ.get("HARBOR_LANGUAGE")
    try:
        os.environ["HARBOR_LANGUAGE"] = "zh"
        os.chdir(tmp_path)
        marker = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text('{"last_log_at":"2026-05-11T12:20:00Z"}\n', encoding="utf-8")
        (tmp_path / ".harbor" / "reports").mkdir(parents=True, exist_ok=True)
        (tmp_path / ".harbor" / "reports" / "checkpoint-only.json").write_text(
            json.dumps({"command": "checkpoint", "status": "pass"}, ensure_ascii=False),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            log_draft,
            "collect_git_workspace_state",
            lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
        )

        code, out, err = run_cmd_with_err(["log", "draft"])

        assert code == 0
        assert "未发现值得起草的新变更证据。" in out
        assert "未生成可写入的 Diary Draft。" in out
        assert "下一步：" not in out
        assert "已更新 latest draft cache" not in err
    finally:
        if old_env is None:
            os.environ.pop("HARBOR_LANGUAGE", None)
        else:
            os.environ["HARBOR_LANGUAGE"] = old_env
        os.chdir(old)


def test_log_message_invalid_type_uses_friendly_zh_error_without_traceback(tmp_path: Path):
    old = Path.cwd()
    old_env = os.environ.get("HARBOR_LANGUAGE")
    try:
        os.environ["HARBOR_LANGUAGE"] = "zh"
        os.chdir(tmp_path)
        code, out, err = run_cmd_with_err(["log", "-m", "摘要", "--type", "invalid-kind"])
        assert code == 1
        assert out == ""
        assert "非法 Diary type：invalid-kind。" in err
        assert "Traceback" not in err
        assert not (tmp_path / ".harbor" / "diary").exists()
    finally:
        if old_env is None:
            os.environ.pop("HARBOR_LANGUAGE", None)
        else:
            os.environ["HARBOR_LANGUAGE"] = old_env
        os.chdir(old)
