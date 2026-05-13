import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.l2 import L2Generator
from harbor.core.module_capsule import collect_module_context, write_module_capsule
from harbor.core.stale import ModuleStaleSummary, ViewStaleResult


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


@pytest.fixture(autouse=True)
def _disable_change_window_writes(monkeypatch):
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", lambda *args, **kwargs: None)


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def run_cmd_with_exit_code(argv):
    buf = StringIO()
    code = 0
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as ex:
            code = ex.code if isinstance(ex.code, int) else 1
    return code, buf.getvalue()


class _FakeWindowsStream:
    def __init__(self, encoding="utf-8", *, is_tty=False, errors="strict", fail_reconfigure=False):
        self.encoding = encoding
        self.errors = errors
        self._is_tty = is_tty
        self._fail_reconfigure = fail_reconfigure
        self.reconfigure_calls = []

    def isatty(self):
        return self._is_tty

    @property
    def reconfigured_to(self):
        if not self.reconfigure_calls:
            return None
        last_call = self.reconfigure_calls[-1]
        return last_call.get("encoding"), last_call.get("errors")

    def reconfigure(self, *, encoding=None, errors=None):
        if self._fail_reconfigure:
            raise OSError("reconfigure blocked")
        self.reconfigure_calls.append({"encoding": encoding, "errors": errors})
        if encoding is not None:
            self.encoding = encoding
        if errors is not None:
            self.errors = errors


class _FakeRedirectedStream(_FakeWindowsStream):
    def __init__(self, encoding="utf-8"):
        super().__init__(encoding=encoding, is_tty=False)

    def isatty(self):
        return super().isatty()

    def reconfigure(self, *, encoding=None, errors=None):
        super().reconfigure(encoding=encoding, errors=errors)


def test_configure_windows_stdio_defaults_non_tty_to_utf8(monkeypatch):
    stdout = _FakeWindowsStream(encoding="cp936")
    stderr = _FakeWindowsStream(encoding="cp936")
    fake_sys = SimpleNamespace(stdout=stdout, stderr=stderr, flags=SimpleNamespace(utf8_mode=0))

    monkeypatch.setattr(cli_main.os, "name", "nt")
    monkeypatch.setattr(cli_main, "sys", fake_sys)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    cli_main._configure_windows_stdio()

    assert stdout.reconfigured_to == ("utf-8", "strict")
    assert stderr.reconfigured_to == ("utf-8", "strict")


def test_configure_windows_stdio_respects_pythonioencoding(monkeypatch):
    stdout = _FakeWindowsStream(encoding="cp936", is_tty=True)
    stderr = _FakeWindowsStream(encoding="cp936", is_tty=True)
    fake_sys = SimpleNamespace(stdout=stdout, stderr=stderr, flags=SimpleNamespace(utf8_mode=0))

    monkeypatch.setattr(cli_main.os, "name", "nt")
    monkeypatch.setattr(cli_main, "sys", fake_sys)
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252:replace")
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    cli_main._configure_windows_stdio()

    assert stdout.reconfigured_to == ("cp1252", "replace")
    assert stderr.reconfigured_to == ("cp1252", "replace")


def test_configure_windows_stdio_prefers_utf8_mode(monkeypatch):
    stdout = _FakeWindowsStream(encoding="cp936", is_tty=True)
    stderr = _FakeWindowsStream(encoding="cp936", is_tty=True)
    fake_sys = SimpleNamespace(stdout=stdout, stderr=stderr, flags=SimpleNamespace(utf8_mode=1))

    monkeypatch.setattr(cli_main.os, "name", "nt")
    monkeypatch.setattr(cli_main, "sys", fake_sys)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    cli_main._configure_windows_stdio()

    assert stdout.reconfigured_to == ("utf-8", "strict")
    assert stderr.reconfigured_to == ("utf-8", "strict")


def test_configure_windows_stdio_normalizes_non_utf8_tty(monkeypatch):
    stdout = _FakeWindowsStream(encoding="cp936", is_tty=True)
    stderr = _FakeWindowsStream(encoding="utf8", is_tty=True)
    fake_sys = SimpleNamespace(stdout=stdout, stderr=stderr, flags=SimpleNamespace(utf8_mode=0))

    monkeypatch.setattr(cli_main.os, "name", "nt")
    monkeypatch.setattr(cli_main, "sys", fake_sys)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    cli_main._configure_windows_stdio()

    assert stdout.reconfigured_to == ("utf-8", "strict")
    assert stderr.reconfigured_to is None


