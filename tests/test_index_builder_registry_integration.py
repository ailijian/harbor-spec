from pathlib import Path
import json
import textwrap
import yaml

from harbor.core.index import IndexBuilder
from harbor.core.readonly_index import load_readonly_index


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_config(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_index_builder_default_registry_python_only(tmp_path: Path):
    code_root = tmp_path / "src"
    _write_file(
        code_root / "mod.py",
        textwrap.dedent(
            """
            def foo():
                \"\"\"doc\"\"\"
                return 1
            """
        ).strip(),
    )
    builder = IndexBuilder(code_roots=[str(code_root)], cache_dir=tmp_path / ".harbor" / "cache")

    assert builder.registry.is_enabled("python") is True
    assert builder.registry.is_enabled("typescript") is False
    assert builder.registry.get_enabled_languages() == ["python"]
    assert "adapter" not in builder.__dict__
    assert builder.adapter is builder.registry.get_adapter("python")
    assert builder._iter_files_by_enabled_adapters() == builder._iter_py_files()


def test_index_builder_file_discovery_includes_typescript_when_ts_enabled(tmp_path: Path):
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
    _write_file(code_root / "a.py", "def a():\n    return 1\n")
    _write_file(code_root / "b.ts", "export function b() { return 2; }\n")

    builder = IndexBuilder(
        code_roots=[str(code_root)],
        cache_dir=tmp_path / ".harbor" / "cache",
        config_path=cfg_path,
    )
    files = builder._iter_files_by_enabled_adapters()

    assert builder.registry.is_enabled("python") is True
    assert builder.registry.is_enabled("typescript") is True
    assert [path.suffix for path in files] == [".py", ".ts"]


def test_readonly_transient_index_discovers_typescript_when_ts_enabled(tmp_path: Path):
    cfg_path = tmp_path / ".harbor" / "config" / "harbor.yaml"
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
    _write_file(code_root / "a.py", "def a():\n    return 1\n")
    _write_file(code_root / "b.ts", "export function b(): number { return 2; }\n")

    payload = load_readonly_index(repo_root=tmp_path)

    assert sorted(payload["files"].keys()) == ["src/a.py", "src/b.ts"]
    assert not (tmp_path / ".harbor" / "cache" / "l3_index.json").exists()
    assert not (tmp_path / ".harbor" / "cache" / "harbor.db").exists()


def test_readonly_transient_index_matches_index_builder_discovery_when_ts_enabled(tmp_path: Path):
    cfg_path = tmp_path / ".harbor" / "config" / "harbor.yaml"
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
    _write_file(code_root / "main.py", "def main():\n    return 1\n")
    _write_file(code_root / "feature.ts", "export function feature(): number { return 2; }\n")

    readonly_files = set(load_readonly_index(repo_root=tmp_path)["files"].keys())
    assert readonly_files == {"src/feature.ts", "src/main.py"}
    assert not (tmp_path / ".harbor" / "cache" / "l3_index.json").exists()
    assert not (tmp_path / ".harbor" / "cache" / "harbor.db").exists()

    builder = IndexBuilder(
        code_roots=[str(code_root)],
        cache_dir=tmp_path / ".tmp-cache",
        config_path=cfg_path,
    )

    builder_files = {
        path.resolve().relative_to(tmp_path).as_posix()
        for path in builder._iter_files_by_enabled_adapters()
    }

    assert readonly_files == builder_files == {"src/feature.ts", "src/main.py"}


def test_build_keeps_python_entry_shape_stable(tmp_path: Path):
    code_root = tmp_path / "pkg"
    _write_file(
        code_root / "m.py",
        textwrap.dedent(
            """
            def foo(a, b):
                \"\"\"doc\"\"\"
                return a + b
            """
        ).strip(),
    )
    cache_dir = tmp_path / ".harbor" / "cache"
    builder = IndexBuilder(code_roots=[str(code_root)], cache_dir=cache_dir)

    report = builder.build(incremental=False)
    assert report.scanned_files == 1
    assert report.updated_files == 1
    assert report.total_items >= 1

    all_files = builder.db.get_all_files()
    assert len(all_files) == 1
    file_path = all_files[0][0]
    entries = builder.db.get_file_entries(file_path)
    assert entries

    entry = entries[0]
    assert set(entry.keys()) == {"id", "file_path", "signature_hash", "body_hash", "contract_hash", "meta"}
    assert set(entry["meta"].keys()) == {
        "name",
        "scope",
        "strictness",
        "lineno",
        "qualified_name",
        "docstring_raw_hash",
    }


def test_typescript_enabled_persists_ts_subjects_without_breaking_python_index(tmp_path: Path):
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
    _write_file(code_root / "ok.py", "def ok():\n    return 1\n")
    _write_file(code_root / "ignored.ts", "export function run(): number { return 1; }\n")

    builder = IndexBuilder(
        code_roots=[str(code_root)],
        cache_dir=tmp_path / ".harbor" / "cache",
        config_path=cfg_path,
    )
    report = builder.build(incremental=False)

    assert builder.registry.is_enabled("typescript") is True
    assert report.scanned_files == 2
    assert report.updated_files == 2
    assert report.skipped_files == 0

    entries_by_path = {file_path: builder.db.get_file_entries(file_path) for file_path, _ in builder.db.get_all_files()}
    py_entries = next(entries for file_path, entries in entries_by_path.items() if file_path.endswith("ok.py"))
    ts_entries = next(entries for file_path, entries in entries_by_path.items() if file_path.endswith("ignored.ts"))

    assert py_entries and py_entries[0]["meta"]["scope"] in {"public", "internal", "unknown"}
    assert ts_entries and len(ts_entries) == 1

    ts_entry = ts_entries[0]
    ts_meta = ts_entry["meta"]
    assert ts_entry["id"].startswith("typescript:")
    assert ts_meta["target_id"] == ts_entry["id"]
    assert ts_meta["func_id"] == ts_entry["id"]
    assert ts_meta["legacy_func_id"] == ts_entry["id"]
    assert ts_meta["language"] == "typescript"
    assert ts_meta["symbol_kind"] == "function"
    assert ts_meta["qualified_name"] == "run"
    assert ts_meta["file_path"].endswith("ignored.ts")
    assert ts_meta["lineno"] == 1
    assert ts_meta["end_lineno"] == 1
    assert ts_meta["visibility"] == "public"
    assert ts_entry["signature_hash"]
    assert ts_entry["body_hash"]


def test_build_writes_typescript_additive_fields_into_runtime_cache_snapshot(tmp_path: Path):
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
    _write_file(
        code_root / "service.ts",
        textwrap.dedent(
            """
            /**
             * @param x value
             * @returns value
             */
            export function api(x: number): number { return x + 1; }
            """
        ).strip(),
    )
    cache_dir = tmp_path / ".harbor" / "cache"
    builder = IndexBuilder(
        code_roots=[str(code_root)],
        cache_dir=cache_dir,
        config_path=cfg_path,
    )

    report = builder.build(incremental=False)
    payload = json.loads((cache_dir / "l3_index.json").read_text(encoding="utf-8"))
    file_key = next(iter(payload["files"]))
    items = payload["files"][file_key]["items"]

    assert report.scanned_files == 1
    assert file_key.endswith("service.ts")
    assert len(items) == 1
    item = items[0]
    assert item["target_id"].startswith("typescript:")
    assert item["target_id"].endswith(":function:api")
    assert item["func_id"] == item["target_id"]
    assert item["legacy_func_id"] == item["target_id"]
    assert item["language"] == "typescript"
    assert item["symbol_kind"] == "function"
    assert item["file_path"].endswith("service.ts")
    assert item["contract_presence"] == "present"
    assert item["contract_required"] is True
    assert item["contract_source_kinds"] == ["tsdoc"]
    assert len(item["contract_source_fingerprints"]) == 1
    assert item["source_confidence_summary"] == "high"
