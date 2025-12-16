from pathlib import Path
import textwrap
import json

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.test_utils import harbor_ddt_target


def write_module(tmp_path: Path, content: str, name: str = "mod.py") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


@harbor_ddt_target(func="harbor.core.sync.SyncEngine.check_status", l3_version=1, strategy="strict")
def test_sync_engine_drift_detection(tmp_path: Path):
    cache_dir = tmp_path / ".harbor" / "cache"
    code_root = tmp_path / "src"
    code_root.mkdir(parents=True, exist_ok=True)

    src1 = textwrap.dedent(
        """
        def foo(a, b):
            \"\"\"Doc.

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
    builder.build(incremental=True)

    src2 = textwrap.dedent(
        """
        def foo(a, b):
            \"\"\"Doc.

            Args:
              a (int): A.
              b (int): B.

            Returns:
              int: Sum.
            \"\"\"
            x = a + b
            pass
            return x
        """
    ).strip()
    write_module(code_root, src2)

    eng = SyncEngine()
    eng.code_roots = [str(code_root)]
    eng.cache_file = cache_dir / "l3_index.json"
    rep = eng.check_status()
    assert rep.counts["drift"] >= 1
    ids = [e.id for e in rep.drift]
    assert any(id_.endswith(".foo") for id_ in ids)
