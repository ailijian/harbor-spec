import json
from pathlib import Path

from harbor.core.module_capsule import (
    collect_module_context,
    read_capsule_fingerprint,
    write_module_capsule,
)
from harbor.core.module_skill import (
    check_capsule_ready_for_skill,
    generate_module_skill,
    normalize_skill_slug,
    skill_dir_for_module,
    write_module_skill,
)


def _write_index(tmp_path: Path) -> Path:
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
            },
            "harbor/core/l2.py": {
                "items": [
                    {
                        "id": "harbor.core.l2.L2Generator.generate",
                        "qualified_name": "L2Generator.generate",
                        "scope": "public",
                        "strictness": "standard",
                    }
                ]
            },
        }
    }
    idx.write_text(json.dumps(payload), encoding="utf-8")
    return idx


def test_normalize_skill_slug_rules_are_stable():
    assert normalize_skill_slug("harbor/core") == "harbor-core"
    assert normalize_skill_slug(r"harbor\core") == "harbor-core"
    assert normalize_skill_slug("app/services/review") == "app-services-review"
    assert normalize_skill_slug("Harbor///Core@@@") == "harbor-core"
    assert normalize_skill_slug("a__b--c") == "a-b-c"
    assert normalize_skill_slug("harbor/core") == normalize_skill_slug("harbor/core")


def test_generate_module_skill_contains_thin_template():
    text = generate_module_skill("harbor/core")
    assert text.startswith("---\nname: harbor-debug-harbor-core\n")
    assert "description: Use when debugging, reviewing, or refactoring the harbor/core module." in text
    assert "## Load order" in text
    assert "## Required checks" in text
    assert "harbor module stale harbor/core" in text
    assert ".harbor/views/modules/harbor/core/module-card.md" in text
    assert ".harbor/views/modules/harbor/core/review-checklist.md" in text
    assert ".harbor/views/modules/harbor/core/debug-playbook.md" in text
    assert "## Responsibility" not in text


def test_check_capsule_ready_unknown_module(tmp_path: Path):
    result = check_capsule_ready_for_skill("harbor/unknown", output_root=tmp_path / ".harbor" / "views" / "modules", context={})
    assert result["status"] == "unknown_module"
    assert result["reason"] == "no indexed records found for module"


def test_check_capsule_ready_missing_capsule(tmp_path: Path):
    context = {
        "module": "harbor/core",
        "key_files": ["harbor/core/sync.py"],
        "contracts": [{"symbol": "SyncEngine.check_status", "file": "harbor/core/sync.py", "scope": "public", "strictness": "standard"}],
        "tests": [],
        "strictness": "standard",
    }
    result = check_capsule_ready_for_skill("harbor/core", output_root=tmp_path / ".harbor" / "views" / "modules", context=context)
    assert result["status"] == "missing_capsule"


def test_check_capsule_ready_stale_capsule(tmp_path: Path, monkeypatch):
    idx = _write_index(tmp_path)
    monkeypatch.chdir(tmp_path)
    context = collect_module_context("harbor/core", index_path=idx)
    write_module_capsule(context, output_root=tmp_path / ".harbor" / "views" / "modules")
    module_card = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md"
    old_fp = read_capsule_fingerprint(module_card)
    assert old_fp
    module_card.write_text(module_card.read_text(encoding="utf-8").replace(old_fp, "deadbeef"), encoding="utf-8")
    result = check_capsule_ready_for_skill("harbor/core", output_root=tmp_path / ".harbor" / "views" / "modules", context=context)
    assert result["status"] == "stale_capsule"
    assert result["reason"] == "fingerprint mismatch"


def test_write_module_skill_only_writes_skill_file(tmp_path: Path):
    target = write_module_skill("harbor/core", root=tmp_path / ".agents" / "skills")
    assert target == tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md"
    assert target.exists()
    assert skill_dir_for_module("harbor/core", root=tmp_path / ".agents" / "skills").exists()
    assert not (tmp_path / "docs" / "harbor" / "modules").exists()


def test_check_capsule_ready_legacy_exists_but_canonical_missing(tmp_path: Path, monkeypatch):
    idx = _write_index(tmp_path)
    monkeypatch.chdir(tmp_path)
    context = collect_module_context("harbor/core", index_path=idx)
    legacy = tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "module-card.md").write_text("legacy\n", encoding="utf-8")
    (legacy / "review-checklist.md").write_text("legacy\n", encoding="utf-8")
    (legacy / "debug-playbook.md").write_text("legacy\n", encoding="utf-8")
    result = check_capsule_ready_for_skill("harbor/core", context=context)
    assert result["status"] == "missing_capsule"
