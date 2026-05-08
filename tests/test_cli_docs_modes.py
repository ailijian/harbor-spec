import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.l2 import collect_all_indexed_modules, infer_module_from_path


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _empty_status_report():
    return SimpleNamespace(
        drift=[],
        modified=[],
        contract_changed=[],
        untracked=[],
        missing=[],
    )


def test_docs_changed_and_all_args_are_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: [])

    out_changed = run_cmd(["docs", "--changed"])
    out_all = run_cmd(["docs", "--all"])

    assert "No changed modules detected" in out_changed
    assert "No indexed modules found" in out_all


def test_docs_mode_flags_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        run_cmd(["docs", "--module", "harbor/core", "--changed"])
    with pytest.raises(SystemExit):
        run_cmd(["docs", "--changed", "--all"])
    with pytest.raises(SystemExit):
        run_cmd(["docs", "--module", "harbor/core", "--all"])


def test_docs_module_mode_still_works(monkeypatch):
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}")
    out = run_cmd(["docs", "--module", "harbor/core"])
    assert "# Module: harbor/core" in out


def test_infer_module_from_path_supports_windows_and_posix():
    assert infer_module_from_path(r"harbor\core\sync.py") == "harbor/core"
    assert infer_module_from_path("harbor/cli/main.py") == "harbor/cli"
    assert infer_module_from_path("app/schemas/__init__.py") == "app/schemas"


def test_changed_modules_detect_and_generate_each(monkeypatch):
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
        modified=[SimpleNamespace(file_path=r"harbor\cli\main.py")],
        contract_changed=[SimpleNamespace(file_path="harbor/core/index.py")],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    generated = []
    wrote = []

    def _gen(self, module):
        generated.append(module)
        return f"# Module: {module}"

    def _write(self, module, md, force=False):
        wrote.append(module)
        return Path(module) / "README.md"

    monkeypatch.setattr(cli_main.L2Generator, "generate", _gen)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write)

    out = run_cmd(["docs", "--changed"])
    assert "Changed modules detected:" in out
    assert "- harbor/cli" in out
    assert "- harbor/core" in out
    assert "Preview only. Use --write to update canonical L2 README files" in out
    assert generated == ["harbor/cli", "harbor/core"]
    assert wrote == []


def test_no_changed_modules_prints_friendly_message(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())
    out = run_cmd(["docs", "--changed"])
    assert "No changed modules detected" in out


def test_collect_all_indexed_modules_from_index_records(tmp_path: Path):
    idx_path = tmp_path / "l3_index.json"
    payload = {
        "files": {
            "harbor/core/sync.py": {"items": [{"id": "a"}]},
            "harbor/cli/main.py": {"items": [{"id": "b"}]},
            "harbor/empty/skip.py": {"items": []},
        }
    }
    idx_path.write_text(json.dumps(payload), encoding="utf-8")
    modules = collect_all_indexed_modules(index_path=idx_path)
    assert modules == ["harbor/cli", "harbor/core"]


def test_collect_all_indexed_modules_normalizes_repo_absolute_file_paths(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    idx_path = tmp_path / "l3_index.json"
    payload = {
        "files": {
            str((tmp_path / "harbor" / "core" / "l2.py").resolve()): {"items": [{"id": "a"}]},
            str((tmp_path / "harbor" / "cli" / "main.py").resolve()): {"items": [{"id": "b"}]},
            "C:/Users/GM/AppData/Local/Temp/outside.py": {"items": [{"id": "c"}]},
        }
    }
    idx_path.write_text(json.dumps(payload), encoding="utf-8")
    modules = collect_all_indexed_modules(index_path=idx_path)
    assert "harbor/cli" in modules
    assert "harbor/core" in modules
    assert "C:/Users/GM/AppData/Local/Temp" in modules


def test_docs_all_preview_does_not_write(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/cli", "harbor/core"])
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}")
    write_calls = {"count": 0}

    def _write(self, module, md, force=False):
        write_calls["count"] += 1
        return Path(module) / "README.md"

    monkeypatch.setattr(cli_main.L2Generator, "write", _write)
    out = run_cmd(["docs", "--all"])
    assert "Generating canonical L2 README for all indexed modules:" in out
    assert "Preview only. Use --write to update canonical L2 README files" in out
    assert write_calls["count"] == 0


def test_docs_all_write_updates_each_module(monkeypatch):
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor/cli", "harbor/core"])
    generated = []
    wrote = []

    def _gen(self, module):
        generated.append(module)
        return f"# Module: {module}"

    def _write(self, module, md, force=False):
        wrote.append(module)
        return [
            Path(".harbor/views/l2") / module / "README.md",
            Path(module) / "README.md",
        ]

    monkeypatch.setattr(cli_main.L2Generator, "generate", _gen)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write)
    out = run_cmd(["docs", "--all", "--write"])
    assert "Updated:" in out
    assert "- .harbor/views/l2/harbor/cli/README.md" in out
    assert "- .harbor/views/l2/harbor/core/README.md" in out
    assert "- harbor/cli/README.md" in out
    assert "- harbor/core/README.md" in out
    assert generated == ["harbor/cli", "harbor/core"]
    assert wrote == ["harbor/cli", "harbor/core"]


def test_docs_module_write_canonical_first_and_filters_meta(monkeypatch):
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}")

    def _write(self, module, md, force=False):
        return [
            Path(".harbor/views/l2") / module / "README.md",
            Path(".harbor/views/l2/_meta.json"),
            Path(module) / "README.md",
        ]

    monkeypatch.setattr(cli_main.L2Generator, "write", _write)
    out = run_cmd(["docs", "--module", "harbor/core", "--write"])
    assert "Updated:" in out
    assert "- .harbor/views/l2/harbor/core/README.md" in out
    assert "- harbor/core/README.md" in out
    assert ".harbor/views/l2/_meta.json" not in out
    canonical_idx = out.index("- .harbor/views/l2/harbor/core/README.md")
    export_idx = out.index("- harbor/core/README.md")
    assert canonical_idx < export_idx


