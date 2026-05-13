import os
import hashlib
import json
from pathlib import Path

import pytest
import yaml

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
    legacy_payload = {module: hashlib.sha256(md.encode("utf-8")).hexdigest()}
    legacy_meta.write_text(json.dumps(legacy_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    gen = L2Generator()
    assert gen.write(module, md, force=False) is None
    assert not (tmp_path / ".harbor" / "views" / "l2" / "_meta.json").exists()

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
