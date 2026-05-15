import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from importlib import resources
from io import StringIO
from pathlib import Path

import pytest

from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_help(argv):
    out = StringIO()
    err = StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        sys.argv = ["harbor"] + argv + ["--help"]
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def test_pyproject_version_and_description_are_release_ready():
    """Release packaging allows multi-segment PEP 440 releases like 1.4.2.2 plus a/b/rc suffixes."""
    pyproject_text = (_repo_root() / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    desc_match = re.search(r'^description\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)

    assert version_match is not None
    assert re.match(r"^\d+(?:\.\d+)+((a|b|rc)\d+)?$", version_match.group(1))

    assert desc_match is not None
    description = desc_match.group(1)
    assert "v1.0.2 reference implementation" not in description


def test_pyproject_declares_cli_runtime_dependencies():
    pyproject_text = (_repo_root() / "pyproject.toml").read_text(encoding="utf-8")
    deps_block_match = re.search(
        r"(?ms)^\s*dependencies\s*=\s*\[(.*?)\]",
        pyproject_text,
    )
    assert deps_block_match is not None
    deps_block = deps_block_match.group(1)
    assert '"rich' in deps_block
    assert '"prompt_toolkit>=3.0,<4"' in deps_block


def test_readme_contains_release_key_commands():
    readme_zh = (_repo_root() / "README.md").read_text(encoding="utf-8")
    required = [
        "harbor finish --sync-context",
        "harbor stale",
        "harbor doctor",
        "harbor module promote-skill",
        "harbor project structure --write",
    ]
    for phrase in required:
        assert phrase in readme_zh


def test_readme_en_contains_release_key_commands():
    readme_en = (_repo_root() / "README.en.md").read_text(encoding="utf-8")
    required = [
        "harbor finish --sync-context",
        "harbor stale",
        "harbor doctor",
        "harbor module promote-skill",
        "harbor project structure --write",
    ]
    for phrase in required:
        assert phrase in readme_en


def test_release_notes_include_v130_release_track():
    release_text = (_repo_root() / "RELEASE.md").read_text(encoding="utf-8")
    assert "# Harbor-spec v1.3.0 — Canonical Workspace 与 Agentic Context Governance" in release_text
    assert ".harbor/config/harbor.yaml" in release_text
    assert ".harbor/views/project-structure.md" in release_text
    assert ".harbor/views/modules/<module>/" in release_text
    assert ".harbor/state/" in release_text
    assert ".harbor/cache/" in release_text
    assert ".harbor/exports/" in release_text
    assert "### 1.2 Workflow Facade" in release_text
    assert "以下命令不属于默认任务流，必须由用户显式请求后再运行：" in release_text
    assert "harbor project structure" in release_text
    assert "canonical generated context views" in release_text


def test_release_notes_include_unreleased_v130_track():
    """Backward-compatible alias test name kept to avoid baseline missing_function drift."""
    test_release_notes_include_v130_release_track()


def test_release_notes_reference_python_ddt_reconciliation_report():
    release_text = (_repo_root() / "RELEASE.md").read_text(encoding="utf-8")
    assert "Python DDT advisory reconciliation completed" in release_text
    assert ".harbor/reports/python-ddt-advisory-reconciliation.md" in release_text
    assert "`ddt_advisory=5`" not in release_text


def test_release_notes_include_v145_plan_summary():
    release_text = (_repo_root() / "RELEASE.md").read_text(encoding="utf-8")
    assert "# Harbor-spec v1.4.5 — Workflow UX & Preview Productization" in release_text
    assert "状态：正式版" in release_text
    assert "## 版本主题" in release_text
    assert "Workflow UX & Preview Productization" in release_text
    assert "## 四条完成面" in release_text
    assert "1. DDT advisory reconciliation" in release_text
    assert "2. Progress Feedback Framework" in release_text
    assert "3. Runtime Performance Baseline" in release_text
    assert "4. Preview Productization" in release_text
    assert "## DDT Advisory 状态" in release_text
    assert "`ddt_version_baseline_missing=5`" in release_text
    assert "`ACCEPTED_BACKLOG`" in release_text
    assert "## 发布验证事实" in release_text
    assert "Diary：正式写入" in release_text
    assert "accepted baseline：已更新" in release_text
    assert "不做 JavaScript first-class governance" in release_text
    assert "不做大规模性能架构重构" in release_text
    assert "docs/《Harbor-spec v1.4.5｜Workflow UX & Preview Productization 定稿版》.md" in release_text


def test_python_ddt_reconciliation_report_is_present_and_explicit():
    report_text = (_repo_root() / ".harbor" / "reports" / "python-ddt-advisory-reconciliation.md").read_text(
        encoding="utf-8"
    )
    assert "# Python DDT Advisory Reconciliation Report" in report_text
    assert "Observed advisory bindings: `5`" in report_text
    assert "Unique `func_id`: `2`" in report_text
    assert "harbor.core.sync.SyncEngine.check_status" in report_text
    assert "harbor.utils.formatting.format_size" in report_text
    assert "`RESOLVE_NOW`" in report_text
    assert "`ACCEPTED_BACKLOG`" in report_text
    assert "`NEEDS_FOLLOW_UP`" in report_text


def test_source_of_truth_priority_and_conflict_docs_are_present():
    repo = _repo_root()

    readme_zh = (repo / "README.md").read_text(encoding="utf-8")
    assert "source of truth" in readme_zh.lower()
    assert "generated views are not source of truth" in readme_zh
    assert "canonical `.harbor/views/**`" in readme_zh
    assert "harbor workspace migrate --write" in readme_zh
    assert "not implemented" in readme_zh

    readme_en = (repo / "README.en.md").read_text(encoding="utf-8")
    assert "source of truth priority" in readme_en.lower()
    assert "generated views are not source of truth" in readme_en
    assert "canonical `.harbor/views/**`" in readme_en
    assert "harbor workspace migrate --write" in readme_en
    assert "not implemented" in readme_en.lower()

    agents_text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "lightweight entrypoint" in agents_text.lower()
    assert "## 3. Priority Rules" in agents_text
    assert "### 3.1 Safety Priority" in agents_text
    assert "### 3.2 Task Priority" in agents_text
    assert "## 5. Source of Truth Priority" in agents_text
    assert "prefer the more specific and local instruction" in agents_text
    assert "choose the safer path" in agents_text
    assert "state the conflict clearly" in agents_text
    assert "do not silently ignore the conflict" in agents_text
    assert "Do not auto-trust either implementation or contract when they conflict." in agents_text
    assert "Generated views help orientation but do not override code, contracts, schemas, tests, policy, or diary." in agents_text
    assert "Skills are not source of truth." in agents_text
    assert "Detailed rules live here:" in agents_text
    assert ".harbor/rules/project-rules-guide.md" in agents_text
    assert "## 11. Contract Authoring Triggers" in agents_text
    assert "## 12. Compact Python Contract Docstring Template" in agents_text
    assert "## 13. Compact TypeScript Contract Template" in agents_text
    assert ".harbor/state/**" in agents_text
    assert ".harbor/reports/**" in agents_text
    assert ".harbor/diary/**" in agents_text
    assert "All harbor log write variants, including --from-draft and --from-latest-draft, are Diary write paths and require explicit user authorization." in agents_text

    role_rules = (repo / ".harbor/rules/role-rules.md").read_text(encoding="utf-8")
    assert "Follow `AGENTS.md`" in role_rules
    assert ".harbor/views/**` is canonical generated context" in role_rules
    assert "Legacy/export artifacts are not source of truth" in role_rules
    assert "1. Runtime safety / tool-native deny rules / machine policy" not in role_rules


def test_help_recognizes_core_release_commands():
    help_targets = [
        [],
        ["finish"],
        ["docs"],
        ["module"],
        ["stale"],
        ["doctor"],
    ]

    for argv in help_targets:
        code, out, err = _run_help(argv)
        assert code == 0
        assert "usage: harbor" in out
        assert err == ""


def test_init_templates_package_resources_are_loadable():
    base = resources.files("harbor.templates.init").joinpath("files")
    required = [
        "AGENTS.md",
        "harbor/rules/role-rules.md",
        "harbor/rules/project-rules-guide.md",
        "harbor/policy.yaml",
        "harbor/safety.yaml",
    ]
    for rel in required:
        target = base
        for part in rel.split("/"):
            target = target.joinpath(part)
        text = target.read_text(encoding="utf-8")
        assert text.strip()
