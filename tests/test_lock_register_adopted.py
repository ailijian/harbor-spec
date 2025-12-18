import yaml
from pathlib import Path
from harbor.cli.main import main
import sys


def test_lock_register_adopted(tmp_path: Path, monkeypatch):
    proj = tmp_path
    (proj / "pkg").mkdir(parents=True, exist_ok=True)
    (proj / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (proj / "pkg" / "a.py").write_text("def a():\n    pass\n", encoding="utf-8")
    (proj / "pkg" / "b.py").write_text("def b():\n    pass\n", encoding="utf-8")
    (proj / "pkg" / "c.py").write_text("def c():\n    pass\n", encoding="utf-8")
    (proj / "pkg" / "d.py").write_text("def d():\n    pass\n", encoding="utf-8")
    (proj / "pkg" / "e.py").write_text("def e():\n    pass\n", encoding="utf-8")
    monkeypatch.chdir(proj)
    sys.argv = ["harbor", "init", "--force"]
    main()
    sys.argv = ["harbor", "lock"]
    main()
    cfg = (proj / ".harbor" / "config.yaml")
    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    assert "pkg/**" in data.get("adopted_roots", [])
    assert "pkg/**" not in data.get("code_roots", [])
