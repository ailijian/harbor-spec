from io import StringIO
from pathlib import Path

from rich.console import Console

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
