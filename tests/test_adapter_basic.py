from pathlib import Path
import textwrap
import sys

from harbor.adapters.python.parser import PythonAdapter


def test_adapter_parses_itself():
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "harbor" / "adapters" / "python" / "parser.py"
    adapter = PythonAdapter()
    items = adapter.parse_file(str(target))
    hits = [x for x in items if x.qualified_name.endswith("PythonAdapter.parse_file")]
    assert hits, "PythonAdapter.parse_file not found"
    entry = hits[0]
    assert entry.docstring and len(entry.docstring) > 0
    assert entry.docstring_raw_hash and len(entry.docstring_raw_hash) > 0
    assert entry.contract_hash and len(entry.contract_hash) > 0
    assert entry.signature_hash and len(entry.signature_hash) > 0


def test_signature_hash_changes(tmp_path: Path):
    src1 = textwrap.dedent(
        """
        def foo(a, b):
            '''Doc.'''
            return a
        """
    ).strip()
    src2 = textwrap.dedent(
        """
        def foo(a, b, c=1, *args, **kwargs):
            '''Doc.'''
            return a
        """
    ).strip()
    p1 = tmp_path / "f1.py"
    p2 = tmp_path / "f2.py"
    p1.write_text(src1, encoding="utf-8")
    p2.write_text(src2, encoding="utf-8")
    adapter = PythonAdapter()
    h1 = [x.signature_hash for x in adapter.parse_file(str(p1)) if x.name == "foo"][0]
    h2 = [x.signature_hash for x in adapter.parse_file(str(p2)) if x.name == "foo"][0]
    assert h1 != h2

