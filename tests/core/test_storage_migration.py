import json
from pathlib import Path

from harbor.core.storage import HarborDB


def test_storage_migration_imports_json_to_sqlite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache_dir = Path(".harbor") / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    json_path = cache_dir / "l3_index.json"
    sample_file = "tests/fixtures_sqlite/sample.py"
    payload = {
        "files": {
            sample_file: {
                "mtime": 1730000000.0,
                "file_hash": "deadbeef",
                "items": [
                    {
                        "id": "tests.fixtures_sqlite.sample.func1",
                        "qualified_name": "tests.fixtures_sqlite.sample.func1",
                        "name": "func1",
                        "signature_hash": "s1",
                        "body_hash": "b1",
                        "contract_hash": "c1",
                        "docstring_raw_hash": "d1",
                        "scope": "public",
                        "strictness": "strict",
                        "lineno": 1,
                    }
                ],
            }
        }
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    db = HarborDB()
    ok = db.migrate_from_json(json_path)
    assert ok is True
    entries = db.get_file_entries(sample_file)
    assert entries and entries[0]["id"] == "tests.fixtures_sqlite.sample.func1"
    # 备份文件存在
    backups = list(cache_dir.glob("l3_index.json.bak-*"))
    assert backups, "expected backup file after migration"


def test_storage_migration_preserves_additive_typescript_meta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache_dir = Path(".harbor") / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    json_path = cache_dir / "l3_index.json"
    payload = {
        "files": {
            "src/service.ts": {
                "mtime": 1730000000.0,
                "file_hash": "",
                "items": [
                    {
                        "id": "typescript:src/service.ts:function:api",
                        "qualified_name": "api",
                        "name": "api",
                        "signature_hash": "s1",
                        "body_hash": "b1",
                        "contract_hash": "c1",
                        "lineno": 1,
                        "target_id": "typescript:src/service.ts:function:api",
                        "func_id": "typescript:src/service.ts:function:api",
                        "legacy_func_id": "typescript:src/service.ts:function:api",
                        "language": "typescript",
                        "symbol_kind": "function",
                        "file_path": "src/service.ts",
                        "end_lineno": 1,
                        "visibility": "public",
                        "contract_presence": "present",
                        "contract_required": True,
                        "contract_source_kinds": ["tsdoc"],
                        "contract_source_fingerprints": ["f1"],
                        "source_confidence_summary": "high",
                    }
                ],
            }
        }
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    db = HarborDB()
    assert db.migrate_from_json(json_path) is True

    entries = db.get_file_entries("src/service.ts")
    assert len(entries) == 1
    meta = entries[0]["meta"]
    assert meta["target_id"] == "typescript:src/service.ts:function:api"
    assert meta["language"] == "typescript"
    assert meta["symbol_kind"] == "function"
    assert meta["contract_presence"] == "present"
    assert meta["contract_source_kinds"] == ["tsdoc"]
