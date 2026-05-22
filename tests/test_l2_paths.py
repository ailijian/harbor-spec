import os
import json
from pathlib import Path

import pytest
import yaml

from harbor.core.context_integrity import build_context_integrity_metadata, split_frontmatter
from harbor.core.l2 import (
    L2Generator,
    _repo_relative_index_path,
    _to_repo_relative,
    normalize_indexed_module_candidate,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_l2_write_writes_canonical_and_module_readme_export_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    paths = gen.write("harbor/core", "# Module: harbor/core\n", force=True)
    assert paths is not None
    assert [p.as_posix() for p in paths] == [
        (tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md").as_posix(),
        (tmp_path / "harbor" / "core" / "README.md").as_posix(),
    ]
    assert (tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md").exists()
    assert (tmp_path / "harbor" / "core" / "README.md").exists()
    assert (tmp_path / ".harbor" / "views" / "l2" / "_meta.json").exists()
    canonical = (tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md").read_text(encoding="utf-8")
    exported = (tmp_path / "harbor" / "core" / "README.md").read_text(encoding="utf-8")
    assert canonical.startswith("---\n")
    assert 'view_type: "l2_readme"' in canonical
    assert not exported.startswith("---\n")


def test_l2_export_module_readme_disabled_writes_only_canonical(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_yaml(
        tmp_path / ".harbor" / "config" / "harbor.yaml",
        {"l2": {"export": {"module_readme": {"enabled": False}}}},
    )
    gen = L2Generator()
    paths = gen.write("harbor/core", "# Module: harbor/core\n", force=True)
    assert paths is not None
    assert [p.as_posix() for p in paths] == [
        (tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md").as_posix(),
    ]
    assert (tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md").exists()
    canonical = (tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md").read_text(encoding="utf-8")
    assert canonical.startswith("---\n")
    assert not (tmp_path / "harbor" / "core" / "README.md").exists()


def test_l2_meta_reads_legacy_then_writes_canonical_only(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = "harbor/core"
    md = "# Module: harbor/core\n"
    legacy_meta = tmp_path / ".harbor" / "l2_meta.json"
    legacy_meta.parent.mkdir(parents=True, exist_ok=True)
    legacy_payload = {module: L2Generator().compute_meta_hash(md)}
    legacy_meta.write_text(json.dumps(legacy_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    gen = L2Generator()
    first_paths = gen.write(module, md, force=False)
    assert first_paths is not None
    assert (tmp_path / ".harbor" / "views" / "l2" / "_meta.json").exists()

    paths = gen.write(module, md, force=True)
    assert paths is not None
    canonical_meta = tmp_path / ".harbor" / "views" / "l2" / "_meta.json"
    assert canonical_meta.exists()
    written_meta = json.loads(canonical_meta.read_text(encoding="utf-8"))
    assert written_meta[module] == legacy_payload[module]
    assert json.loads(legacy_meta.read_text(encoding="utf-8")) == legacy_payload


def test_l2_canonical_root_cannot_escape_repo_root(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_yaml(
        tmp_path / ".harbor" / "config" / "harbor.yaml",
        {"l2": {"canonical_root": "../outside"}},
    )
    with pytest.raises(ValueError, match="escapes repo root"):
        L2Generator()


def test_l2_module_path_traversal_rejected_with_export_enabled(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    with pytest.raises(ValueError, match="Relative parent segments are not allowed"):
        gen.write("../outside/module", "# bad\n", force=True)
    assert not (tmp_path / ".harbor" / "views" / "l2").exists()
    assert not (tmp_path / "outside").exists()


def test_l2_module_path_traversal_rejected_with_export_disabled(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_yaml(
        tmp_path / ".harbor" / "config" / "harbor.yaml",
        {"l2": {"export": {"module_readme": {"enabled": False}}}},
    )
    gen = L2Generator()
    with pytest.raises(ValueError, match="Relative parent segments are not allowed"):
        gen.write("harbor/../../outside", "# bad\n", force=True)
    assert not (tmp_path / ".harbor" / "views" / "l2").exists()
    assert not (tmp_path / "outside").exists()


def test_l2_absolute_module_path_outside_repo_still_rejected(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    with pytest.raises(ValueError, match="escapes repo root"):
        gen.write("C:/Users/GM/AppData/Local/Temp/demo", "# bad\n", force=True)


def test_normalize_indexed_module_candidate_maps_repo_absolute_file_path(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    abs_file = (tmp_path / "harbor" / "core" / "l2.py").resolve()
    module = normalize_indexed_module_candidate(str(abs_file), repo_root=tmp_path.resolve())
    assert module == "harbor/core"


def test_l2_repo_relative_helpers_handle_duplicate_repo_name_root(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "harbor-spec" / "harbor-spec"
    file_path = repo_root / "tests" / "test_sync_engine.py"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    monkeypatch.chdir(repo_root)

    rel = _repo_relative_index_path(str(file_path.resolve()), repo_root=repo_root)
    display = _to_repo_relative(str(file_path.resolve()), repo_root=repo_root)
    module = normalize_indexed_module_candidate(str(file_path.resolve()), repo_root=repo_root)

    assert rel == "tests/test_sync_engine.py"
    assert display == "tests/test_sync_engine.py"
    assert module == "tests"
    assert not rel.startswith("harbor-spec/")


@pytest.mark.skipif(os.name != "nt", reason="Windows path normalization scenario")
def test_l2_repo_relative_helpers_normalize_github_actions_windows_path():
    repo_root = Path(r"D:\a\harbor-spec\harbor-spec")
    path_text = r"D:\a\harbor-spec\harbor-spec\tests\test_sync_engine.py"

    assert _repo_relative_index_path(path_text, repo_root=repo_root) == "tests/test_sync_engine.py"
    assert _to_repo_relative(path_text, repo_root=repo_root) == "tests/test_sync_engine.py"
    assert normalize_indexed_module_candidate(path_text, repo_root=repo_root) == "tests"


def test_l2_repeat_write_keeps_canonical_content_when_body_unchanged(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    _ = gen.write("harbor/core", "# Module: harbor/core\n", force=True)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    first = canonical.read_text(encoding="utf-8")
    _ = gen.write("harbor/core", "# Module: harbor/core\n", force=True)
    second = canonical.read_text(encoding="utf-8")
    assert first == second


def test_l2_write_refreshes_canonical_when_body_hash_matches_but_frontmatter_drifted(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    body = "# Module: harbor/core\n"
    _ = gen.write("harbor/core", body, force=True)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    first = canonical.read_text(encoding="utf-8")

    original_builder = build_context_integrity_metadata

    def _patched_builder(*args, **kwargs):
        payload = original_builder(*args, **kwargs)
        payload["generator_fingerprint"] = "sha256:patched"
        return payload

    monkeypatch.setattr("harbor.core.l2.build_context_integrity_metadata", _patched_builder)

    paths = gen.write("harbor/core", body, force=False)
    second = canonical.read_text(encoding="utf-8")

    assert paths is not None
    assert canonical in paths
    assert first != second
    assert 'generator_fingerprint: "sha256:patched"' in second


def test_l2_meta_hash_matches_canonical_body_after_write(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    body = "# Module: harbor/core\n"
    _ = gen.write("harbor/core", body, force=True)

    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    canonical_text = canonical.read_text(encoding="utf-8")
    _, canonical_body = split_frontmatter(canonical_text)
    meta_payload = json.loads((tmp_path / ".harbor" / "views" / "l2" / "_meta.json").read_text(encoding="utf-8"))

    assert meta_payload["harbor/core"] == gen.compute_meta_hash(body)
    assert meta_payload["harbor/core"] == gen.compute_meta_hash(canonical_body)


def test_l2_generate_uses_summary_first_and_dependency_summary(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n- harbor/**\n- tests/**\nexclude_paths: []\n", encoding="utf-8")

    sample = tmp_path / "harbor" / "core" / "sample.py"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text(
        '''import harbor
from harbor.utils.formatting import noop

def run(value: int) -> int:
    """Return the provided integer unchanged.

    Behavior:
      - Returns the provided integer unchanged.

    Args:
      value (int): Input integer.

    Returns:
      int: Same integer value.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    """
    return noop(value)
''',
        encoding="utf-8",
    )
    util = tmp_path / "harbor" / "utils" / "formatting.py"
    util.parent.mkdir(parents=True, exist_ok=True)
    util.write_text("def noop(value):\n    return value\n", encoding="utf-8")

    test_file = tmp_path / "tests" / "test_sample.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(
        "from harbor.core.sample import run\n\n"
        "def test_run_value():\n"
        "    assert run(1) == 1\n",
        encoding="utf-8",
    )

    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        json.dumps(
            {
                "files": {
                    "harbor/core/sample.py": {
                        "items": [
                            {
                                "id": "harbor.core.sample.run",
                                "qualified_name": "harbor.core.sample.run",
                                "name": "run",
                                "lineno": 3,
                                "scope": "public",
                                "strictness": "strict",
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    md = L2Generator(index_path=idx).generate("harbor/core")

    assert "## Public API Summary" in md
    assert "## High-Risk Targets" in md
    assert "### Contract / DDT Coverage Gaps" in md
    assert "## Full Indexed Contracts" in md
    assert "<details>" in md
    assert "## Dependency Summary" in md
    assert "**Outbound Dependencies**" in md
    assert "**Inbound Dependents**" in md
    assert "## Public API\n" not in md
    assert "## Dependency (MVP)" not in md
    assert "harbor/utils (1 edges): harbor/utils/formatting" in md
    assert "harbor (root package)" not in md
    assert "- tests" in md


def test_l2_dependency_summary_reuses_repo_import_graph_and_filters_root_package(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    core = tmp_path / "harbor" / "core" / "sample.py"
    core.parent.mkdir(parents=True, exist_ok=True)
    core.write_text(
        "import harbor\n"
        "from harbor.utils.formatting import noop\n\n"
        "def run(value):\n"
        "    return noop(value)\n",
        encoding="utf-8",
    )
    cli = tmp_path / "harbor" / "cli" / "main.py"
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text(
        "from harbor.core.sample import run\n\n"
        "def main():\n"
        "    return run(1)\n",
        encoding="utf-8",
    )
    util = tmp_path / "harbor" / "utils" / "formatting.py"
    util.parent.mkdir(parents=True, exist_ok=True)
    util.write_text("def noop(value):\n    return value\n", encoding="utf-8")
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        json.dumps(
            {
                "files": {
                    "harbor/core/sample.py": {"items": [{"id": "harbor.core.sample.run", "name": "run"}]},
                    "harbor/cli/main.py": {"items": [{"id": "harbor.cli.main.main", "name": "main"}]},
                }
            }
        ),
        encoding="utf-8",
    )

    import harbor.core.l2 as l2_module

    build_calls = 0
    original_build = l2_module._build_repo_import_graph

    def spy_build(repo_root: Path):
        nonlocal build_calls
        build_calls += 1
        return original_build(repo_root)

    monkeypatch.setattr(l2_module, "_build_repo_import_graph", spy_build)
    gen = L2Generator(index_path=idx)

    core_md = gen.generate("harbor/core")
    cli_md = gen.generate("harbor/cli")

    assert build_calls == 1
    assert "harbor (root package)" not in core_md
    assert "harbor/utils (1 edges): harbor/utils/formatting" in core_md
    assert "harbor/cli (1 edges): harbor/cli" in core_md
    assert "harbor/core (1 edges): harbor/core/sample" in cli_md


def test_l2_generate_displays_unknown_strictness_instead_of_python_none(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        json.dumps(
            {
                "files": {
                    "harbor/core/sample.py": {
                        "items": [
                            {
                                "id": "harbor.core.sample.run",
                                "qualified_name": "harbor.core.sample.run",
                                "name": "run",
                                "lineno": 1,
                                "scope": "unknown",
                                "strictness": None,
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    md = L2Generator(index_path=idx).generate("harbor/core")

    assert "| harbor.core.sample.run | harbor/core/sample.py | unknown | unknown |" in md
    assert "| unknown | None |" not in md


def test_l2_meta_write_sanitizes_absolute_and_outside_repo_keys(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    body = "# Module: harbor/core\n"

    fixtures_file = tmp_path / "tests" / "fixtures_sqlite" / "sample.py"
    fixtures_file.parent.mkdir(parents=True, exist_ok=True)
    fixtures_file.write_text("def sample():\n    return 1\n", encoding="utf-8")

    canonical_meta = tmp_path / ".harbor" / "views" / "l2" / "_meta.json"
    canonical_meta.parent.mkdir(parents=True, exist_ok=True)
    canonical_meta.write_text(
        json.dumps(
            {
                str((tmp_path / "harbor" / "core").resolve()): "dir-hash",
                str(fixtures_file.resolve()): "file-hash",
                "harbor\\cli": "cli-hash",
                "C:/Users/GM/AppData/Local/Temp/pytest-of-GM/outside.py": "outside-hash",
                "": "blank-hash",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    _ = gen.write("harbor/core", body, force=True)
    meta_payload = json.loads(canonical_meta.read_text(encoding="utf-8"))

    assert meta_payload["harbor/core"] == gen.compute_meta_hash(body)
    assert meta_payload["tests/fixtures_sqlite"] == "file-hash"
    assert meta_payload["harbor/cli"] == "cli-hash"
    assert all("C:/" not in key for key in meta_payload)
    assert all("AppData" not in key for key in meta_payload)
    assert "" not in meta_payload


def test_l2_write_without_force_still_cleans_dirty_meta_keys(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gen = L2Generator()
    body = "# Module: harbor/core\n## Public API Summary\n"
    _ = gen.write("harbor/core", body, force=True)

    canonical_meta = tmp_path / ".harbor" / "views" / "l2" / "_meta.json"
    payload = json.loads(canonical_meta.read_text(encoding="utf-8"))
    payload["C:/Users/GM/AppData/Local/Temp/pytest-of-GM/outside.py"] = "outside-hash"
    canonical_meta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = gen.write("harbor/core", body, force=False)
    cleaned = json.loads(canonical_meta.read_text(encoding="utf-8"))

    assert result is not None
    assert all("C:/" not in key for key in cleaned)
    assert cleaned["harbor/core"] == gen.compute_meta_hash(body)
