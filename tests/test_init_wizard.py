from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console
from rich.prompt import Prompt

from harbor.core.init_prompt import Choice, confirm, select_one
from harbor.core.init_wizard import InitWizard, InitWizardOptions


def test_wizard_language_prompt_comes_first(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    monkeypatch.setattr("harbor.core.init_prompt._is_interactive", lambda _interactive=None: True)
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: None)
    asks = iter(["1", "1", "1"])

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
    assert "默认扫描范围" in zh_out
    assert "已自动排除" in zh_out
    assert "harbor config list" in zh_out
    assert "建议下一步：" in zh_out
    assert "AI IDE 接入说明" in zh_out
    assert "Detected stack" not in zh_out
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
    assert "Default scan roots" in en_out
    assert "Auto-excluded" in en_out
    assert "harbor config list" in en_out
    assert "Next steps:" in en_out
    assert "AI IDE integration guidance" in en_out
    assert "检测到：技术栈" not in en_out
    assert "AI IDE 接入说明" not in en_out


def test_provider_fallback_accepts_name_deepseek(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    asks = iter(["deepseek", ""])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(asks)))
    def _yes_no(self, prompt_text, default):
        return ("scan roots" in prompt_text) or ("扫描范围" in prompt_text)
    monkeypatch.setattr(InitWizard, "_ask_yes_no", _yes_no)
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="zh",
            project="new",
            governance=False,
            governance_docs=False,
            llm=True,
            advice_mode="basic",
            update_gitignore=False,
        ),
        console=Console(file=StringIO(), force_terminal=False, width=200),
    )
    wiz.run()
    content = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "HARBOR_LLM_PROVIDER=deepseek" in content
    assert "HARBOR_LLM_BASE_URL=https://api.deepseek.com/v1" in content


def test_provider_fallback_accepts_number_2(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    asks = iter(["2", ""])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(asks)))
    def _yes_no(self, prompt_text, default):
        return ("scan roots" in prompt_text) or ("扫描范围" in prompt_text)
    monkeypatch.setattr(InitWizard, "_ask_yes_no", _yes_no)
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="en",
            project="new",
            governance=False,
            governance_docs=False,
            llm=True,
            advice_mode="basic",
            update_gitignore=False,
        ),
        console=Console(file=StringIO(), force_terminal=False, width=200),
    )
    wiz.run()
    content = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "HARBOR_LLM_PROVIDER=deepseek" in content
    assert "HARBOR_LLM_BASE_URL=https://api.deepseek.com/v1" in content


def test_provider_invalid_input_shows_available_options(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    asks = iter(["oops", "2", ""])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(asks)))
    def _yes_no(self, prompt_text, default):
        return ("scan roots" in prompt_text) or ("扫描范围" in prompt_text)
    monkeypatch.setattr(InitWizard, "_ask_yes_no", _yes_no)
    stream = StringIO()
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="zh",
            project="new",
            governance=False,
            governance_docs=False,
            llm=True,
            advice_mode="basic",
            update_gitignore=False,
        ),
        console=Console(file=stream, force_terminal=False, width=200),
    )
    wiz.run()
    out = stream.getvalue()
    assert "无效输入" in out
    assert "可选：1/2/3" in out


def test_non_tty_does_not_try_arrow_selector(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: (_ for _ in ()).throw(AssertionError()))
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(dry_run=True),
        console=Console(file=StringIO(), force_terminal=False, width=200),
    )
    wiz.run()


def test_pytest_env_does_not_try_arrow_selector(monkeypatch):
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_init_wizard.py::test_pytest_env_does_not_try_arrow_selector")
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "1"))
    selected = select_one(
        "Choose",
        options=[
            Choice(value="openai", label_zh="OpenAI", label_en="OpenAI", aliases=["openai"]),
            Choice(value="deepseek", label_zh="DeepSeek", label_en="DeepSeek", aliases=["deepseek"]),
        ],
        default="openai",
        language="en",
        interactive=None,
        console=Console(file=StringIO(), force_terminal=False, width=120),
    )
    assert selected == "openai"


def test_selector_source_does_not_use_full_screen_dialog():
    src = (Path(__file__).resolve().parents[1] / "harbor" / "core" / "init_prompt.py").read_text(encoding="utf-8")
    assert "radiolist_dialog" not in src
    assert "checkboxlist_dialog" not in src
    assert "full_screen=True" not in src
    assert "Confirm.ask" not in src
    assert "WordCompleter" not in src
    assert "complete_while_typing=True" not in src


