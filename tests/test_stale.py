import json
import os
from types import SimpleNamespace
from pathlib import Path

import pytest

from harbor.core.l2 import L2Generator
from harbor.core.module_capsule import collect_module_context
from harbor.core.module_capsule import write_module_capsule
from harbor.core.stale import (
    _sanitize_single_path,
    check_l2_readme_stale,
    check_module_derived_views_stale,
    stale_report_to_dict,
)


def _write_index(tmp_path: Path) -> None:
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": {
            "harbor/core/sync.py": {
                "items": [
                    {
                        "id": "harbor.core.sync.SyncEngine.check_status",
                        "qualified_name": "SyncEngine.check_status",
                        "scope": "public",
                        "strictness": "standard",
                    }
                ]
            }
        }
    }
    idx.write_text(json.dumps(payload), encoding="utf-8")


def _write_l2_export_config(tmp_path: Path, enabled: bool) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "l2:\n  export:\n    module_readme:\n      enabled: " + ("true" if enabled else "false") + "\n",
        encoding="utf-8",
    )


def _write_sample_repo(tmp_path: Path) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n- harbor/**\n- tests/**\nexclude_paths: []\n", encoding="utf-8")

    pkg = tmp_path / "harbor" / "core"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "sample.py").write_text(
        '''def run(value: int) -> int:
    """Return the provided value.

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

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text("def test_sample():\n    assert True\n", encoding="utf-8")


def _write_typescript_sample_repo(tmp_path: Path) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "code_roots:\n- src/**\nexclude_paths: []\nlanguages:\n  python:\n    enabled: true\n  typescript:\n    enabled: true\n",
        encoding="utf-8",
    )

    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "sample.ts").write_text(
        '''/**
 * Return the provided value.
 *
 * @param value Input integer.
 * @returns Same integer value.
 * @harbor.scope public
 * @harbor.l3_strictness strict
 */
