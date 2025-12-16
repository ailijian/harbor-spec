from pathlib import Path
import textwrap

from harbor.core.index import IndexBuilder
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.test_utils import harbor_ddt_target


def write_test_file(tmp_path: Path, content: str, name: str = "test_ddt_mod.py") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_ddt_validate_matrix(tmp_path: Path):
    cache_dir = tmp_path / ".harbor" / "cache"
    src_root = tmp_path / "src"
    tests_root = tmp_path / "tests"
    src_root.mkdir(parents=True, exist_ok=True)
    tests_root.mkdir(parents=True, exist_ok=True)

    code = textwrap.dedent(
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
    ).strip()
    (src_root / "mod.py").write_text(code, encoding="utf-8")

    test_code = textwrap.dedent(
        '''
        from harbor.test_utils import harbor_ddt_target
        @harbor_ddt_target(func="src.mod.target", l3_version=1, strategy="strict")
        def test_target():
            assert True
        '''
    ).strip()
    write_test_file(tests_root, test_code)

    builder = IndexBuilder(code_roots=[str(src_root)], cache_dir=cache_dir)
    builder.build(incremental=True)

    scanner = DDTScanner()
    scanner.test_roots = [str(tests_root)]
    bindings = scanner.scan_tests()
    validator = DDTValidator(index_path=cache_dir / "l3_index.json", map_path=cache_dir / "l3_hash_map.json")
    rep = validator.validate(bindings)
    assert rep.counts["valid"] >= 1

