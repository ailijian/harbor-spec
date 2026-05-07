import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _status_report_with_changed():
    return SimpleNamespace(
        counts={"drift": 1, "contract_changed": 0, "modified": 1, "untracked": 0, "missing": 0},
        drift=[SimpleNamespace(id="a", details="x", file_path="harbor/core/sync.py")],
        contract_changed=[],
        modified=[SimpleNamespace(id="b", details="y", file_path=r"harbor\cli\main.py")],
        untracked=[],
        missing=[],
    )


def _empty_status_report():
    return SimpleNamespace(
        counts={"drift": 0, "contract_changed": 0, "modified": 0, "untracked": 0, "missing": 0},
        drift=[],
        contract_changed=[],
        modified=[],
        untracked=[],
        missing=[],
    )


def _empty_validation_report():
    return SimpleNamespace(valid=[], violations=[])


def _patch_finish_basics(monkeypatch):
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _empty_validation_report())
    monkeypatch.setattr(cli_main, "resolve_provider", lambda: SimpleNamespace(name="mock", model="mock-model"))


def test_finish_default_does_not_run_sync_context_flow(monkeypatch):
    _patch_finish_basics(monkeypatch)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())

    calls = {"docs": 0, "seal": 0, "stale": 0, "log": 0, "lock": 0, "promote": 0}

    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: calls.__setitem__("docs", calls["docs"] + 1))
    monkeypatch.setattr(cli_main, "write_module_capsule", lambda context: calls.__setitem__("seal", calls["seal"] + 1))
    monkeypatch.setattr(
        cli_main,
        "check_module_capsule_stale",
        lambda context: calls.__setitem__("stale", calls["stale"] + 1),
    )
    monkeypatch.setattr(cli_main.DiaryManager, "log", lambda self, **kwargs: calls.__setitem__("log", calls["log"] + 1))
    monkeypatch.setattr(
        cli_main.DiaryManager,
        "export_markdown",
        lambda self, **kwargs: calls.__setitem__("log", calls["log"] + 1),
    )
    monkeypatch.setattr(
        cli_main.IndexBuilder,
        "iter_build",
        lambda self, incremental=True: calls.__setitem__("lock", calls["lock"] + 1) or iter([]),
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_skill",
        lambda module: calls.__setitem__("promote", calls["promote"] + 1),
    )

    out = run_cmd(["finish"])
    assert "Harbor Finish:" in out
    assert "Next steps:" in out
    assert "Context Sync:" not in out
    assert calls["docs"] == 0
    assert calls["seal"] == 0
    assert calls["stale"] == 0
    assert calls["log"] == 0
    assert calls["lock"] == 0
    assert calls["promote"] == 0


def test_finish_sync_context_runs_status_check_docs_seal_stale(monkeypatch):
    _patch_finish_basics(monkeypatch)

    status_calls = {"count": 0}

    def _status(self):
        status_calls["count"] += 1
        return _status_report_with_changed()

    monkeypatch.setattr(cli_main.SyncEngine, "check_status", _status)

    docs_generated = []
    docs_written = []
    capsule_written = []
    stale_checked = []
    side_effect_calls = {"lock": 0, "log": 0, "promote": 0}

    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: docs_generated.append(module) or f"# {module}")
    monkeypatch.setattr(
        cli_main.L2Generator,
        "write",
        lambda self, module, md, force=False: docs_written.append(module) or (Path(module) / "README.md"),
    )
    monkeypatch.setattr(
        cli_main,
        "collect_module_context",
        lambda module: {"module": module, "key_files": [f"{module}/x.py"], "contracts": []},
    )

    def _write_capsule(context):
        module = context.get("module", "")
        capsule_written.append(module)
        return SimpleNamespace(
            canonical_paths=[Path(f".harbor/views/modules/{module}/module-card.md")],
            exported_paths=[],
        )

    monkeypatch.setattr(cli_main, "write_module_capsule", _write_capsule)

    def _check_stale(context):
        module = context.get("module", "")
        stale_checked.append(module)
        return {"status": "up_to_date"}

    monkeypatch.setattr(cli_main, "check_module_capsule_stale", _check_stale)
    monkeypatch.setattr(
        cli_main.IndexBuilder,
        "iter_build",
        lambda self, incremental=True: side_effect_calls.__setitem__("lock", side_effect_calls["lock"] + 1) or iter([]),
    )
    monkeypatch.setattr(
        cli_main.DiaryManager,
        "log",
        lambda self, **kwargs: side_effect_calls.__setitem__("log", side_effect_calls["log"] + 1),
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_skill",
        lambda module: side_effect_calls.__setitem__("promote", side_effect_calls["promote"] + 1),
    )

    out = run_cmd(["finish", "--sync-context"])
    assert "Harbor Finish:" in out
    assert "Context Sync:" in out
    assert "Refreshing L2 README for changed modules" in out
    assert "Refreshing Module Capsules for changed modules" in out
    assert "Checking Module Capsule stale status" in out
    assert "Run `harbor log`" in out
    assert "Run `harbor accept`" in out
    assert "Optionally run `harbor module promote-skill <module>`" in out
    assert status_calls["count"] >= 3
    assert docs_generated == ["harbor/cli", "harbor/core"]
    assert docs_written == ["harbor/cli", "harbor/core"]
    assert capsule_written == ["harbor/cli", "harbor/core"]
    assert stale_checked == ["harbor/cli", "harbor/core"]
    assert side_effect_calls["lock"] == 0
    assert side_effect_calls["log"] == 0
    assert side_effect_calls["promote"] == 0


