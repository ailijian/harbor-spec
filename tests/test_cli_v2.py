import json
import sys
from io import StringIO
from contextlib import redirect_stdout
from types import SimpleNamespace
from pathlib import Path
import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.diary import DiaryEntry


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


@pytest.fixture(autouse=True)
def _isolate_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def _clean_status_report():
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


def test_status_alias_st():
    out1 = run_cmd(["status"])
    out2 = run_cmd(["st"])
    assert out1.strip()
    assert out2.strip()
    assert ("Harbor Context Status" in out1) or ("No changes detected." in out1)
    assert ("Harbor Context Status" in out2) or ("No changes detected." in out2)
    assert out1.splitlines()[0] == out2.splitlines()[0]


def test_ddt_validate_maps_to_check_fast():
    out1 = run_cmd(["ddt", "validate"])
    out2 = run_cmd(["check", "--fast"])
    assert "Harbor Check Report:" in out1
    assert "Harbor Check Report:" in out2
    assert "[DDT] Validation:" in out1
    assert "[DDT] Validation:" in out2


def test_diary_export_maps_to_log_export():
    out1 = run_cmd(["diary", "export", "--visibility", "repo"])
    out2 = run_cmd(["log", "--export", "--visibility", "repo"])
    assert "# Harbor Diary Export" in out1
    assert "# Harbor Diary Export" in out2


def test_log_message_keeps_json_first_line_and_prints_canonical_target(monkeypatch):
    def _fake_log(self, **kwargs):
        return DiaryEntry(
            ver=1,
            ts="2026-05-12T09:00:00Z",
            author="tester",
            type="feature",
            importance="normal",
            visibility="repo",
            summary="hello",
        )

    monkeypatch.setattr(cli_main.DiaryManager, "log", _fake_log)
    monkeypatch.setattr(
        cli_main.DiaryManager,
        "_current_file_path",
        lambda self, ts_iso: Path(".harbor/diary/2026-05.jsonl"),
    )

    out = run_cmd(["log", "-m", "hello", "--visibility", "repo"])
    lines = [line for line in out.splitlines() if line.strip()]

    assert len(lines) >= 3
    assert lines[0].startswith('{"ver": 1,')
    assert lines[1] == "Diary write target: .harbor/diary/2026-05.jsonl"
    assert "Canonical write: .harbor/diary/YYYY-MM.jsonl" in lines[2]


def test_decorate_maps_to_adopt_dry_run():
    out1 = run_cmd(["adopt", "harbor", "--dry-run"])
    out2 = run_cmd(["decorate", "harbor", "--dry-run"])
    assert "Decorate Candidates" in out1
    assert "Decorate Candidates" in out2


def test_gen_l2_maps_to_docs():
    out1 = run_cmd(["gen", "l2", "--module", "harbor/core"])
    out2 = run_cmd(["docs", "--module", "harbor/core"])
    assert "# Module:" in out1
    assert "# Module:" in out2


def test_start_command_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _clean_status_report())
    out = run_cmd(["start"])
    assert "Harbor Start:" in out
    assert "No Harbor changes detected. You can start AI coding." in out


def test_checkpoint_command_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _clean_status_report())
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _empty_validation_report())
    out = run_cmd(["checkpoint"])
    assert "Harbor Checkpoint:" in out
    assert "Harbor Check Report:" in out
    assert "Contract Impact 分类：" not in out


def test_checkpoint_ci_json_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _clean_status_report())
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _empty_validation_report())
    out = run_cmd(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    assert payload["command"] == "checkpoint"
    assert payload["ci"] is True
    assert payload["status"] == "pass"
    assert payload["writes_files"] is False


def test_finish_command_recognized(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _clean_status_report())
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _empty_validation_report())
    monkeypatch.setattr(
        cli_main,
        "resolve_provider",
        lambda: SimpleNamespace(name="mock", model="mock-model"),
    )
    out = run_cmd(["finish"])
    assert "Harbor Finish:" in out
    assert "Finish Summary:" in out
    assert "- Blocking failures:" in out
    assert "Next steps:" in out
    assert "harbor checkpoint --ci --format json --advice basic" in out


def test_accept_maps_to_lock_logic(monkeypatch):
    class FakeDB:
        db_path = SimpleNamespace(as_posix=lambda: ".harbor/cache/harbor.db")

        @staticmethod
        def get_all_files():
            return []

    class FakeBuilder:
        def __init__(self, code_roots=None, cache_dir=None):
            self.db = FakeDB()

        @staticmethod
        def iter_build(incremental=True):
            return iter([SimpleNamespace(total=0, status="scanning", path="fake.py", items_count=0)])

    monkeypatch.setattr(cli_main, "IndexBuilder", FakeBuilder)
    out = run_cmd(["accept"])
    assert "scanned=0 updated=0 skipped=0 items=0" in out
    assert "Accepted current Harbor baseline." in out