def test_configure_windows_stdio_skips_utf8_tty(monkeypatch):
    stdout = _FakeWindowsStream(encoding="utf-8-sig", is_tty=True)
    stderr = _FakeWindowsStream(encoding="utf-8", is_tty=True)
    fake_sys = SimpleNamespace(stdout=stdout, stderr=stderr, flags=SimpleNamespace(utf8_mode=0))

    monkeypatch.setattr(cli_main.os, "name", "nt")
    monkeypatch.setattr(cli_main, "sys", fake_sys)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    cli_main._configure_windows_stdio()

    assert stdout.reconfigured_to is None
    assert stderr.reconfigured_to is None


def test_configure_windows_stdio_reconfigure_failure_does_not_interrupt(monkeypatch):
    stdout = _FakeWindowsStream(encoding="cp936", is_tty=True, fail_reconfigure=True)
    stderr = _FakeWindowsStream(encoding="cp936")
    fake_sys = SimpleNamespace(stdout=stdout, stderr=stderr, flags=SimpleNamespace(utf8_mode=0))

    monkeypatch.setattr(cli_main.os, "name", "nt")
    monkeypatch.setattr(cli_main, "sys", fake_sys)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    cli_main._configure_windows_stdio()

    assert stdout.reconfigured_to is None
    assert stderr.reconfigured_to == ("utf-8", "strict")


def test_configure_redirected_windows_stdio_prefers_locale_encoding(monkeypatch):
    test_configure_windows_stdio_defaults_non_tty_to_utf8(monkeypatch)


def test_configure_redirected_windows_stdio_respects_pythonioencoding(monkeypatch):
    test_configure_windows_stdio_respects_pythonioencoding(monkeypatch)


def _status_report_with_changed():
    return SimpleNamespace(
        counts={
            "drift": 1,
            "contract_changed": 0,
            "modified": 1,
            "contract_gap": 0,
            "skipped_no_contract": 0,
            "contract_parse_error": 0,
            "untracked": 0,
            "missing": 0,
        },
        drift=[SimpleNamespace(id="a", details="x", file_path="harbor/core/sync.py")],
        contract_changed=[],
        modified=[SimpleNamespace(id="b", details="y", file_path=r"harbor\cli\main.py")],
        contract_gap=[],
        skipped_no_contract=[],
        contract_parse_error=[],
        untracked=[],
        missing=[],
    )


def _empty_status_report():
    return SimpleNamespace(
        counts={
            "drift": 0,
            "contract_changed": 0,
            "modified": 0,
            "contract_gap": 0,
            "skipped_no_contract": 0,
            "contract_parse_error": 0,
            "untracked": 0,
            "missing": 0,
        },
        drift=[],
        contract_changed=[],
        modified=[],
        contract_gap=[],
        skipped_no_contract=[],
        contract_parse_error=[],
        untracked=[],
        missing=[],
    )


def _empty_validation_report():
    return SimpleNamespace(valid=[], violations=[], advisory=[], counts={"valid": 0, "violations": 0, "advisory": 0})


def _status_report_for_paths(*paths):
    entries = [SimpleNamespace(id=f"item-{idx}", details=f"changed-{idx}", file_path=path) for idx, path in enumerate(paths, start=1)]
    return SimpleNamespace(
        counts={
            "drift": 0,
            "contract_changed": 0,
            "modified": len(entries),
            "contract_gap": 0,
            "skipped_no_contract": 0,
            "contract_parse_error": 0,
            "unsupported_syntax_advisory": 0,
            "untracked": 0,
            "missing": 0,
        },
        drift=[],
        contract_changed=[],
        modified=entries,
        contract_gap=[],
        skipped_no_contract=[],
        contract_parse_error=[],
        unsupported_syntax_advisory=[],
        untracked=[],
        missing=[],
    )


