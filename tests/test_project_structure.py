import json
import re
from pathlib import Path

import harbor
from harbor.core.project_structure import (
    classify_project_area,
    collect_project_structure_integrity_inputs,
    collect_project_structure_context,
    generate_project_structure_markdown,
    rank_key_file,
    write_project_structure,
)


def _write_index(root: Path) -> Path:
    idx = root / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": {
            "harbor/core/a.py": {
                "items": [{"id": "a1"}, {"id": "a2"}],
            },
            "harbor/core/b.py": {
                "items": [{"id": "b1"}],
            },
            "harbor/core/c.py": {
                "items": [{"id": "c1"}],
            },
            "harbor/core/d.py": {
                "items": [{"id": "d1"}],
            },
            "harbor/core/README.md": {
                "items": [],
            },
            "harbor/core/__init__.py": {
                "items": [],
            },
            "harbor/cli/__init__.py": {
                "items": [],
            },
            r"harbor\cli\main.py": {
                "items": [{"id": "cli1"}],
            },
            "tests/test_core.py": {
                "items": [],
            },
            "C:/external/other-project/outside.py": {
                "items": [{"id": "outside"}],
            },
        }
    }
    idx.write_text(json.dumps(payload), encoding="utf-8")
    return idx


def _write_source_repo(root: Path) -> None:
    (root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "harbor-spec"',
                'version = "1.4.2.2"',
                "",
                "[project.scripts]",
                'harbor = "harbor.cli.main:main"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cfg = root / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n- harbor/**\n- tests/**\nexclude_paths: []\n", encoding="utf-8")
    pkg = root / "harbor" / "core"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "sample.py").write_text(
        '''def run(value: int) -> int:
    """Return the provided value unchanged.

    Behavior:
      - Returns the provided integer unchanged.

    Args:
      value (int): Input integer.

    Returns:
      int: Same integer value.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    """
    return value
''',
        encoding="utf-8",
    )
    tests_dir = root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text("def test_sample():\n    assert True\n", encoding="utf-8")


def test_collect_project_structure_context_builds_expected_flags_and_counts(tmp_path: Path):
    idx = _write_index(tmp_path)
    (tmp_path / "harbor" / "core" / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "harbor" / "core" / "README.md").write_text("# core", encoding="utf-8")

    cap = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core"
    cap.mkdir(parents=True, exist_ok=True)
    (cap / "module-card.md").write_text("x", encoding="utf-8")
    (cap / "review-checklist.md").write_text("x", encoding="utf-8")
    (cap / "debug-playbook.md").write_text("x", encoding="utf-8")

    skill = tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text("x", encoding="utf-8")

    context = collect_project_structure_context(tmp_path, index_path=idx)
    modules = {m.module: m for m in context.modules}

    assert [m.module for m in context.modules] == ["harbor/cli", "harbor/core"]

    core = modules["harbor/core"]
    assert core.indexed_files_count == 6
    assert core.indexed_contracts_count == 5
    assert core.has_l2_readme is True
    assert core.has_canonical_module_capsule is True
    assert core.has_capsule_export is False
    assert core.has_skill is True
    assert len(core.key_files) == 4
    assert core.key_files[-1] == "... (+3 more)"
    assert core.key_files[0] != "harbor/core/README.md"
    assert all("__init__.py" not in item for item in core.key_files[:3])

    cli = modules["harbor/cli"]
    assert cli.indexed_files_count == 2
    assert cli.indexed_contracts_count == 1
    assert cli.has_l2_readme is False
    assert cli.has_canonical_module_capsule is False
    assert cli.has_capsule_export is False
    assert cli.has_skill is False
    assert cli.key_files[0] == "harbor/cli/main.py"


def test_collect_project_structure_context_filters_windows_absolute_paths_on_posix(tmp_path: Path):
    idx = _write_index(tmp_path)
    context = collect_project_structure_context(tmp_path, index_path=idx)

    module_names = [m.module for m in context.modules]
    supporting_names = [a.area for a in context.supporting_areas]

    assert "C:/external/other-project" not in module_names
    assert "C:/external/other-project" not in supporting_names


