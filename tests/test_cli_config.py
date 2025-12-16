import sys
from pathlib import Path
import yaml

from harbor.cli.main import main


def test_config_add_list_remove(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / ".harbor" / "config.yaml"

    # add
    sys.argv = ["harbor", "config", "add", "backend/legacy/**"]
    main()
    assert cfg.exists()
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    assert "backend/legacy/**" in data.get("code_roots", [])

    # list (just ensure it doesn't crash and reads file)
    sys.argv = ["harbor", "config", "list"]
    main()

    # remove
    sys.argv = ["harbor", "config", "remove", "backend/legacy/**"]
    main()
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    assert "backend/legacy/**" not in data.get("code_roots", [])