def _view_summary(module: str, *, l2="up_to_date", export="up_to_date", capsule="up_to_date") -> ModuleStaleSummary:
    return ModuleStaleSummary(
        module=module,
        l2_readme=ViewStaleResult("L2 README", l2, "l2 reason", f"harbor docs --module {module} --write"),
        l2_readme_export=ViewStaleResult("L2 README Export", export, "export reason", f"harbor docs --module {module} --write"),
        module_capsule=ViewStaleResult("Module Capsule", capsule, "capsule reason", f"harbor module seal {module} --write"),
    )


def _write_sample_repo(tmp_path: Path) -> None:
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("code_roots:\n- harbor/**\n- tests/**\nexclude_paths: []\n", encoding="utf-8")

    harbor_pkg = tmp_path / "harbor"
    harbor_pkg.mkdir(parents=True, exist_ok=True)
    (harbor_pkg / "__init__.py").write_text(
        '''def version() -> str:
    """Return a stable version marker.

    Behavior:
      - Returns a deterministic string for generated-view tests.

    Returns:
      str: Stable version marker.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    """
    return "1.0"
''',
        encoding="utf-8",
    )

    core_pkg = harbor_pkg / "core"
    core_pkg.mkdir(parents=True, exist_ok=True)
    (core_pkg / "__init__.py").write_text("", encoding="utf-8")
    (core_pkg / "sample.py").write_text(
        '''def run(value: int) -> int:
    """Return the provided value.

    Behavior:
      - Returns the provided integer unchanged.

    Args:
      value (int): Input integer.

    Returns:
      int: Same integer value.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    """
    return value
''',
        encoding="utf-8",
    )

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "test_sample.py").write_text(
        "def test_sample():\n"
        "    assert True\n",
        encoding="utf-8",
    )


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
        lambda self, module, md, force=False: docs_written.append(module) or [
            Path(".harbor/views/l2") / module / "README.md",
            Path(module) / "README.md",
        ],
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

    def _check_stale(module):
        stale_checked.append(module)
        return _view_summary(module)

    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", _check_stale)
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
    assert "Running changed-scope stale self-check" in out
    assert "Changed-scope stale self-check passed for 3 modules." in out
    assert "harbor checkpoint --ci --format json --advice basic" in out
    assert "harbor stale --ci --format json --advice basic" in out
    assert "harbor doctor --ci --format json --advice basic" in out
    assert status_calls["count"] >= 1
    assert docs_generated == ["harbor", "harbor/cli", "harbor/core"]
    assert docs_written == ["harbor", "harbor/cli", "harbor/core"]
    assert capsule_written == ["harbor", "harbor/cli", "harbor/core"]
    assert stale_checked == ["harbor", "harbor/cli", "harbor/core"]
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
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: calls.__setitem__("stale", calls["stale"] + 1))

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
        canonical = Path(".harbor/views/l2") / module / "README.md"
        exported = Path(module) / "README.md"
        written_paths.append(canonical.as_posix())
        written_paths.append(exported.as_posix())
        return [canonical, exported]

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
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _view_summary(module))

    out = run_cmd(["finish", "--sync-context"])
    assert "Context Sync:" in out
    assert written_paths
    assert any(path.startswith(".harbor/views/l2/") for path in written_paths)
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
            counts={
                "drift": 1,
                "contract_changed": 0,
                "modified": 1,
                "contract_gap": 0,
                "skipped_no_contract": 0,
                "contract_parse_error": 0,
                "untracked": 0,
                "missing": 0,
            },
            drift=[SimpleNamespace(id="a", details="x", file_path="harbor/core/sync.py")],
            contract_changed=[],
            modified=[SimpleNamespace(id="b", details="y", file_path="C:/Users/GM/AppData/Local/Temp/outside.py")],
            contract_gap=[],
            skipped_no_contract=[],
            contract_parse_error=[],
            untracked=[],
            missing=[],
        ),
    )

    written_paths = []
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# {module}")

    def _write_readme(self, module, md, force=False):
        canonical = Path(".harbor/views/l2") / module / "README.md"
        exported = Path(module) / "README.md"
        written_paths.append(canonical.as_posix())
        written_paths.append(exported.as_posix())
        return [canonical, exported]

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
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _view_summary(module))

    out = run_cmd(["finish", "--sync-context"])
    assert "C:/Users/GM/AppData/Local/Temp/outside.py" not in out
    assert ".harbor/views/l2/harbor/README.md" in written_paths
    assert "harbor/README.md" in written_paths
    assert ".harbor/views/l2/harbor/core/README.md" in written_paths
    assert "harbor/core/README.md" in written_paths
    assert ".harbor/views/modules/harbor/module-card.md" in written_paths
    assert ".harbor/views/modules/harbor/review-checklist.md" in written_paths
    assert ".harbor/views/modules/harbor/debug-playbook.md" in written_paths
    assert ".harbor/views/modules/harbor/core/module-card.md" in written_paths
    assert ".harbor/views/modules/harbor/core/review-checklist.md" in written_paths
    assert ".harbor/views/modules/harbor/core/debug-playbook.md" in written_paths
    context_sync_output = out.split("Context Sync:", 1)[1]
    assert "C:/Users/GM/AppData/Local/Temp/outside.py" not in context_sync_output
    assert all("C:/Users/GM/AppData/Local/Temp" not in path for path in written_paths)


