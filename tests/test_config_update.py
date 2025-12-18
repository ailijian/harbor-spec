import yaml
from pathlib import Path
from harbor.core.init import Initializer


def test_write_config_and_update(tmp_path: Path):
    proj = tmp_path
    (proj / "pkg").mkdir(parents=True, exist_ok=True)
    (proj / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    init = Initializer(cwd=proj)
    cfg_file = init.write_config(["pkg/**"], force=True)
    assert cfg_file.exists()
    data = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
    assert "pkg/**" in data.get("code_roots", [])
    roots = data.get("code_roots", [])
    if "pkg/**" in roots:
        roots = [x for x in roots if x != "pkg/**"]
        data["code_roots"] = roots
        cfg_file.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    data2 = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
    assert "pkg/**" not in data2.get("code_roots", [])
