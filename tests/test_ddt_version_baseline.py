import json
import textwrap
from pathlib import Path

from harbor.core.ddt import DDTBinding, DDTValidator
from harbor.core.index import IndexBuilder


def _build_strict_target(tmp_path: Path) -> tuple[Path, str, str]:
    cache_dir = tmp_path / ".harbor" / "cache"
    src_root = tmp_path / "src"
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "mod.py").write_text(
        textwrap.dedent(
            """
            def target(a, b):
                \"\"\"Doc.

                @harbor.scope: public
                @harbor.l3_strictness: strict

                Args:
                  a (int): A.
                  b (int): B.

                Returns:
                  int: Sum.
                \"\"\"
                return a + b
            """
        ).strip(),
        encoding="utf-8",
    )
    builder = IndexBuilder(code_roots=[str(src_root)], cache_dir=cache_dir)
    builder.build(incremental=True)
    payload = json.loads((cache_dir / "l3_index.json").read_text(encoding="utf-8"))
    first_file = next(iter(payload.get("files", {}).values()))
    first_item = (first_file.get("items") or [])[0]
    func_id = str(first_item.get("id") or "")
    binding_path = str((tmp_path / "tests" / "test_ddt_target.py").as_posix())
    return cache_dir, func_id, binding_path


def test_strict_binding_reports_baseline_missing_advisory(tmp_path: Path):
    cache_dir, func_id, binding_path = _build_strict_target(tmp_path)
    validator = DDTValidator(index_path=cache_dir / "l3_index.json", map_path=cache_dir / "l3_hash_map.json")
    rep = validator.validate(
        [
            DDTBinding(
                func_id=func_id,
                l3_version=1,
                strategy="strict",
                file_path=binding_path,
                test_name="test_target",
            )
        ]
    )
    assert rep.counts["violations"] == 0
    assert rep.counts["valid"] == 1
    assert rep.counts["advisory"] == 1
    assert rep.advisory[0].category == "ddt_version_baseline_missing"


def test_strict_binding_with_latest_still_fails(tmp_path: Path):
    cache_dir, func_id, binding_path = _build_strict_target(tmp_path)
    validator = DDTValidator(index_path=cache_dir / "l3_index.json", map_path=cache_dir / "l3_hash_map.json")
    rep = validator.validate(
        [
            DDTBinding(
                func_id=func_id,
                l3_version=1,
                strategy="latest",
                file_path=binding_path,
                test_name="test_target_latest",
            )
        ]
    )
    assert rep.counts["violations"] == 1
    assert rep.violations[0][0] == "strict_forbid_latest"


def test_strict_binding_missing_l3_version_still_fails(tmp_path: Path):
    cache_dir, func_id, binding_path = _build_strict_target(tmp_path)
    validator = DDTValidator(index_path=cache_dir / "l3_index.json", map_path=cache_dir / "l3_hash_map.json")
    rep = validator.validate(
        [
            DDTBinding(
                func_id=func_id,
                l3_version=None,
                strategy="strict",
                file_path=binding_path,
                test_name="test_target_missing_version",
            )
        ]
    )
    assert rep.counts["violations"] == 1
    assert rep.violations[0][0] == "missing_binding_info"


def test_strict_binding_with_available_baseline_has_no_missing_baseline_advisory(tmp_path: Path):
    cache_dir, func_id, binding_path = _build_strict_target(tmp_path)
    validator_seed = DDTValidator(index_path=cache_dir / "l3_index.json", map_path=cache_dir / "l3_hash_map.json")
    _, contract_hash = validator_seed._func_meta[func_id]
    (cache_dir / "l3_hash_map.json").write_text(
        json.dumps({func_id: {"l3_version": 1, "contract_hash": contract_hash}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    validator = DDTValidator(index_path=cache_dir / "l3_index.json", map_path=cache_dir / "l3_hash_map.json")
    rep = validator.validate(
        [
            DDTBinding(
                func_id=func_id,
                l3_version=1,
                strategy="strict",
                file_path=binding_path,
                test_name="test_target_with_baseline",
            )
        ]
    )
    assert rep.counts["violations"] == 0
    assert rep.counts["valid"] == 1
    assert rep.counts["advisory"] == 0
