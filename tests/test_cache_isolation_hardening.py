import hashlib
import json
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from harbor.cli.main import main
from harbor.core.index import IndexBuilder


def _run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _fingerprint(path: Path):
    if not path.exists():
        return ("missing",)
    data = path.read_bytes()
    return ("exists", len(data), path.stat().st_mtime_ns, hashlib.sha256(data).hexdigest())


def _snapshot_repo_cache():
    repo_root = Path(__file__).resolve().parents[1]
    cache_dir = repo_root / ".harbor" / "cache"
    return {
        "db": _fingerprint(cache_dir / "harbor.db"),
        "json": _fingerprint(cache_dir / "l3_index.json"),
    }


def test_index_builder_uses_isolated_cache_dir_without_touching_repo_cache(tmp_path, monkeypatch):
    before = _snapshot_repo_cache()
    monkeypatch.chdir(tmp_path)

    src_root = tmp_path / "src"
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "mod.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    cache_dir = tmp_path / ".harbor" / "cache"

    builder = IndexBuilder(code_roots=[str(src_root)], cache_dir=cache_dir)
    rep = builder.build(incremental=True)

    assert rep.scanned_files >= 1
    assert (cache_dir / "harbor.db").exists()
    assert (cache_dir / "l3_index.json").exists()
    assert _snapshot_repo_cache() == before


def test_cli_status_writes_cache_in_tmp_workspace_only(tmp_path, monkeypatch):
    before = _snapshot_repo_cache()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")

    out = _run_cmd(["status"])

    assert out.strip()
    assert ("Harbor Context Status" in out) or ("No changes detected." in out)
    assert (tmp_path / ".harbor" / "cache" / "harbor.db").exists()
    assert _snapshot_repo_cache() == before


def test_external_temp_paths_only_land_in_isolated_workspace_index(tmp_path, monkeypatch):
    before = _snapshot_repo_cache()
    monkeypatch.chdir(tmp_path)

    cache_dir = tmp_path / ".harbor" / "cache"
    with tempfile.TemporaryDirectory() as ext_dir:
        ext_root = Path(ext_dir)
        (ext_root / "outside_mod.py").write_text("def outside():\n    return 42\n", encoding="utf-8")
        builder = IndexBuilder(code_roots=[str(ext_root)], cache_dir=cache_dir)
        builder.build(incremental=True)
        payload = json.loads((cache_dir / "l3_index.json").read_text(encoding="utf-8"))
        assert payload.get("files")
        assert any(str(ext_root).replace("\\", "/") in fp for fp in payload["files"].keys())

    assert _snapshot_repo_cache() == before


def test_docs_all_external_only_index_is_isolated(tmp_path, monkeypatch):
    before = _snapshot_repo_cache()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")
    cache_dir = tmp_path / ".harbor" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "l3_index.json").write_text(
        json.dumps(
            {
                "files": {
                    "C:/Users/GM/AppData/Local/Temp/pytest-isolated/outside.py": {
                        "mtime": 0.0,
                        "file_hash": "",
                        "items": [{"id": "outside.mod.fn"}],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    out = _run_cmd(["docs", "--all", "--write"])

    assert "Skipped unsafe indexed modules:" in out
    assert "No indexed modules found. Nothing to generate." in out
    assert _snapshot_repo_cache() == before
