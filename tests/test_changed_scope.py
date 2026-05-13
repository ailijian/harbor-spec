import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from harbor.core.changed_scope import (
    collect_changed_modules_from_status,
    collect_changed_paths_from_status,
    detect_generator_integrity_changes,
)


def _status_report(*paths):
    entries = [SimpleNamespace(file_path=path) for path in paths]
    return SimpleNamespace(
        drift=[],
        modified=entries,
        contract_changed=[],
        contract_gap=[],
        skipped_no_contract=[],
        contract_parse_error=[],
        unsupported_syntax_advisory=[],
        untracked=[],
        missing=[],
    )


def test_collect_changed_paths_from_status_includes_all_relevant_buckets():
    report = SimpleNamespace(
        drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
        modified=[SimpleNamespace(file_path="tests/test_sample.py")],
        contract_changed=[SimpleNamespace(file_path="harbor/cli/main.py")],
        contract_gap=[SimpleNamespace(file_path="harbor/core/l2.py")],
        skipped_no_contract=[SimpleNamespace(file_path="harbor/core/helper.py")],
        contract_parse_error=[SimpleNamespace(file_path="harbor/core/bad.py")],
        unsupported_syntax_advisory=[SimpleNamespace(file_path="harbor/adapters/typescript/parser.ts")],
        untracked=[SimpleNamespace(file_path="harbor/core/new.py")],
        missing=[SimpleNamespace(file_path="harbor/core/old.py")],
    )

    changed_paths = collect_changed_paths_from_status(report)

    assert changed_paths == [
        "harbor/core/sync.py",
        "tests/test_sample.py",
        "harbor/cli/main.py",
        "harbor/core/l2.py",
        "harbor/core/helper.py",
        "harbor/core/bad.py",
        "harbor/adapters/typescript/parser.ts",
        "harbor/core/new.py",
        "harbor/core/old.py",
    ]


def test_collect_changed_modules_from_status_normalizes_repo_absolute_paths_and_adds_indexed_parents(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report = _status_report(
        str((tmp_path / "harbor" / "core" / "sample.py").resolve()),
        str((tmp_path / "tests" / "test_sample.py").resolve()),
        "C:/Users/GM/AppData/Local/Temp/outside.py",
    )

    modules = collect_changed_modules_from_status(
        report,
        repo_root=tmp_path,
        indexed_modules=["harbor", "harbor/core", "tests"],
    )

    assert modules == ["harbor", "harbor/core", "tests"]


def test_detect_generator_integrity_changes_matches_only_guarded_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    changed_paths = [
        str((tmp_path / "harbor" / "core" / "l2.py").resolve()),
        str((tmp_path / "harbor" / "core" / "context_integrity.py").resolve()),
        "harbor/core/module_capsule.py",
        "harbor/core/sync.py",
    ]

    advisory_paths = detect_generator_integrity_changes(changed_paths, repo_root=Path(tmp_path))

    assert advisory_paths == [
        "harbor/core/context_integrity.py",
        "harbor/core/l2.py",
        "harbor/core/module_capsule.py",
    ]


def test_collect_changed_modules_from_status_uses_full_repo_root_for_duplicate_repo_name_paths(tmp_path, monkeypatch):
    repo_root = tmp_path / "harbor-spec" / "harbor-spec"
    (repo_root / "harbor" / "core").mkdir(parents=True, exist_ok=True)
    (repo_root / "tests").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(repo_root)
    report = _status_report(
        str((repo_root / "harbor" / "core" / "sync.py").resolve()),
        str((repo_root / "tests" / "test_sync_engine.py").resolve()),
    )

    modules = collect_changed_modules_from_status(
        report,
        repo_root=repo_root,
        indexed_modules=["harbor", "harbor/core", "tests"],
    )

    assert modules == ["harbor", "harbor/core", "tests"]
    assert all(not module.startswith("harbor-spec/") for module in modules)


@pytest.mark.skipif(os.name != "nt", reason="Windows path normalization scenario")
def test_collect_changed_modules_from_status_normalizes_github_actions_windows_paths():
    report = _status_report(
        r"D:\a\harbor-spec\harbor-spec\harbor\core\sync.py",
        r"D:\a\harbor-spec\harbor-spec\tests\test_sync_engine.py",
    )

    modules = collect_changed_modules_from_status(
        report,
        repo_root=Path(r"D:\a\harbor-spec\harbor-spec"),
        indexed_modules=["harbor", "harbor/core", "tests"],
    )

    assert modules == ["harbor", "harbor/core", "tests"]
    assert "harbor-spec/harbor" not in modules
    assert "harbor-spec/tests" not in modules