def test_collect_project_structure_reads_metadata_from_pyproject(tmp_path: Path):
    idx = _write_index(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "harbor-spec"',
                'version = "1.3.0"',
                'description = "desc"',
                "",
                "[project.scripts]",
                'harbor = "harbor.cli.main:main"',
            ]
        ),
        encoding="utf-8",
    )

    context = collect_project_structure_context(tmp_path, index_path=idx)
    assert context.metadata.name == "harbor-spec"
    assert context.metadata.version == "1.3.0"
    assert context.metadata.description == "desc"
    assert context.metadata.entrypoint == "harbor.cli.main:main"


def test_generate_markdown_contains_required_sections_and_is_deterministic(tmp_path: Path):
    idx = _write_index(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "\n".join(["[project]", 'name = "harbor-spec"', '[project.scripts]', 'harbor = "harbor.cli.main:main"']),
        encoding="utf-8",
    )
    context = collect_project_structure_context(tmp_path, index_path=idx)
    markdown = generate_project_structure_markdown(context)

    assert "## Project Metadata" in markdown
    assert "## Discovery Mode" in markdown
    assert "## Source of Truth" in markdown
    assert "## Key Areas" in markdown
    assert "## Code Modules" in markdown
    assert "## Supporting Areas" in markdown
    assert "## Module Index" not in markdown
    assert "## Main Harbor Workflows" in markdown
    assert "## Where to Look First" in markdown
    assert "## AI Context Loading Guidance" in markdown
    assert "## Regeneration" in markdown
    assert "| Mode | Harbor index |" in markdown
    assert "| Module | Key Files | L2 README | Canonical Capsule | Docs Export | Skill |" in markdown
    assert "3. `.harbor/views/project-structure.md`" in markdown
    assert "3. `docs/harbor/project-structure.md`" not in markdown
    assert "harbor log" not in markdown
    assert "harbor accept" not in markdown

    root_text = str(tmp_path).replace("\\", "/")
    assert root_text not in markdown
    assert "C:/external/other-project" not in markdown
    assert "outside.py" not in markdown
    assert re.search(r"\d{4}-\d{2}-\d{2}", markdown) is None


def test_collect_project_structure_context_distinguishes_canonical_capsule_and_docs_export(tmp_path: Path):
    idx = _write_index(tmp_path)
    canonical = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core"
    canonical.mkdir(parents=True, exist_ok=True)
    (canonical / "module-card.md").write_text("canonical\n", encoding="utf-8")
    (canonical / "review-checklist.md").write_text("canonical\n", encoding="utf-8")
    (canonical / "debug-playbook.md").write_text("canonical\n", encoding="utf-8")

    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "views:\n  export:\n    docs:\n      enabled: true\n      root: docs/harbor\n",
        encoding="utf-8",
    )

    exported = tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core"
    exported.mkdir(parents=True, exist_ok=True)
    (exported / "module-card.md").write_text("export\n", encoding="utf-8")
    (exported / "review-checklist.md").write_text("export\n", encoding="utf-8")
    (exported / "debug-playbook.md").write_text("export\n", encoding="utf-8")

    context = collect_project_structure_context(tmp_path, index_path=idx)
    modules = {m.module: m for m in context.modules}
    core = modules["harbor/core"]

    assert core.has_canonical_module_capsule is True
    assert core.has_capsule_export is True