def test_docs_all_write_skips_unsafe_indexed_modules_and_continues(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "collect_all_indexed_modules",
        lambda: ["harbor/core", "C:/Users/GM/AppData/Local/Temp/project/src", "../outside", ""],
    )
    generated = []
    wrote = []

    def _gen(self, module):
        generated.append(module)
        return f"# Module: {module}"

    def _write(self, module, md, force=False):
        wrote.append(module)
        return [
            Path(".harbor/views/l2") / module / "README.md",
            Path(module) / "README.md",
        ]

    monkeypatch.setattr(cli_main.L2Generator, "generate", _gen)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write)

    out = run_cmd(["docs", "--all", "--write"])
    assert "Skipped unsafe indexed modules:" in out
    assert "outside repository root" in out
    assert "contains parent traversal" in out
    assert "<outside-repo>" in out
    assert "C:/Users/GM/AppData/Local/Temp/project/src" not in out
    assert generated == ["harbor/core"]
    assert wrote == ["harbor/core"]
    assert "- .harbor/views/l2/harbor/core/README.md" in out
    assert "- harbor/core/README.md" in out


def test_docs_all_write_supports_repo_absolute_file_candidate(monkeypatch):
    repo_root = Path.cwd().resolve()
    monkeypatch.setattr(
        cli_main,
        "collect_all_indexed_modules",
        lambda: [
            f"{repo_root.as_posix()}/harbor/core/l2.py",
            "harbor/cli/main.py",
            "C:/Users/GM/AppData/Local/Temp/outside.py",
        ],
    )
    generated = []
    wrote = []

    def _gen(self, module):
        generated.append(module)
        return f"# Module: {module}"

    def _write(self, module, md, force=False):
        wrote.append(module)
        return [
            Path(".harbor/views/l2") / module / "README.md",
            Path(module) / "README.md",
        ]

    monkeypatch.setattr(cli_main.L2Generator, "generate", _gen)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write)

    out = run_cmd(["docs", "--all", "--write"])
    assert "Skipped unsafe indexed modules:" in out
    assert "<outside-repo>" in out
    assert "C:/Users/GM/AppData/Local/Temp/outside.py" not in out
    assert generated == ["harbor/core", "harbor/cli"]
    assert wrote == ["harbor/core", "harbor/cli"]
    assert "- .harbor/views/l2/harbor/core/README.md" in out
    assert "- .harbor/views/l2/harbor/cli/README.md" in out


def test_docs_all_write_only_unsafe_modules_returns_zero_and_does_not_write(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "collect_all_indexed_modules",
        lambda: ["C:/Users/GM/AppData/Local/Temp/outside.py", "../outside", ""],
    )
    calls = {"write": 0}
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}")

    def _write(self, module, md, force=False):
        calls["write"] += 1
        return [Path(".harbor/views/l2") / module / "README.md"]

    monkeypatch.setattr(cli_main.L2Generator, "write", _write)

    out = run_cmd(["docs", "--all", "--write"])
    assert "Skipped unsafe indexed modules:" in out
    assert "outside repository root" in out
    assert "contains parent traversal" in out
    assert "No indexed modules found. Nothing to generate." in out
    assert calls["write"] == 0


def test_docs_changed_write_skips_external_changed_module_and_writes_safe(monkeypatch):
    rep = SimpleNamespace(
        drift=[SimpleNamespace(file_path="harbor/core/sync.py")],
        modified=[SimpleNamespace(file_path="C:/Users/GM/AppData/Local/Temp/outside.py")],
        contract_changed=[],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)
    generated = []
    wrote = []

    def _gen(self, module):
        generated.append(module)
        return f"# Module: {module}"

    def _write(self, module, md, force=False):
        wrote.append(module)
        return [
            Path(".harbor/views/l2") / module / "README.md",
            Path(module) / "README.md",
        ]

    monkeypatch.setattr(cli_main.L2Generator, "generate", _gen)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write)

    out = run_cmd(["docs", "--changed", "--write"])
    assert "Skipped unsafe indexed modules:" in out
    assert "outside repository root" in out
    assert "<outside-repo>" in out
    assert "C:/Users/GM/AppData/Local/Temp/outside.py" not in out
    assert generated == ["harbor/core"]
    assert wrote == ["harbor/core"]


@pytest.mark.parametrize(
    "unsafe_module",
    [
        "../outside",
        "C:/Users/GM/AppData/Local/Temp/demo",
        "harbor/../../outside",
    ],
)
def test_docs_module_write_rejects_explicit_unsafe_module(monkeypatch, unsafe_module):
    calls = {"write": 0}
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}")

    def _write(self, module, md, force=False):
        calls["write"] += 1
        return [Path(".harbor/views/l2") / module / "README.md"]

    monkeypatch.setattr(cli_main.L2Generator, "write", _write)

    with pytest.raises(ValueError, match="Unsafe module is not allowed"):
        run_cmd(["docs", "--module", unsafe_module, "--write"])
    assert calls["write"] == 0


def test_docs_module_write_canonical_has_frontmatter_export_plain(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# Module: {module}\n")
    out = run_cmd(["docs", "--module", "harbor/core", "--write"])
    canonical = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    exported = tmp_path / "harbor" / "core" / "README.md"
    assert "Updated:" in out
    assert canonical.exists()
    assert exported.exists()
    assert canonical.read_text(encoding="utf-8").startswith("---\n")
    assert not exported.read_text(encoding="utf-8").startswith("---\n")
