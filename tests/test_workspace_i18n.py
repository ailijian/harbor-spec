import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from harbor.cli.main import main


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _write_workspace_fixture(tmp_path: Path) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n  - harbor/**\n", encoding="utf-8")


def test_workspace_text_i18n_zh(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "zh")
    _write_workspace_fixture(tmp_path)

    inspect_out = run_cmd(["workspace", "inspect"])
    migrate_out = run_cmd(["workspace", "migrate", "--dry-run"])

    assert "Harbor 工作区检查" in inspect_out
    assert "配置" in inspect_out
    assert "建议摘要" in inspect_out

    assert "Harbor Workspace Migrate（Dry-run）" in migrate_out
    assert "安全提示：仅 dry-run，不会修改任何文件。" in migrate_out
    assert "未修改任何文件。" in migrate_out
    assert "摘要" in migrate_out
