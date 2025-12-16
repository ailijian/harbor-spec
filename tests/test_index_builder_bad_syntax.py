from pathlib import Path

from harbor.core.index import IndexBuilder


def test_index_builder_skips_bad_syntax(tmp_path: Path):
    bad = tmp_path / "bad_syntax.py"
    bad.write_text('s = """\nunclosed string', encoding="utf-8")
    ok = tmp_path / "ok.py"
    ok.write_text(
        'def foo():\n    """doc"""\n    return 1\n',
        encoding="utf-8",
    )
    cache_dir = tmp_path / ".harbor" / "cache"
    builder = IndexBuilder(code_roots=[str(tmp_path)], cache_dir=cache_dir)
    rep = builder.build(incremental=False)
    assert rep.scanned_files == 2
    assert rep.skipped_files >= 1
    assert rep.updated_files >= 1
    assert Path(rep.cache_path).exists()
