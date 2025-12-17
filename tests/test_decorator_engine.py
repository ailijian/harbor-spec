from pathlib import Path
import textwrap

from harbor.core.decorator import DecoratorEngine


def test_safe_adds_scope_without_breaking_indent(tmp_path: Path):
    src = textwrap.dedent(
        """
        def foo():
            \"\"\"Line 1

            Line 2
            \"\"\"
            return 1
        """
    ).strip() + "\n"
    p = tmp_path / "a.py"
    p.write_text(src, encoding="utf-8")
    eng = DecoratorEngine()
    plans = eng.preview(p, strategy="safe")
    assert plans and plans[0].will_write
    rep = eng.apply(plans, dry_run=False, strategy="safe")
    assert p in rep.changed_files
    new_src = p.read_text(encoding="utf-8")
    lines = new_src.splitlines()
    idx_close = None
    for i, ln in enumerate(lines):
        if ln.strip() == '"""':
            idx_close = i
            break
    assert idx_close is not None
    tag_line = lines[idx_close - 1]
    close_line = lines[idx_close]
    assert tag_line.strip() == "@harbor.scope: public"
    assert len(tag_line) - len(tag_line.lstrip(" ")) == len(close_line) - len(close_line.lstrip(" "))


def test_safe_does_not_duplicate_tag(tmp_path: Path):
    src = textwrap.dedent(
        """
        def foo():
            \"\"\"Doc.

            @harbor.scope: public
            \"\"\"
            return 1
        """
    ).strip() + "\n"
    p = tmp_path / "b.py"
    p.write_text(src, encoding="utf-8")
    eng = DecoratorEngine()
    plans = eng.preview(p, strategy="safe")
    rep = eng.apply(plans, dry_run=False, strategy="aggressive")
    text = p.read_text(encoding="utf-8")
    assert text.count("@harbor.scope: public") == 1


def test_aggressive_inserts_todo_docstring(tmp_path: Path):
    src = textwrap.dedent(
        """
        def foo(a, b):
            return a + b
        """
    ).strip() + "\n"
    p = tmp_path / "c.py"
    p.write_text(src, encoding="utf-8")
    eng = DecoratorEngine()
    plans = eng.preview(p, strategy="aggressive")
    rep = eng.apply(plans, dry_run=False, strategy="aggressive")
    text = p.read_text(encoding="utf-8")
    assert '"""TODO: Add summary.' in text
    assert "@harbor.scope: public" in text


def test_filters_out_internal_and_testlike_names(tmp_path: Path):
    src = textwrap.dedent(
        """
        def _internal():
            return 1

        def test_foo():
            return 2

        def setup_bar():
            return 3

        def teardown_baz():
            return 4
        """
    ).strip() + "\n"
    p = tmp_path / "d.py"
    p.write_text(src, encoding="utf-8")
    eng = DecoratorEngine()
    cands = eng.scan(str(p), strategy="aggressive")
    skipped = [c for c in cands if c.action == "Skip"]
    assert len(skipped) == 4
