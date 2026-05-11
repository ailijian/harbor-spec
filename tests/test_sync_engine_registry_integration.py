from pathlib import Path
import textwrap
import yaml

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_config(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_sync_engine_default_registry_python_only(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code_root = tmp_path / "src"
    _write(code_root / "a.py", "def a():\n    return 1\n")

    eng = SyncEngine()
    eng.code_roots = [str(code_root)]

    assert eng.registry.is_enabled("python") is True
    assert eng.registry.is_enabled("typescript") is False
    assert eng._iter_files_by_enabled_adapters() == eng._iter_py_files()


def test_sync_engine_file_discovery_matches_python_only_when_ts_enabled(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".harbor" / "config.yaml"
    _write_config(
        cfg_path,
        {
            "code_roots": [str(tmp_path / "src")],
            "languages": {
                "python": {"enabled": True},
                "typescript": {"enabled": True},
            },
        },
    )
    code_root = tmp_path / "src"
    _write(code_root / "x.py", "def x():\n    return 1\n")
    _write(code_root / "y.ts", "export function y() { return 2; }\n")

    eng = SyncEngine(config_path=cfg_path)
    eng.code_roots = [str(code_root)]
    files = eng._iter_files_by_enabled_adapters()

    assert eng.registry.is_enabled("python") is True
    assert eng.registry.is_enabled("typescript") is False
    assert len(files) == 1
    assert files[0].suffix == ".py"


def test_typescript_enabled_unavailable_does_not_affect_python_status(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".harbor" / "config.yaml"
    _write_config(
        cfg_path,
        {
            "code_roots": [str(tmp_path / "src")],
            "languages": {
                "python": {"enabled": True},
                "typescript": {"enabled": True},
            },
        },
    )
    code_root = tmp_path / "src"
    _write(
        code_root / "ok.py",
        textwrap.dedent(
            """
            def ok(v):
                \"\"\"doc\"\"\"
                return v
            """
        ).strip(),
    )
    _write(code_root / "ignored.ts", "export const ignored = true;\n")

    builder = IndexBuilder(code_roots=[str(code_root)], cache_dir=tmp_path / ".harbor" / "cache")
    builder.build(incremental=True)

    eng = SyncEngine(config_path=cfg_path)
    eng.code_roots = [str(code_root)]
    report = eng.check_status()

    assert report.counts["drift"] == 0
    assert report.counts["modified"] == 0
    assert report.counts["contract_changed"] == 0
    assert report.counts["contract_gap"] == 0
    assert report.counts["contract_parse_error"] == 0
