import yaml
from pathlib import Path
from harbor.cli.main import main
import sys


def _prepare_proj(tmp_path: Path):
    proj = tmp_path
    (proj / "pkg").mkdir(parents=True, exist_ok=True)
    for n in ["a", "b", "c", "d", "e"]:
        (proj / "pkg" / f"{n}.py").write_text(f"def {n}():\n    pass\n", encoding="utf-8")
    return proj


def test_lock_no_register_adopted(tmp_path: Path, monkeypatch):
    proj = _prepare_proj(tmp_path)
    monkeypatch.chdir(proj)
    sys.argv = ["harbor", "init", "--force"]
    main()
    sys.argv = ["harbor", "lock", "--no-register-adopted"]
    main()
    cfg = (proj / ".harbor" / "config.yaml")
    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    assert "pkg/**" not in data.get("adopted_roots", [])


def test_lock_register_scan(tmp_path: Path, monkeypatch):
    proj = _prepare_proj(tmp_path)
    monkeypatch.chdir(proj)
    sys.argv = ["harbor", "init", "--force"]
    main()
    sys.argv = ["harbor", "lock", "--register-scan"]
    main()
    cfg = (proj / ".harbor" / "config.yaml")
    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    assert "pkg/**" in data.get("adopted_roots", [])
    assert "pkg/**" in data.get("code_roots", [])
