import json
import re
from pathlib import Path

from harbor.core.generated_verify import (
    ARTIFACT_STATUS_FAIL,
    ARTIFACT_STATUS_UP_TO_DATE,
    build_generated_verification_report,
)
from harbor.core.l2 import L2Generator
from harbor.core.module_capsule import collect_module_context, write_module_capsule
from harbor.core.project_structure import collect_project_structure_context, write_project_structure


def _write_sample_repo(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "sample-harbor"
version = "0.1.0"
description = "sample"
""".strip()
        + "\n",
        encoding="utf-8",
    )
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


def _generate_views(tmp_path: Path) -> None:
    gen = L2Generator()
    gen.write("harbor/core", gen.generate("harbor/core"), force=True)
    write_module_capsule(collect_module_context("harbor/core"))
    write_project_structure(collect_project_structure_context(tmp_path), tmp_path)


def test_generated_verify_passes_when_views_match(tmp_path: Path, monkeypatch):
    _write_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _generate_views(tmp_path)

    report = build_generated_verification_report(scope="all", modules=["harbor/core"])

    assert report.status == "pass"
    assert report.summary["failures"] == 0
    assert report.summary["missing"] == 0
    assert report.summary["blocked"] == 0
    assert report.summary["unknown"] == 0
    statuses = [item.status for item in report.project.artifacts + report.modules[0].artifacts]
    assert all(status == ARTIFACT_STATUS_UP_TO_DATE for status in statuses)


def test_generated_verify_ignores_generated_at_only_changes(tmp_path: Path, monkeypatch):
    _write_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _generate_views(tmp_path)

    readme = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r'generated_at:\s*"[^"]+"', 'generated_at: "2099-01-01T00:00:00Z"', text, count=1)
    readme.write_text(text, encoding="utf-8")

    report = build_generated_verification_report(scope="all", modules=["harbor/core"])
    artifact = next(item for item in report.modules[0].artifacts if item.artifact == "canonical_l2_readme")

    assert artifact.status == ARTIFACT_STATUS_UP_TO_DATE
    assert report.status == "pass"


def test_generated_verify_detects_l2_meta_hash_mismatch(tmp_path: Path, monkeypatch):
    _write_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _generate_views(tmp_path)

    meta_path = tmp_path / ".harbor" / "views" / "l2" / "_meta.json"
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    payload["harbor/core"] = "deadbeef"
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = build_generated_verification_report(scope="all", modules=["harbor/core"])
    artifact = next(item for item in report.project.artifacts if item.artifact == "l2_meta")

    assert artifact.status == ARTIFACT_STATUS_FAIL
    assert artifact.reason == "l2_meta_hash_mismatch"
    assert report.status == "fail"


def test_generated_verify_detects_module_capsule_fingerprint_mismatch(tmp_path: Path, monkeypatch):
    _write_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _generate_views(tmp_path)

    card = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md"
    text = card.read_text(encoding="utf-8").replace("view_fingerprint:", "view_fingerprint: \"deadbeef\" #")
    card.write_text(text, encoding="utf-8")

    report = build_generated_verification_report(scope="all", modules=["harbor/core"])
    artifact = next(item for item in report.modules[0].artifacts if item.artifact == "module_card")

    assert artifact.status == ARTIFACT_STATUS_FAIL
    assert artifact.reason == "module_capsule_fingerprint_mismatch"
    assert report.status == "fail"


def test_generated_verify_ignores_cross_platform_source_line_endings(tmp_path: Path, monkeypatch):
    _write_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _generate_views(tmp_path)

    sample = tmp_path / "harbor" / "core" / "sample.py"
    raw = sample.read_bytes()
    if b"\r\n" in raw:
        sample.write_bytes(raw.replace(b"\r\n", b"\n"))
    else:
        sample.write_bytes(raw.replace(b"\n", b"\r\n"))

    report = build_generated_verification_report(scope="all", modules=["harbor/core"])

    assert report.status == "pass"
    assert report.summary["failures"] == 0


def test_generated_verify_project_structure_passes_without_runtime_cache(tmp_path: Path, monkeypatch):
    _write_sample_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _generate_views(tmp_path)

    cache_dir = tmp_path / ".harbor" / "cache"
    backup_dir = tmp_path / ".harbor" / "cache_backup"
    if backup_dir.exists():
        raise AssertionError(f"unexpected backup cache path: {backup_dir}")
    renamed = False
    if cache_dir.exists():
        cache_dir.rename(backup_dir)
        renamed = True
    try:
        report = build_generated_verification_report(scope="all", modules=["harbor/core"])
    finally:
        if renamed:
            backup_dir.rename(cache_dir)

    project_structure = next(item for item in report.project.artifacts if item.artifact == "project_structure")
    assert project_structure.status == ARTIFACT_STATUS_UP_TO_DATE
    assert project_structure.reason is None
    assert report.status == "pass"