def test_finish_sync_context_adds_only_indexed_parent_modules(monkeypatch):
    _patch_finish_basics(monkeypatch)
    monkeypatch.setattr(
        cli_main.SyncEngine,
        "check_status",
        lambda self: SimpleNamespace(
            counts={
                "drift": 0,
                "contract_changed": 0,
                "modified": 2,
                "contract_gap": 0,
                "skipped_no_contract": 0,
                "contract_parse_error": 0,
                "untracked": 0,
                "missing": 0,
            },
            drift=[],
            contract_changed=[],
            modified=[
                SimpleNamespace(id="a", details="x", file_path="harbor/cli/main.py"),
                SimpleNamespace(id="b", details="y", file_path="tests/test_cli_finish_sync_context.py"),
            ],
            contract_gap=[],
            skipped_no_contract=[],
            contract_parse_error=[],
            untracked=[],
            missing=[],
        ),
    )
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor", "harbor/cli", "tests"])

    written_modules = []
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# {module}")
    monkeypatch.setattr(
        cli_main.L2Generator,
        "write",
        lambda self, module, md, force=False: written_modules.append(module) or [],
    )
    monkeypatch.setattr(
        cli_main,
        "collect_module_context",
        lambda module: {"module": module, "key_files": [f"{module}/x.py"], "contracts": []},
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_capsule",
        lambda context: SimpleNamespace(canonical_paths=[], exported_paths=[]),
    )
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _view_summary(module))

    _ = run_cmd(["finish", "--sync-context"])
    assert written_modules == ["harbor", "harbor/cli", "tests"]


def test_changed_scope_consistency_across_finish_docs_module_seal_and_stale(monkeypatch):
    _patch_finish_basics(monkeypatch)
    report = _status_report_for_paths("harbor/core/sample.py", "tests/test_sample.py")
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: report)
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor", "harbor/core", "tests"])

    seen = {
        "finish_docs": [],
        "finish_seal": [],
        "finish_stale": [],
        "docs": [],
        "seal": [],
        "stale": [],
        "stale_ci": [],
    }
    current = {"command": ""}

    def _generate(self, module):
        target = "finish_docs" if current["command"] == "finish" else "docs"
        seen[target].append(module)
        return f"# {module}"

    def _write_readme(self, module, md, force=False):
        return []

    def _context(module):
        return {"module": module, "key_files": [f"{module}/x.py"], "contracts": []}

    def _write_capsule(context):
        module = context.get("module", "")
        target = "finish_seal" if current["command"] == "finish" else "seal"
        seen[target].append(module)
        return SimpleNamespace(canonical_paths=[], exported_paths=[])

    def _check_stale(module):
        target = "finish_stale" if current["command"] == "finish" else ("stale_ci" if current["command"] == "stale_ci" else "stale")
        seen[target].append(module)
        return _view_summary(module)

    monkeypatch.setattr(cli_main.L2Generator, "generate", _generate)
    monkeypatch.setattr(cli_main.L2Generator, "write", _write_readme)
    monkeypatch.setattr(cli_main, "collect_module_context", _context)
    monkeypatch.setattr(cli_main, "write_module_capsule", _write_capsule)
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", _check_stale)

    current["command"] = "finish"
    _ = run_cmd(["finish", "--sync-context"])
    current["command"] = "docs"
    _ = run_cmd(["docs", "--changed", "--write"])
    current["command"] = "seal"
    _ = run_cmd(["module", "seal", "--changed", "--write"])
    current["command"] = "stale"
    _ = run_cmd(["stale", "--changed"])
    current["command"] = "stale_ci"
    code, out = run_cmd_with_exit_code(["stale", "--ci", "--format", "json"])

    payload = json.loads(out)
    expected = ["harbor", "harbor/core", "tests"]
    assert code == 0
    assert payload["status"] == "pass"
    assert seen["finish_docs"] == expected
    assert seen["finish_seal"] == expected
    assert seen["finish_stale"] == expected
    assert seen["docs"] == expected
    assert seen["seal"] == expected
    assert seen["stale"] == expected
    assert seen["stale_ci"] == expected


