from io import StringIO
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from harbor.core.init_wizard import InitWizard, InitWizardOptions


def test_wizard_language_prompt_comes_first(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    asks = iter(["1", "1"])

    def _fake_prompt(*args, **kwargs):
        return next(asks)

    monkeypatch.setattr(Prompt, "ask", staticmethod(_fake_prompt))

    def _fake_yes_no(self, prompt_text, default):
        if "scan roots" in prompt_text:
            return True
        if "governance starter files" in prompt_text:
            return False
        if "governance docs" in prompt_text:
            return False
        if "AI IDE" in prompt_text:
            return False
        if "LLM semantic audit" in prompt_text:
            return False
        if ".gitignore" in prompt_text:
            return False
        return default

    monkeypatch.setattr(InitWizard, "_ask_yes_no", _fake_yes_no)
    stream = StringIO()
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(dry_run=True),
        console=Console(file=stream, force_terminal=False, width=200),
    )
    wiz.run()
    out = stream.getvalue()
    assert out.index("选择工作语言 / Choose language") < out.index("你准备如何接入 HarborSpec")


def test_new_project_next_steps_do_not_suggest_immediate_checkpoint(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    stream = StringIO()
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            language="zh",
            project="new",
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=stream, force_terminal=False, width=200),
    )
    wiz.run()
    out = stream.getvalue()
    assert "harbor start" in out
    assert "harbor finish --sync-context" in out
    assert "harbor doctor" in out
    assert "harbor accept" in out
    assert "运行首次 checkpoint" not in out


def test_existing_project_next_steps_include_checkpoint_and_adopt(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    stream = StringIO()
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            language="en",
            project="existing",
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=stream, force_terminal=False, width=200),
    )
    wiz.run()
    out = stream.getvalue()
    assert "harbor project structure --write" in out
    assert "harbor checkpoint" in out
    assert "harbor adopt <path> --strategy safe --dry-run" in out


def test_dry_run_non_tty_uses_safe_defaults(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    stream = StringIO()
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(dry_run=True),
        console=Console(file=stream, force_terminal=False, width=200),
    )
    res = wiz.run()
    out = stream.getvalue()
    assert res.project == "new"
    assert "dry-run" in out
    # non-TTY safe defaults: governance yes, governance docs no, llm no
    assert "AGENTS.md" in out
    assert ".harbor/rules/project-rules-guide.md" in out
    assert ".harbor/rules/glossary.md" not in out


def test_init_wizard_dry_run_i18n_purity(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)

    zh_stream = StringIO()
    zh_wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            language="zh",
            project="new",
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=zh_stream, force_terminal=False, width=200),
    )
    zh_wiz.run()
    zh_out = zh_stream.getvalue()
    assert "探测到的代码根" in zh_out
    assert "探测到的排除项" in zh_out
    assert "建议下一步：" in zh_out
    assert "AI IDE 接入说明" in zh_out
    assert "Detected code roots" not in zh_out
    assert "Next steps:" not in zh_out

    en_stream = StringIO()
    en_wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            language="en",
            project="new",
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=en_stream, force_terminal=False, width=200),
    )
    en_wiz.run()
    en_out = en_stream.getvalue()
    assert "Detected code roots" in en_out
    assert "Detected excludes" in en_out
    assert "Next steps:" in en_out
    assert "AI IDE integration guidance" in en_out
    assert "探测到的代码根" not in en_out
    assert "AI IDE 接入说明" not in en_out