export function run(value: number): number { return value; }
''',
        encoding="utf-8",
    )


def test_l2_readme_stale_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    result = check_l2_readme_stale("harbor/core")
    assert result.status == "stale"
    assert result.reason == "canonical README.md not found"
    assert result.suggested_command == "harbor docs --module harbor/core --write"


def test_l2_readme_up_to_date_when_content_matches_except_timestamp(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    readme = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        "A\nGenerated At: 2020-01-01T00:00:00Z\nB\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "A\nGenerated At: 2026-01-01T00:00:00Z\nB\n",
    )
    result = check_l2_readme_stale("harbor/core")
    assert result.status == "up_to_date"


def test_l2_readme_stale_when_content_differs(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    readme = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text("OLD\n", encoding="utf-8")
    monkeypatch.setattr("harbor.core.stale.L2Generator.generate", lambda self, module: "NEW\n")
    result = check_l2_readme_stale("harbor/core")
    assert result.status == "stale"
    assert result.reason == "README content mismatch"


def test_l2_readme_unknown_when_no_indexed_records(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    result = check_l2_readme_stale("harbor/unknown")
    assert result.status == "unknown"
    assert result.reason == "no indexed records found for module"
    assert result.suggested_command is None


def test_l2_readme_check_does_not_write_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    readme = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    original = "SAME\nGenerated At: 2020-01-01T00:00:00Z\n"
    readme.write_text(original, encoding="utf-8")
    before = readme.read_text(encoding="utf-8")
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "SAME\nGenerated At: 2026-01-01T00:00:00Z\n",
    )
    _ = check_l2_readme_stale("harbor/core")
    after = readme.read_text(encoding="utf-8")
    assert before == after


def test_check_module_derived_views_stale_returns_both_views(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    monkeypatch.setattr("harbor.core.stale.L2Generator.generate", lambda self, module: "NEW\n")
    summary = check_module_derived_views_stale("harbor/core")
    assert summary.module == "harbor/core"
    assert summary.l2_readme.view == "L2 README"
    assert summary.l2_readme.status == "stale"
    assert summary.l2_readme_export.view == "L2 README Export"
    assert summary.l2_readme_export.status == "unknown"
    assert summary.module_capsule.view == "Module Capsule"
    assert summary.module_capsule.status == "stale"
    assert summary.module_capsule.reason == "module-card.md not found"


def test_check_module_derived_views_stale_unknown_consistency_when_no_indexed_records(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    summary = check_module_derived_views_stale("harbor/unknown")
    assert summary.l2_readme.status == "unknown"
    assert summary.l2_readme_export.status == "unknown"
    assert summary.module_capsule.status == "unknown"
    assert summary.module_capsule.reason == "no indexed records found for module"


def test_stale_sanitize_single_path_uses_full_repo_root_for_duplicate_repo_name(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "harbor-spec" / "harbor-spec"
    module_dir = repo_root / "harbor" / "core"
    module_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(repo_root)

    sanitized = _sanitize_single_path(str(module_dir.resolve()))

    assert sanitized == "harbor/core"
    assert sanitized != "harbor-spec/harbor/core"


@pytest.mark.skipif(os.name != "nt", reason="Windows path normalization scenario")
def test_stale_sanitize_single_path_normalizes_github_actions_windows_module_path():
    repo_root = Path(r"D:\a\harbor-spec\harbor-spec")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("harbor.core.stale.Path.cwd", lambda: repo_root)
        sanitized = _sanitize_single_path(r"D:\a\harbor-spec\harbor-spec\harbor\core")

    assert sanitized == "harbor/core"
    assert sanitized != "harbor-spec/harbor/core"


def test_l2_export_ok_when_canonical_up_to_date_and_export_matches(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_l2_export_config(tmp_path, enabled=True)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    exported = tmp_path / "harbor" / "core" / "README.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    exported.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("A\nGenerated At: 2020-01-01T00:00:00Z\nB\n", encoding="utf-8")
    exported.write_text("A\nGenerated At: 2026-01-01T00:00:00Z\nB\n", encoding="utf-8")
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "A\nGenerated At: 2026-01-01T00:00:00Z\nB\n",
    )
    summary = check_module_derived_views_stale("harbor/core")
    assert summary.l2_readme.status == "up_to_date"
    assert summary.l2_readme_export.status == "up_to_date"


def test_l2_export_ok_when_canonical_has_frontmatter_and_export_is_plain_body(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_l2_export_config(tmp_path, enabled=True)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    exported = tmp_path / "harbor" / "core" / "README.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    exported.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(
        '---\nview_type: "l2_readme"\nsource_fingerprint: "sha256:x"\ncontract_fingerprint: "sha256:y"\ngenerator_fingerprint: "sha256:z"\ngenerated_at: "2026-01-01T00:00:00Z"\n---\n\n# Module: harbor/core\n',
        encoding="utf-8",
    )
    exported.write_text("# Module: harbor/core\n", encoding="utf-8")
    monkeypatch.setattr("harbor.core.stale.L2Generator.generate", lambda self, module: "# Module: harbor/core\n")
    summary = check_module_derived_views_stale("harbor/core")
    assert summary.l2_readme.status == "up_to_date"
    assert summary.l2_readme_export.status == "up_to_date"


def test_l2_export_warn_when_canonical_up_to_date_but_export_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_l2_export_config(tmp_path, enabled=True)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("SAME\nGenerated At: 2020-01-01T00:00:00Z\n", encoding="utf-8")
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "SAME\nGenerated At: 2026-01-01T00:00:00Z\n",
    )
    summary = check_module_derived_views_stale("harbor/core")
    assert summary.l2_readme.status == "up_to_date"
    assert summary.l2_readme_export.status == "stale"
    assert summary.l2_readme_export.reason == "module README export missing"


def test_l2_export_warn_when_canonical_up_to_date_but_export_mismatch(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_l2_export_config(tmp_path, enabled=True)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    exported = tmp_path / "harbor" / "core" / "README.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    exported.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("SAME\nGenerated At: 2020-01-01T00:00:00Z\n", encoding="utf-8")
    exported.write_text("DIFF\nGenerated At: 2026-01-01T00:00:00Z\n", encoding="utf-8")
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "SAME\nGenerated At: 2026-01-01T00:00:00Z\n",
    )
    summary = check_module_derived_views_stale("harbor/core")
    assert summary.l2_readme.status == "up_to_date"
    assert summary.l2_readme_export.status == "stale"
    assert summary.l2_readme_export.reason == "module README export out of sync"


def test_l2_export_disabled_is_explicit_and_not_warn_counter(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_l2_export_config(tmp_path, enabled=False)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("SAME\nGenerated At: 2020-01-01T00:00:00Z\n", encoding="utf-8")
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "SAME\nGenerated At: 2026-01-01T00:00:00Z\n",
    )
    summary = check_module_derived_views_stale("harbor/core")
    payload = stale_report_to_dict([summary], scope="module:harbor/core")
    assert summary.l2_readme_export.status == "disabled"
    assert payload["summary"]["disabled_views"] == 1
    assert payload["summary"]["stale_views"] == 1  # module capsule stale only


def test_l2_export_skips_compare_when_canonical_unavailable(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_l2_export_config(tmp_path, enabled=True)
    exported = tmp_path / "harbor" / "core" / "README.md"
    exported.parent.mkdir(parents=True, exist_ok=True)
    exported.write_text("DIFF\n", encoding="utf-8")
    summary = check_module_derived_views_stale("harbor/core")
    assert summary.l2_readme.status == "stale"
    assert summary.l2_readme_export.status == "unknown"
    assert summary.l2_readme_export.reason == "canonical L2 README unavailable"


def test_stale_json_contains_l2_readme_export_view_name(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_index(tmp_path)
    _write_l2_export_config(tmp_path, enabled=False)
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("SAME\nGenerated At: 2020-01-01T00:00:00Z\n", encoding="utf-8")
    monkeypatch.setattr(
        "harbor.core.stale.L2Generator.generate",
        lambda self, module: "SAME\nGenerated At: 2026-01-01T00:00:00Z\n",
    )
    payload = stale_report_to_dict([check_module_derived_views_stale("harbor/core")], scope="module:harbor/core")
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    loaded = json.loads(dumped)
    view_names = [item["view"] for item in loaded["modules"][0]["views"]]
    assert "l2_readme" in view_names
    assert "l2_readme_export" in view_names
    assert "specs/diary" not in dumped
    assert ".harbor/diary" not in dumped


def test_check_module_derived_views_stale_is_up_to_date_without_runtime_index_cache(tmp_path: Path, monkeypatch):
    _write_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    gen = L2Generator()
    markdown = gen.generate("harbor/core")
    gen.write("harbor/core", markdown, force=True)
    write_module_capsule(collect_module_context("harbor/core"))

    summary = check_module_derived_views_stale("harbor/core")

    assert summary.l2_readme.status == "up_to_date"
    assert summary.module_capsule.status == "up_to_date"
    assert not (tmp_path / ".harbor" / "cache" / "l3_index.json").exists()
    assert not (tmp_path / ".harbor" / "cache" / "harbor.db").exists()


def test_check_module_derived_views_stale_uses_ts_aware_transient_index_without_runtime_cache(
    tmp_path: Path, monkeypatch
):
    _write_typescript_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    gen = L2Generator()
    markdown = gen.generate("src")
    gen.write("src", markdown, force=True)
    write_module_capsule(collect_module_context("src"))

    summary = check_module_derived_views_stale("src")

    assert summary.l2_readme.status == "up_to_date"
    assert summary.module_capsule.status == "up_to_date"
    assert not (tmp_path / ".harbor" / "cache" / "l3_index.json").exists()
    assert not (tmp_path / ".harbor" / "cache" / "harbor.db").exists()


def test_l2_generate_is_stable_when_duplicate_short_names_arrive_in_different_index_order(
    tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    idx = tmp_path / ".harbor" / "cache" / "l3_index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("harbor.core.l2.DDTScanner.scan_tests", lambda self: [])
    monkeypatch.setattr(
        "harbor.core.l2.DDTValidator.validate",
        lambda self, bindings: SimpleNamespace(valid=[], violations=[]),
    )

    entries = {
        "harbor/core/a.py": {
            "items": [
                {
                    "id": "harbor.core.a.Alpha.to_dict",
                    "qualified_name": "harbor.core.a.Alpha.to_dict",
                    "name": "to_dict",
                    "scope": "public",
                    "strictness": "strict",
                    "lineno": 1,
                }
            ]
        },
        "harbor/core/b.py": {
            "items": [
                {
                    "id": "harbor.core.b.Beta.to_dict",
                    "qualified_name": "harbor.core.b.Beta.to_dict",
                    "name": "to_dict",
                    "scope": "public",
                    "strictness": "strict",
                    "lineno": 1,
                }
            ]
        },
    }

    idx.write_text(json.dumps({"files": entries}, ensure_ascii=False), encoding="utf-8")
    first = L2Generator().generate("harbor/core")

    reversed_entries = {
        "harbor/core/b.py": entries["harbor/core/b.py"],
        "harbor/core/a.py": entries["harbor/core/a.py"],
    }
    idx.write_text(json.dumps({"files": reversed_entries}, ensure_ascii=False), encoding="utf-8")
    second = L2Generator().generate("harbor/core")

    assert first == second
    assert first.index("harbor.core.a.Alpha.to_dict") < first.index("harbor.core.b.Beta.to_dict")