def test_selector_fallback_does_not_repeat_selector_block(monkeypatch):
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "1"))
    stream = StringIO()
    selected = select_one(
        "Choose provider",
        options=[
            Choice(value="openai", label_zh="OpenAI", label_en="OpenAI", aliases=["openai"]),
            Choice(value="deepseek", label_zh="DeepSeek", label_en="DeepSeek", aliases=["deepseek"]),
        ],
        default="openai",
        language="en",
        interactive=True,
        console=Console(file=stream, force_terminal=False, width=120),
    )
    out = stream.getvalue()
    assert selected == "openai"
    assert "◇ Choose provider" in out
    assert out.count("◇ Choose provider") == 1
    assert out.count("1. OpenAI") == 1
    assert out.count("2. DeepSeek") == 1


def test_confirm_accepts_english_yes_no(monkeypatch):
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: None)
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "yes"))
    assert confirm("Use detected scan roots?", default=True, language="en", interactive=True) is True

    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "n"))
    assert confirm("Use detected scan roots?", default=True, language="en", interactive=True) is False


def test_confirm_accepts_chinese_yes_no(monkeypatch):
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: None)
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "是"))
    assert confirm("使用这些扫描范围吗？", default=True, language="zh", interactive=True) is True

    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "否"))
    assert confirm("使用这些扫描范围吗？", default=True, language="zh", interactive=True) is False


def test_init_wizard_source_has_no_legacy_yes_no_prompt_tokens():
    src = (Path(__file__).resolve().parents[1] / "harbor" / "core" / "init_wizard.py").read_text(encoding="utf-8")
    assert "Confirm.ask" not in src
    assert "Prompt.ask(choices=" not in src
    assert "[Y/n]" not in src
    assert "[y/N]" not in src
    assert "Use detected scan roots? (Y)" not in src


def test_confirm_shows_yes_no_labels_by_language(monkeypatch):
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: None)
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: "1"))

    en_stream = StringIO()
    confirm("Generate Harbor governance starter files?", default=True, language="en", interactive=True, console=Console(file=en_stream))
    en_out = en_stream.getvalue()
    assert "1. Yes" in en_out
    assert "2. No" in en_out

    zh_stream = StringIO()
    confirm("是否生成 Harbor 治理入口文件？", default=True, language="zh", interactive=True, console=Console(file=zh_stream))
    zh_out = zh_stream.getvalue()
    assert "1. 是" in zh_out
    assert "2. 否" in zh_out


def test_init_wizard_prompts_are_single_language_after_selection(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    monkeypatch.setattr("harbor.core.init_prompt._is_interactive", lambda _interactive=None: True)
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: None)

    en_answers = iter(["2", "1", "1", "1", "2"])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(en_answers)))
    en_stream = StringIO()
    InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=en_stream, force_terminal=False, width=200),
    ).run()
    en_out = en_stream.getvalue()
    assert "How do you want to onboard HarborSpec?" in en_out
    assert "Use detected scan roots?" in en_out
    assert "Show AI IDE integration guidance?" in en_out
    assert "你准备如何接入 HarborSpec？" not in en_out
    assert "使用这些扫描范围吗？" not in en_out
    assert "是否输出 AI IDE 接入说明？" not in en_out

    zh_answers = iter(["1", "1", "1", "1", "2"])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(zh_answers)))
    zh_stream = StringIO()
    InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=zh_stream, force_terminal=False, width=200),
    ).run()
    zh_out = zh_stream.getvalue()
    assert "你准备如何接入 HarborSpec？" in zh_out
    assert "使用这些扫描范围吗？" in zh_out
    assert "是否输出 AI IDE 接入说明？" in zh_out
    assert "How do you want to onboard HarborSpec?" not in zh_out
    assert "Use detected scan roots?" not in zh_out
    assert "Show AI IDE integration guidance?" not in zh_out


def test_init_wizard_repair_guidance_mode_prompt_is_localized(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    monkeypatch.setattr("harbor.core.init_prompt._is_interactive", lambda _interactive=None: True)
    monkeypatch.setattr("harbor.core.init_prompt._try_arrow_select", lambda **kwargs: None)

    en_answers = iter(["2", "1", "1", "1", "2"])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(en_answers)))
    en_stream = StringIO()
    InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=en_stream, force_terminal=False, width=200),
    ).run()
    en_out = en_stream.getvalue()
    assert "Repair guidance mode:" in en_out
    assert "deterministic suggestions, no LLM, recommended" in en_out
    assert "修复建议模式：" not in en_out

    zh_answers = iter(["1", "1", "1", "1", "2"])
    monkeypatch.setattr(Prompt, "ask", staticmethod(lambda *args, **kwargs: next(zh_answers)))
    zh_stream = StringIO()
    InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            dry_run=True,
            governance=False,
            governance_docs=False,
            llm=False,
            update_gitignore=False,
        ),
        console=Console(file=zh_stream, force_terminal=False, width=200),
    ).run()
    zh_out = zh_stream.getvalue()
    assert "修复建议模式：" in zh_out
    assert "确定性建议，不依赖 LLM，推荐" in zh_out
    assert "Repair guidance mode:" not in zh_out