def test_finish_sync_context_no_changed_modules_friendly(monkeypatch):
    _patch_finish_basics(monkeypatch)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _empty_status_report())

    calls = {"docs_write": 0, "seal_write": 0, "stale": 0}
    monkeypatch.setattr(
        cli_main.L2Generator,
        "write",
        lambda self, module, md, force=False: calls.__setitem__("docs_write", calls["docs_write"] + 1),
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_capsule",
        lambda context: calls.__setitem__("seal_write", calls["seal_write"] + 1),
    )
    monkeypatch.setattr(
        cli_main,
        "check_module_capsule_stale",
        lambda context: calls.__setitem__("stale", calls["stale"] + 1),
    )

    out = run_cmd(["finish", "--sync-context"])
    assert "No changed modules detected. Context sync skipped." in out
    assert calls["docs_write"] == 0
    assert calls["seal_write"] == 0
    assert calls["stale"] == 0


def test_finish_sync_context_write_boundary_only_allows_docs_and_capsules(monkeypatch):
    _patch_finish_basics(monkeypatch)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _status_report_with_changed())

    written_paths = []
    forbidden_markers = [".env", "migrations", ".github/workflows", ".agents/skills"]

    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# {module}")

    def _write_readme(self, module, md, force=False):
        p = Path(module) / "README.md"
        written_paths.append(p.as_posix())
        return p

    monkeypatch.setattr(cli_main.L2Generator, "write", _write_readme)
    monkeypatch.setattr(
        cli_main,
        "collect_module_context",
        lambda module: {"module": module, "key_files": [f"{module}/x.py"], "contracts": []},
    )

    def _write_capsule(context):
        module = context.get("module", "")
        p = Path(f".harbor/views/modules/{module}/module-card.md")
        written_paths.append(p.as_posix())
        return SimpleNamespace(canonical_paths=[p], exported_paths=[])

    monkeypatch.setattr(cli_main, "write_module_capsule", _write_capsule)
    monkeypatch.setattr(cli_main, "check_module_capsule_stale", lambda context: {"status": "up_to_date"})

    out = run_cmd(["finish", "--sync-context"])
    assert "Context Sync:" in out
    assert written_paths
    assert any(path.endswith("/README.md") for path in written_paths)
    assert any(path.startswith(".harbor/views/modules/") for path in written_paths)
    for path in written_paths:
        assert all(marker not in path for marker in forbidden_markers)


def test_finish_sync_context_ignores_changed_modules_outside_workspace(monkeypatch):
    _patch_finish_basics(monkeypatch)
    monkeypatch.setattr(
        cli_main.SyncEngine,
        "check_status",
        lambda self: SimpleNamespace(
            counts={"drift": 1, "contract_changed": 0, "modified": 1, "untracked": 0, "missing": 0},
            drift=[SimpleNamespace(id="a", details="x", file_path="harbor/core/sync.py")],
            contract_changed=[],
            modified=[SimpleNamespace(id="b", details="y", file_path="C:/Users/GM/AppData/Local/Temp/outside.py")],
            untracked=[],
            missing=[],
        ),
    )

    written_paths = []
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# {module}")

    def _write_readme(self, module, md, force=False):
        path = Path(module) / "README.md"
        written_paths.append(path.as_posix())
        return path

    monkeypatch.setattr(cli_main.L2Generator, "write", _write_readme)
    monkeypatch.setattr(
        cli_main,
        "collect_module_context",
        lambda module: {"module": module, "key_files": [f"{module}/x.py"], "contracts": []},
    )

    def _write_capsule(context):
        module = context.get("module", "")
        rel_base = Path(".harbor/views/modules") / module
        canonical_paths = [
            rel_base / "module-card.md",
            rel_base / "review-checklist.md",
            rel_base / "debug-playbook.md",
        ]
        written_paths.extend([p.as_posix() for p in canonical_paths])
        return SimpleNamespace(canonical_paths=canonical_paths, exported_paths=[])

    monkeypatch.setattr(cli_main, "write_module_capsule", _write_capsule)
    monkeypatch.setattr(cli_main, "check_module_capsule_stale", lambda context: {"status": "up_to_date"})

    _ = run_cmd(["finish", "--sync-context"])
    assert "harbor/core/README.md" in written_paths
    assert ".harbor/views/modules/harbor/core/module-card.md" in written_paths
    assert ".harbor/views/modules/harbor/core/review-checklist.md" in written_paths
    assert ".harbor/views/modules/harbor/core/debug-playbook.md" in written_paths
    assert all("C:/Users/GM/AppData/Local/Temp" not in path for path in written_paths)