def test_finish_sync_context_reports_residual_stale_guidance(monkeypatch):
    _patch_finish_basics(monkeypatch)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _status_report_for_paths("harbor/core/sample.py"))
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor", "harbor/core"])
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# {module}")
    monkeypatch.setattr(cli_main.L2Generator, "write", lambda self, module, md, force=False: [])
    monkeypatch.setattr(
        cli_main,
        "collect_module_context",
        lambda module: {"module": module, "key_files": [f"{module}/x.py"], "contracts": []},
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_capsule",
        lambda context: SimpleNamespace(canonical_paths=[], exported_paths=[]),
    )
    monkeypatch.setattr(
        cli_main,
        "check_module_derived_views_stale",
        lambda module: _view_summary(module, l2="stale", capsule="stale"),
    )

    out = run_cmd(["finish", "--sync-context"])
    assert "Residual stale detected after sync" in out
    assert "- harbor | L2 README | stale: l2 reason" in out
    assert "- harbor/core | Module Capsule | stale: capsule reason" in out
    assert "Deterministic repair guidance:" in out
    assert "harbor docs --module harbor --write" in out
    assert "harbor module seal harbor/core --write" in out


def test_finish_sync_context_warns_on_generator_integrity_changes(monkeypatch):
    _patch_finish_basics(monkeypatch)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _status_report_for_paths("harbor/core/l2.py"))
    monkeypatch.setattr(cli_main, "collect_all_indexed_modules", lambda: ["harbor", "harbor/core"])
    monkeypatch.setattr(cli_main.L2Generator, "generate", lambda self, module: f"# {module}")
    monkeypatch.setattr(cli_main.L2Generator, "write", lambda self, module, md, force=False: [])
    monkeypatch.setattr(
        cli_main,
        "collect_module_context",
        lambda module: {"module": module, "key_files": [f"{module}/x.py"], "contracts": []},
    )
    monkeypatch.setattr(
        cli_main,
        "write_module_capsule",
        lambda context: SimpleNamespace(canonical_paths=[], exported_paths=[]),
    )
    monkeypatch.setattr(cli_main, "check_module_derived_views_stale", lambda module: _view_summary(module))

    out = run_cmd(["finish", "--sync-context"])
    assert "Changed generator/integrity files detected." in out
    assert "- harbor/core/l2.py" in out
    assert "Changed-scope sync may be insufficient. Consider:" in out
    assert "harbor docs --all --write" in out
    assert "harbor module seal --all --write" in out


@pytest.mark.parametrize(
    ("changed_path", "expected_module"),
    [
        ("tests/test_sample.py", "tests"),
        ("harbor/core/sample.py", "harbor/core"),
    ],
)
def test_finish_sync_context_then_stale_ci_pass_for_changed_scope(tmp_path: Path, monkeypatch, changed_path: str, expected_module: str):
    monkeypatch.chdir(tmp_path)
    _write_sample_repo(tmp_path)
    _patch_finish_basics(monkeypatch)
    report = _status_report_for_paths(changed_path)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: report)

    finish_out = run_cmd(["finish", "--sync-context"])
    code, stale_out = run_cmd_with_exit_code(["stale", "--ci", "--format", "json"])
    payload = json.loads(stale_out)

    assert expected_module in finish_out
    assert "Changed-scope stale self-check passed" in finish_out
    assert code == 0
    assert payload["status"] == "pass"
    assert payload["summary"]["ci_failures"] == 0