def test_commit_alias_unchanged_maps_to_lock(monkeypatch):
    calls = {"iter_build": 0}

    class FakeDB:
        db_path = SimpleNamespace(as_posix=lambda: ".harbor/cache/harbor.db")

        @staticmethod
        def get_all_files():
            return []

    class FakeBuilder:
        def __init__(self, code_roots=None, cache_dir=None):
            self.db = FakeDB()

        @staticmethod
        def iter_build(incremental=True):
            calls["iter_build"] += 1
            return iter([SimpleNamespace(total=0, status="scanning", path="fake.py", items_count=0)])

    monkeypatch.setattr(cli_main, "IndexBuilder", FakeBuilder)
    run_cmd(["commit"])
    assert calls["iter_build"] == 1


def test_checkpoint_does_not_trigger_semantic_audit(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _clean_status_report())
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _empty_validation_report())

    def _should_not_call(*args, **kwargs):
        raise AssertionError("semantic audit path should not run in checkpoint")

    monkeypatch.setattr(cli_main, "resolve_provider", _should_not_call)
    monkeypatch.setattr(cli_main.SemanticGuard, "audit", _should_not_call)
    out = run_cmd(["checkpoint"])
    assert "Harbor Checkpoint:" in out
    assert "Harbor Check Report:" in out


def test_checkpoint_prints_contract_impact_summary_when_dirty(monkeypatch):
    dirty = SimpleNamespace(
        counts={
            "drift": 0,
            "contract_changed": 1,
            "modified": 0,
            "contract_gap": 0,
            "skipped_no_contract": 0,
            "contract_parse_error": 0,
            "untracked": 0,
            "missing": 0,
        },
        drift=[],
        contract_changed=[
            SimpleNamespace(
                id="harbor.core.stale.stale_report_to_dict",
                name="stale_report_to_dict",
                file_path="harbor/core/stale.py",
                change_type="Contract Changed",
                details="Contract updated",
            )
        ],
        modified=[],
        contract_gap=[],
        skipped_no_contract=[],
        contract_parse_error=[],
        untracked=[],
        missing=[],
    )
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: dirty)
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _empty_validation_report())
    out = run_cmd(["checkpoint"])
    assert "Contract Impact 分类：" in out
    assert "cli_json_output" in out


def test_finish_does_not_auto_run_docs_log_lock(monkeypatch):
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _clean_status_report())
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _empty_validation_report())
    monkeypatch.setattr(
        cli_main,
        "resolve_provider",
        lambda: SimpleNamespace(name="mock", model="mock-model"),
    )

    calls = {"docs": 0, "log": 0, "lock": 0}

    def _docs_call(*args, **kwargs):
        calls["docs"] += 1

    def _log_call(*args, **kwargs):
        calls["log"] += 1

    def _lock_call(*args, **kwargs):
        calls["lock"] += 1
        return iter([])

    monkeypatch.setattr(cli_main.L2Generator, "generate", _docs_call)
    monkeypatch.setattr(cli_main.DiaryManager, "log", _log_call)
    monkeypatch.setattr(cli_main.DiaryManager, "export_markdown", _log_call)
    monkeypatch.setattr(cli_main.IndexBuilder, "iter_build", _lock_call)

    run_cmd(["finish"])
    assert calls["docs"] == 0
    assert calls["log"] == 0
    assert calls["lock"] == 0


def test_status_skipped_no_contract_default_summary(monkeypatch):
    rep = _clean_status_report()
    rep.counts["skipped_no_contract"] = 2
    rep.skipped_no_contract = [
        SimpleNamespace(id="harbor.core.a._helper", details="No contract required", file_path="harbor/core/a.py"),
        SimpleNamespace(id="harbor.core.b._helper", details="No contract required", file_path="harbor/core/b.py"),
    ]
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)

    out = run_cmd(["status"])
    assert "Skipped No Contract: 2 targets skipped (non-blocking)" in out
    assert "Reason: no contract required for these targets." in out
    assert "Use --verbose to view details." in out
    assert "harbor.core.a._helper" not in out
    assert "harbor.core.b._helper" not in out


def test_status_skipped_no_contract_verbose_lists_targets(monkeypatch):
    rep = _clean_status_report()
    rep.counts["skipped_no_contract"] = 2
    rep.skipped_no_contract = [
        SimpleNamespace(id="harbor.core.a._helper", details="No contract required", file_path="harbor/core/a.py"),
        SimpleNamespace(id="harbor.core.b._helper", details="No contract required", file_path="harbor/core/b.py"),
    ]
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: rep)

    out = run_cmd(["status", "--verbose"])
    assert "harbor.core.a._helper" in out
    assert "harbor.core.b._helper" in out


