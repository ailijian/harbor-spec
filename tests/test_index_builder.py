from pathlib import Path
import textwrap
import json

from harbor.core.index import IndexBuilder


def write_module(tmp_path: Path, content: str, name: str = "mod.py") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def read_index(cache_dir: Path) -> dict:
    return json.loads((cache_dir / "l3_index.json").read_text(encoding="utf-8"))


def test_index_build_incremental_and_docstring_stability(tmp_path: Path):
    cache_dir = tmp_path / ".harbor" / "cache"
    code_root = tmp_path / "src"
    code_root.mkdir(parents=True, exist_ok=True)
    src1 = textwrap.dedent(
        """
        def foo(a, b):
            \"\"\"Calc.

            Args:
              a (int): A.
              b (int): B.

            Returns:
              int: Sum.
            \"\"\"
            x = a + b
            return x
        """
    ).strip()
    p = write_module(code_root, src1)
    builder = IndexBuilder(code_roots=[str(code_root)], cache_dir=cache_dir)
    r1 = builder.build(incremental=True)
    assert r1.updated_files >= 1
    idx1 = read_index(cache_dir)
    fp = str(p.as_posix())
    items = idx1["files"][fp]["items"]
    assert items and items[0]["name"] == "foo"
    body1 = items[0]["body_hash"]
    raw1 = items[0]["docstring_raw_hash"]

    r2 = builder.build(incremental=True)
    assert r2.skipped_files >= 1

    src2 = textwrap.dedent(
        """
        def foo(a, b):
            \"\"\"Calc changed doc.

            Args:
              a (int): A.
              b (int): B.

            Returns:
              int: Sum.
            \"\"\"
            x = a + b
            return x
        """
    ).strip()
    write_module(code_root, src2)
    r3 = builder.build(incremental=True)
    idx3 = read_index(cache_dir)
    items3 = idx3["files"][fp]["items"]
    body2 = items3[0]["body_hash"]
    raw2 = items3[0]["docstring_raw_hash"]
    assert body2 == body1
    assert raw2 != raw1

    src3 = textwrap.dedent(
        """
        def foo(a, b):
            \"\"\"Calc changed doc.

            Args:
              a (int): A.
              b (int): B.

            Returns:
              int: Sum.
            \"\"\"
            x = a * b
            return x
        """
    ).strip()
    write_module(code_root, src3)
    r4 = builder.build(incremental=True)
    idx4 = read_index(cache_dir)
    items4 = idx4["files"][fp]["items"]
    body3 = items4[0]["body_hash"]
    assert body3 != body2