def test_collect_project_structure_context_uses_filesystem_fallback_when_index_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "\n".join(["[project]", 'name = "harbor-spec"', '[project.scripts]', 'harbor = "harbor.cli.main:main"']),
        encoding="utf-8",
    )
    (tmp_path / "harbor" / "cli").mkdir(parents=True, exist_ok=True)
    (tmp_path / "harbor" / "core").mkdir(parents=True, exist_ok=True)
    (tmp_path / "harbor" / "utils").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "harbor" / "cli" / "main.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (tmp_path / "harbor" / "core" / "x.py").write_text("def x():\n    pass\n", encoding="utf-8")
    (tmp_path / "harbor" / "utils" / "u.py").write_text("def u():\n    pass\n", encoding="utf-8")
    (tmp_path / "tests" / "test_x.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")

    context = collect_project_structure_context(tmp_path, index_path=tmp_path / ".harbor" / "cache" / "l3_index.json")
    module_names = [m.module for m in context.modules]
    supporting_names = [a.area for a in context.supporting_areas]

    assert context.key_areas
    assert "harbor/cli" in module_names
    assert "harbor/core" in module_names
    assert "harbor/utils" in module_names
    assert "tests" in supporting_names
    assert context.discovery_mode == "Harbor index"
    assert context.contract_aware == "yes"
    assert any(m.indexed_files_count > 0 for m in context.modules)
    markdown = generate_project_structure_markdown(context)
    assert "| Mode | Harbor index |" in markdown
    assert "This view was generated from Harbor indexed records." in markdown


def test_collect_project_structure_context_prefers_fresh_source_over_cache(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_source_repo(tmp_path)
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        json.dumps(
            {
                "files": {
                    "harbor/core/stale.py": {
                        "items": [{"id": "stale", "qualified_name": "harbor.core.stale.old"}]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    context = collect_project_structure_context(tmp_path)
    source_paths, contract_records = collect_project_structure_integrity_inputs(tmp_path)

    assert context.discovery_mode == "Harbor index"
    assert "harbor/core/sample.py" in source_paths
    assert "harbor/core/stale.py" not in source_paths
    assert all(record["file"] != "harbor/core/stale.py" for record in contract_records)
    assert any(module.module == "harbor/core" for module in context.modules)
    core = next(module for module in context.modules if module.module == "harbor/core")
    assert "harbor/core/sample.py" in core.key_files
    assert "harbor/core/stale.py" not in core.key_files


def test_classify_project_area_is_stable():
    assert classify_project_area("harbor/cli") == "code"
    assert classify_project_area("harbor/core") == "code"
    assert classify_project_area("harbor/utils") == "code"
    assert classify_project_area("tests") == "supporting"
    assert classify_project_area("docs/harbor") == "supporting"


def test_rank_key_file_prioritizes_entrypoints_and_impl_files():
    files = [
        "harbor/cli/__init__.py",
        "harbor/cli/main.py",
        "harbor/core/README.md",
        "harbor/core/project_structure.py",
        "harbor/core/index.py",
        "tests/test_core.py",
    ]
    ranked = sorted(files, key=rank_key_file)
    assert ranked[0] == "harbor/cli/main.py"
    assert ranked.index("harbor/core/README.md") > ranked.index("harbor/core/index.py")
    assert ranked[-1] == "harbor/cli/__init__.py"


def test_write_project_structure_returns_canonical_first(tmp_path: Path):
    idx = _write_index(tmp_path)
    context = collect_project_structure_context(tmp_path, index_path=idx)
    result = write_project_structure(context, tmp_path)

    assert result.canonical_path == (tmp_path / ".harbor" / "views" / "project-structure.md").resolve()
    assert result.exported_paths == []
    assert result.canonical_path.exists()
    text = result.canonical_path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert f'harbor_version: "{harbor.__version__}"' in text
    assert 'view_type: "project_structure"' in text
    assert "source_path_count:" in text


def test_write_project_structure_is_stable_with_or_without_cache(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_source_repo(tmp_path)

    first_result = write_project_structure(collect_project_structure_context(tmp_path), tmp_path)
    first_text = first_result.canonical_path.read_text(encoding="utf-8")

    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        json.dumps(
            {
                "files": {
                    "harbor/core/stale.py": {
                        "items": [{"id": "stale", "qualified_name": "harbor.core.stale.old"}]
                    },
                    "docs/legacy.md": {"items": []},
                }
            }
        ),
        encoding="utf-8",
    )

    second_result = write_project_structure(collect_project_structure_context(tmp_path), tmp_path)
    second_text = second_result.canonical_path.read_text(encoding="utf-8")

    assert first_text == second_text
    assert '- "harbor/core/stale.py"' not in second_text
    assert '- "docs/legacy.md"' not in second_text
