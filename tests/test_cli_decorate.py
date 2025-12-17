import sys
import io
from pathlib import Path
import textwrap
from contextlib import redirect_stdout

from harbor.cli.main import main


def test_cli_dry_run_preview_counts(tmp_path: Path):
    src = textwrap.dedent(
        """
        def foo():
            \"\"\"Doc.
            \"\"\"
            return 1
        """
    ).strip() + "\n"
    p = tmp_path / "e.py"
    p.write_text(src, encoding="utf-8")
    buf = io.StringIO()
    old_argv = sys.argv[:]
    try:
        sys.argv = ["harbor", "decorate", str(p), "--dry-run", "--strategy", "safe"]
        with redirect_stdout(buf):
            main()
    finally:
        sys.argv = old_argv
    out = buf.getvalue()
    assert "Found 1 candidates. 1 have docstrings, 0 do not." in out
