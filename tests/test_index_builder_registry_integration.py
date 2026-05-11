from pathlib import Path
import textwrap
import yaml

from harbor.core.index import IndexBuilder


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
    assert builder._iter_files_by_enabled_adapters() == builder._iter_py_files()


def test_index_builder_file_discovery_matches_python_only_when_ts_enabled(tmp_path: Path):
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
    assert builder.registry.is_enabled("typescript") is False
    assert len(files) == 1
    assert files[0].suffix == ".py"


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


def test_typescript_enabled_unavailable_does_not_affect_python_index(tmp_path: Path):
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
    _write_file(code_root / "ignored.ts", "export const x = 1;\n")

    builder = IndexBuilder(
        code_roots=[str(code_root)],
        cache_dir=tmp_path / ".harbor" / "cache",
        config_path=cfg_path,
    )
    report = builder.build(incremental=False)

    assert report.scanned_files == 1
    assert report.updated_files == 1
    assert report.skipped_files == 0
