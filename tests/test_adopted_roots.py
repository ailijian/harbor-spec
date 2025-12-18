import yaml
from pathlib import Path
from harbor.core.init import Initializer


def test_adopted_roots_write_and_remove(tmp_path: Path):
    proj = tmp_path
    init = Initializer(cwd=proj)
    cfg = init.write_config(["**/*.py"], force=True)
    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    assert data.get("adopted_roots") == []
    adopted = data.get("adopted_roots", [])
    adopted.append("pkg/**")
    data["adopted_roots"] = adopted
    roots = data.get("code_roots", [])
    roots.append("pkg/**")
    data["code_roots"] = roots
    cfg.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    data2 = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    assert "pkg/**" in data2.get("adopted_roots", [])
    assert "pkg/**" in data2.get("code_roots", [])
    data2["adopted_roots"] = [x for x in data2.get("adopted_roots", []) if x != "pkg/**"]
    data2["code_roots"] = [x for x in data2.get("code_roots", []) if x != "pkg/**"]
    cfg.write_text(yaml.safe_dump(data2, allow_unicode=True, sort_keys=False), encoding="utf-8")
    data3 = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    assert "pkg/**" not in data3.get("adopted_roots", [])
    assert "pkg/**" not in data3.get("code_roots", [])
