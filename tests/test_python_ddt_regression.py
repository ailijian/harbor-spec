import json
from pathlib import Path

from harbor.core.ddt import DDTBinding, DDTValidator


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_python_ddt_strict_forbids_latest_and_strict_version_stays_valid(tmp_path: Path):
    cache = tmp_path / ".harbor" / "cache"
    _write(
        cache / "l3_index.json",
        {
            "meta": {"schema_version": "1.0.2"},
            "files": {
                "src/mod.py": {
                    "mtime": 0.0,
                    "file_hash": "",
                    "items": [
                        {"id": "src.mod.target", "strictness": "strict", "contract_hash": "h1"},
                    ],
                }
            },
        },
    )
    _write(
        cache / "l3_hash_map.json",
        {
            "src.mod.target": {
                "l3_version": 1,
                "contract_hash": "h1",
            }
        },
    )
    validator = DDTValidator(index_path=cache / "l3_index.json", map_path=cache / "l3_hash_map.json")
    report = validator.validate(
        [
            DDTBinding(
                func_id="src.mod.target",
                l3_version=1,
                strategy="strict",
                file_path="tests/test_mod.py",
                test_name="test_target_strict",
            ),
            DDTBinding(
                func_id="src.mod.target",
                l3_version=None,
                strategy="latest",
                file_path="tests/test_mod.py",
                test_name="test_target_latest",
            ),
        ]
    )
    assert report.counts["valid"] == 1
    assert report.counts["violations"] == 1
    assert report.violations[0][0] == "strict_forbid_latest"


def test_typescript_binding_is_advisory_and_does_not_change_python_rules(tmp_path: Path):
    cache = tmp_path / ".harbor" / "cache"
    _write(
        cache / "l3_index.json",
        {
            "meta": {"schema_version": "1.0.2"},
            "files": {
                "src/mod.py": {
                    "mtime": 0.0,
                    "file_hash": "",
                    "items": [
                        {"id": "src.mod.target", "strictness": "strict", "contract_hash": "h1"},
                    ],
                }
            },
        },
    )
    _write(cache / "l3_hash_map.json", {"src.mod.target": {"l3_version": 1, "contract_hash": "h1"}})
    validator = DDTValidator(index_path=cache / "l3_index.json", map_path=cache / "l3_hash_map.json")
    report = validator.validate(
        [
            DDTBinding(
                func_id="typescript:src/mod.ts:function:target",
                l3_version=1,
                strategy="strict",
                file_path="tests/test_ts.py",
                test_name="test_ts_target",
            ),
            DDTBinding(
                func_id="src.mod.target",
                l3_version=1,
                strategy="strict",
                file_path="tests/test_mod.py",
                test_name="test_py_target",
            ),
        ]
    )
    assert report.counts["valid"] == 1
    assert report.counts["violations"] == 0
    assert report.counts["advisory"] == 1
    assert report.advisory[0].category == "ddt_not_supported"
