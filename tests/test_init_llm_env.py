from io import StringIO
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from harbor.core.init_wizard import InitWizard, InitWizardOptions


def test_llm_env_append_missing_only_and_force_does_not_overwrite(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    env_file = tmp_path / ".env"
    env_file.write_text("HARBOR_LLM_API_KEY=old-secret\n", encoding="utf-8")
    monkeypatch.setenv("HARBOR_LLM_PROVIDER", "openai")
    monkeypatch.setenv("HARBOR_LLM_API_KEY", "new-secret")
    monkeypatch.setenv("HARBOR_LLM_BASE_URL", "https://api.openai.com/v1")

    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            force=True,
            language="zh",
            project="new",
            governance=False,
            governance_docs=False,
            llm=True,
            update_gitignore=False,
        ),
        console=Console(file=StringIO(), force_terminal=False),
    )
    wiz.run()
    content = env_file.read_text(encoding="utf-8")
    assert "HARBOR_LLM_API_KEY=old-secret" in content
    assert "HARBOR_LLM_PROVIDER=openai" in content
    assert "HARBOR_LLM_BASE_URL=https://api.openai.com/v1" in content
    assert "HARBOR_LANGUAGE=zh" in content


def test_gitignore_has_separate_managed_blocks(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    monkeypatch.setenv("HARBOR_LLM_PROVIDER", "openai")
    monkeypatch.setenv("HARBOR_LLM_API_KEY", "sk-1234567890")
    monkeypatch.setenv("HARBOR_LLM_BASE_URL", "https://api.openai.com/v1")

    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("node_modules/\n", encoding="utf-8")
    wiz = InitWizard(
        cwd=tmp_path,
        options=InitWizardOptions(
            language="en",
            project="existing",
            governance=False,
            governance_docs=False,
            llm=True,
            update_gitignore=True,
        ),
        console=Console(file=StringIO(), force_terminal=False),
    )
    wiz.run()
    text = gitignore.read_text(encoding="utf-8")
    assert "# >>> HarborSpec secrets (managed)" in text
    assert ".env" in text
    assert "# >>> HarborSpec runtime files (managed)" in text
    assert ".harbor/cache/" in text
    assert ".harbor/state/" in text
    assert ".harbor/exports/" in text


def test_gitignore_managed_blocks_are_idempotent(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: False)
    monkeypatch.setenv("HARBOR_LLM_PROVIDER", "openai")
    monkeypatch.setenv("HARBOR_LLM_API_KEY", "sk-1234567890")
    monkeypatch.setenv("HARBOR_LLM_BASE_URL", "https://api.openai.com/v1")

    opts = InitWizardOptions(
        language="en",
        project="existing",
        governance=False,
        governance_docs=False,
        llm=True,
        update_gitignore=True,
    )
    InitWizard(cwd=tmp_path, options=opts, console=Console(file=StringIO(), force_terminal=False)).run()
    InitWizard(cwd=tmp_path, options=opts, console=Console(file=StringIO(), force_terminal=False)).run()
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text.count("# >>> HarborSpec secrets (managed)") == 1
    assert text.count("# >>> HarborSpec runtime files (managed)") == 1


def test_llm_provider_alias_custom_writes_env(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    asks = iter(["compatible", "https://example.com/v1", "sk-xyz"])
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
            update_gitignore=False,
        ),
        console=Console(file=StringIO(), force_terminal=False),
    )
    wiz.run()
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "HARBOR_LLM_PROVIDER=custom" in text
    assert "HARBOR_LLM_BASE_URL=https://example.com/v1" in text


def test_llm_provider_alias_openai_writes_env(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("harbor.core.init_wizard._is_tty", lambda: True)
    asks = iter(["openai", ""])
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
            update_gitignore=False,
        ),
        console=Console(file=StringIO(), force_terminal=False),
    )
    wiz.run()
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "HARBOR_LLM_PROVIDER=openai" in text


def test_llm_provider_alias_number_2_writes_deepseek_env(tmp_path: Path, monkeypatch):
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
            update_gitignore=False,
        ),
        console=Console(file=StringIO(), force_terminal=False),
    )
    wiz.run()
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "HARBOR_LLM_PROVIDER=deepseek" in text
    assert "HARBOR_LLM_BASE_URL=https://api.deepseek.com/v1" in text


def test_init_wizard_source_removes_legacy_yes_no_brackets():
    src = (Path(__file__).resolve().parents[1] / "harbor" / "core" / "init_wizard.py").read_text(encoding="utf-8")
    assert "[Y/n]" not in src
    assert "[y/N]" not in src
