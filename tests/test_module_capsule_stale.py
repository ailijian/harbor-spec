import json
from pathlib import Path

from harbor.core.module_capsule import (
    check_module_capsule_stale,
    collect_module_context,
    compute_module_fingerprint,
    read_capsule_fingerprint,
    write_module_capsule,
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


def test_compute_module_fingerprint_is_stable_and_normalized():
    ctx1 = {
        "module": r"harbor\core",
        "key_files": [r"harbor\core\sync.py", "harbor/core/l2.py"],
        "contracts": [
            {"symbol": "SyncEngine.check_status", "file": r"harbor\core\sync.py", "scope": "public", "strictness": "standard"},
            {"symbol": "L2Generator.generate", "file": "harbor/core/l2.py", "scope": "public", "strictness": "standard"},
        ],
        "tests": [r"tests\test_sync_engine.py", "tests/test_l2.py"],
        "strictness": "standard",
    }
    ctx2 = {
        "module": "harbor/core",
        "key_files": ["harbor/core/l2.py", "harbor/core/sync.py"],
        "contracts": [
            {"symbol": "L2Generator.generate", "file": "harbor/core/l2.py", "scope": "public", "strictness": "standard"},
            {"symbol": "SyncEngine.check_status", "file": "harbor/core/sync.py", "scope": "public", "strictness": "standard"},
        ],
        "tests": ["tests/test_l2.py", "tests/test_sync_engine.py"],
        "strictness": "standard",
    }
    fp1 = compute_module_fingerprint(ctx1)
    fp2 = compute_module_fingerprint(ctx2)
    assert fp1 == fp2
    assert len(fp1) == 64


def test_write_module_card_contains_frontmatter_fingerprint(tmp_path: Path):
    ctx = {
        "module": "harbor/core",
        "key_files": ["harbor/core/sync.py"],
        "contracts": [
            {
                "symbol": "SyncEngine.check_status",
                "file": "harbor/core/sync.py",
                "scope": "public",
                "strictness": "standard",
            }
        ],
        "tests": ["tests/test_sync_engine.py"],
        "strictness": "standard",
    }
    write_module_capsule(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    card = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md"
    text = card.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "fingerprint:" in text
    assert read_capsule_fingerprint(card) == compute_module_fingerprint(ctx)


def test_stale_when_module_card_missing(tmp_path: Path):
    ctx = {
        "module": "harbor/core",
        "key_files": ["harbor/core/sync.py"],
        "contracts": [{"symbol": "SyncEngine.check_status", "file": "harbor/core/sync.py", "scope": "public", "strictness": "standard"}],
        "tests": [],
        "strictness": "standard",
    }
    result = check_module_capsule_stale(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    assert result["status"] == "stale"
    assert result["reason"] == "module-card.md not found"


def test_stale_when_fingerprint_missing(tmp_path: Path):
    out = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core"
    out.mkdir(parents=True, exist_ok=True)
    (out / "module-card.md").write_text("# Module Card: harbor/core\n", encoding="utf-8")
    ctx = {
        "module": "harbor/core",
        "key_files": ["harbor/core/sync.py"],
        "contracts": [{"symbol": "SyncEngine.check_status", "file": "harbor/core/sync.py", "scope": "public", "strictness": "standard"}],
        "tests": [],
        "strictness": "standard",
    }
    result = check_module_capsule_stale(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    assert result["status"] == "stale"
    assert result["reason"] == "fingerprint missing"


def test_up_to_date_when_fingerprint_matches(tmp_path: Path, monkeypatch):
    idx = _write_index(tmp_path)
    monkeypatch.chdir(tmp_path)
    ctx = collect_module_context("harbor/core", index_path=idx)
    write_module_capsule(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    result = check_module_capsule_stale(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    assert result["status"] == "up_to_date"
    assert result["reason"] == "up to date"


def test_stale_when_fingerprint_mismatch(tmp_path: Path, monkeypatch):
    idx = _write_index(tmp_path)
    monkeypatch.chdir(tmp_path)
    ctx = collect_module_context("harbor/core", index_path=idx)
    write_module_capsule(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    card = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md"
    text = card.read_text(encoding="utf-8").replace(read_capsule_fingerprint(card), "deadbeef")
    card.write_text(text, encoding="utf-8")
    result = check_module_capsule_stale(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    assert result["status"] == "stale"
    assert result["reason"] == "fingerprint mismatch"


def test_unknown_module_is_friendly_stale(tmp_path: Path):
    ctx = {
        "module": "harbor/unknown",
        "key_files": [],
        "contracts": [],
        "tests": [],
        "strictness": "standard",
    }
    result = check_module_capsule_stale(ctx, output_root=tmp_path / ".harbor" / "views" / "modules")
    assert result["status"] == "stale"
    assert result["reason"] == "no indexed records found for module"


def test_legacy_exists_but_canonical_missing_is_stale(tmp_path: Path, monkeypatch):
    idx = _write_index(tmp_path)
    monkeypatch.chdir(tmp_path)
    ctx = collect_module_context("harbor/core", index_path=idx)
    legacy = tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "module-card.md").write_text("legacy\n", encoding="utf-8")
    result = check_module_capsule_stale(ctx)
    assert result["status"] == "stale"
    assert result["reason"] == "module-card.md not found"
