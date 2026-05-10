from pathlib import Path
import textwrap
import json
from types import SimpleNamespace

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.test_utils import harbor_ddt_target


def write_module(tmp_path: Path, content: str, name: str = "mod.py") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


@harbor_ddt_target(func="harbor.core.sync.SyncEngine.check_status", l3_version=1, strategy="strict")
def test_sync_engine_drift_detection(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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


def test_sync_engine_contract_gap_for_required_target_without_docstring(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache_dir = tmp_path / ".harbor" / "cache"
    code_root = tmp_path / "harbor" / "core"
    code_root.mkdir(parents=True, exist_ok=True)

    src1 = textwrap.dedent(
        """
        def write_report(x):
            return x
        """
    ).strip()
    p = write_module(code_root, src1, name="gap_case.py")

    builder = IndexBuilder(code_roots=[str(tmp_path / "harbor")], cache_dir=cache_dir)
    builder.build(incremental=True)

    src2 = textwrap.dedent(
        """
        def write_report(x):
            y = x + 1
            return y
        """
    ).strip()
    write_module(code_root, src2, name="gap_case.py")

    eng = SyncEngine()
    eng.code_roots = [str(tmp_path / "harbor")]
    rep = eng.check_status()
    assert rep.counts["contract_gap"] >= 1
    assert rep.counts["drift"] == 0


def test_sync_engine_skipped_no_contract_for_internal_helper_without_docstring(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code_root = tmp_path / "src"
    code_root.mkdir(parents=True, exist_ok=True)

    src = textwrap.dedent(
        """
        def _helper(x):
            return x + 1
        """
    ).strip()
    write_module(code_root, src, name="helpers.py")

    eng = SyncEngine()
    eng.code_roots = [str(code_root)]
    rep = eng.check_status()

    assert rep.counts["skipped_no_contract"] >= 1
    assert any(entry.id.endswith("._helper") for entry in rep.skipped_no_contract)


def test_sync_engine_contract_parse_error_when_contract_presence_is_malformed(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code_root = tmp_path / "src"
    code_root.mkdir(parents=True, exist_ok=True)

    src = textwrap.dedent(
        """
        def foo(x):
            return x
        """
    ).strip()
    write_module(code_root, src)

    monkeypatch.setattr(
        "harbor.core.sync.evaluate_contract_presence",
        lambda fc, fp: SimpleNamespace(presence="malformed", required=True, reason="Malformed contract source"),
    )

    eng = SyncEngine()
    eng.code_roots = [str(code_root)]
    rep = eng.check_status()

    assert rep.counts["contract_parse_error"] >= 1
    assert any(entry.id.endswith(".foo") for entry in rep.contract_parse_error)