def test_check_ddt_baseline_missing_default_aggregated(monkeypatch):
    binding1 = SimpleNamespace(
        func_id="harbor.core.sync.SyncEngine.check_status",
        l3_version=1,
        strategy="strict",
        test_name="test_sync_status",
        file_path="tests/test_sync.py",
    )
    binding2 = SimpleNamespace(
        func_id="harbor.core.ci.format_checkpoint_ci_result",
        l3_version=2,
        strategy="strict",
        test_name="test_ci_format",
        file_path="tests/test_ci.py",
    )
    advisory = [
        SimpleNamespace(category="ddt_version_baseline_missing", binding=binding1, message="msg"),
        SimpleNamespace(category="ddt_version_baseline_missing", binding=binding2, message="msg"),
    ]
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [binding1, binding2])
    monkeypatch.setattr(
        cli_main.DDTValidator,
        "validate",
        lambda self, bindings: SimpleNamespace(valid=[binding1, binding2], violations=[], advisory=advisory),
    )

    out = run_cmd(["check", "--fast"])
    assert "baseline-missing: 2 strict DDT bindings" in out
    assert out.count("Strict DDT binding is structurally valid") == 1
    assert "Use --verbose to view bindings." in out
    assert "func_id=harbor.core.sync.SyncEngine.check_status" not in out


def test_check_ddt_baseline_missing_verbose_lists_bindings(monkeypatch):
    binding1 = SimpleNamespace(
        func_id="harbor.core.sync.SyncEngine.check_status",
        l3_version=1,
        strategy="strict",
        test_name="test_sync_status",
        file_path="tests/test_sync.py",
    )
    binding2 = SimpleNamespace(
        func_id="harbor.core.ci.format_checkpoint_ci_result",
        l3_version=2,
        strategy="strict",
        test_name="test_ci_format",
        file_path="tests/test_ci.py",
    )
    advisory = [
        SimpleNamespace(category="ddt_version_baseline_missing", binding=binding1, message="msg"),
        SimpleNamespace(category="ddt_version_baseline_missing", binding=binding2, message="msg"),
    ]
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [binding1, binding2])
    monkeypatch.setattr(
        cli_main.DDTValidator,
        "validate",
        lambda self, bindings: SimpleNamespace(valid=[binding1, binding2], violations=[], advisory=advisory),
    )

    out = run_cmd(["check", "--fast", "--verbose"])
    assert "func_id=harbor.core.sync.SyncEngine.check_status" in out
    assert "func_id=harbor.core.ci.format_checkpoint_ci_result" in out


def test_checkpoint_ci_json_advisory_unchanged_with_advice_modes(monkeypatch):
    binding = SimpleNamespace(
        func_id="harbor.core.sync.SyncEngine.check_status",
        file_path="harbor/core/sync.py",
        l3_version=1,
        strategy="strict",
        test_name="test_sync",
    )
    binding2 = SimpleNamespace(
        func_id="harbor.core.ci.format_checkpoint_ci_result",
        file_path="harbor/core/ci.py",
        l3_version=2,
        strategy="strict",
        test_name="test_ci",
    )
    advisory = [
        SimpleNamespace(category="ddt_version_baseline_missing", binding=binding, message="m1", suggested_action="s1"),
        SimpleNamespace(category="ddt_version_baseline_missing", binding=binding2, message="m2", suggested_action="s2"),
    ]
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _clean_status_report())
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(
        cli_main.DDTValidator,
        "validate",
        lambda self, bindings: SimpleNamespace(valid=[], violations=[], advisory=advisory, counts={"valid": 0, "violations": 0, "advisory": 2}),
    )

    out_basic = run_cmd(["checkpoint", "--ci", "--format", "json", "--advice", "basic"])
    payload_basic = json.loads(out_basic)
    assert len(payload_basic["advisory"]) == 2
    assert all(item["category"] == "ddt_version_baseline_missing" for item in payload_basic["advisory"])
    assert all("guidance" in item for item in payload_basic["advisory"])

    out_off = run_cmd(["checkpoint", "--ci", "--format", "json", "--advice", "off"])
    payload_off = json.loads(out_off)
    assert len(payload_off["advisory"]) == 2
    assert all(item["category"] == "ddt_version_baseline_missing" for item in payload_off["advisory"])
    assert all("guidance" not in item for item in payload_off["advisory"])
