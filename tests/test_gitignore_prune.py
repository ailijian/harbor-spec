import os
from pathlib import Path
import textwrap
import json

from harbor.core.index import IndexBuilder


def test_gitignore_prunes_node_modules(tmp_path: Path):
    root = tmp_path
    cache_dir = root / ".harbor" / "cache"
    app_dir = root / "app"
    nm_dir = root / "node_modules"
    app_dir.mkdir(parents=True, exist_ok=True)
    nm_dir.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (app_dir / "main.py").write_text(
        textwrap.dedent(
            """
            def hello():
                \"\"\"Say hello.

                Args:
                  None

                Returns:
                  None
                \"\"\"
                return None
            """
        ).strip(),
        encoding="utf-8",
    )
    (nm_dir / "fake.py").write_text("x=1\n", encoding="utf-8")
    cwd_old = Path.cwd()
    try:
        os.chdir(root)
        builder = IndexBuilder(code_roots=[str(root)], cache_dir=cache_dir)
        _ = builder.build(incremental=False)
        idx = json.loads((cache_dir / "l3_index.json").read_text(encoding="utf-8"))
        files = list(idx.get("files", {}).keys())
        assert any("app/main.py" in f.replace("\\\\", "/") for f in files)
        assert not any("node_modules/fake.py" in f.replace("\\\\", "/") for f in files)
    finally:
        os.chdir(cwd_old)
