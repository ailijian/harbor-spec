from pathlib import Path
import textwrap

from harbor.core.index import IndexBuilder


def test_iter_build_emits_progress_and_counts(tmp_path: Path):
    cache_dir = tmp_path / ".harbor" / "cache"
    code_root = tmp_path / "pkg"
    code_root.mkdir(parents=True, exist_ok=True)
    (code_root / "a.py").write_text(
        textwrap.dedent(
            '''
            def foo():
                """doc"""
                return 1
            '''
        ).strip(),
        encoding="utf-8",
    )
    (code_root / "b.py").write_text(
        textwrap.dedent(
            '''
            def bar():
                """doc"""
                return 2
            '''
        ).strip(),
        encoding="utf-8",
    )
    builder = IndexBuilder(code_roots=[str(code_root)], cache_dir=cache_dir)
    parsed = 0
    skipped = 0
    scanning = 0
    for ev in builder.iter_build(incremental=True):
        assert ev.total == 2
        assert ev.path.endswith(".py")
        if ev.status == "parsed":
            parsed += 1
            assert ev.items_count >= 1
        elif ev.status == "skipped":
            skipped += 1
        elif ev.status == "scanning":
            scanning += 1
    assert parsed == 2
    assert skipped == 0
    assert scanning >= 2  # 每个解析文件至少一次扫描事件

    # 再次运行（增量），应当全部跳过
    parsed = 0
    skipped = 0
    for ev in builder.iter_build(incremental=True):
        if ev.status == "parsed":
            parsed += 1
        elif ev.status == "skipped":
            skipped += 1
    assert parsed == 0
    assert skipped == 2
