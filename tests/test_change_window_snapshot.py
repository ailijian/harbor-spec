import json
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.cli.main as cli_main
from harbor.cli.main import main
from harbor.core.change_window import (
    change_window_dir,
    get_latest_change_window,
    list_change_windows,
    write_change_window_snapshot,
)
from harbor.core.contract_impact import ContractImpactLevel, ContractImpactReport


@pytest.fixture(autouse=True)
def _stub_checkpoint_baseline_artifact(monkeypatch):
    monkeypatch.setattr(
        cli_main,
        "load_checkpoint_baseline_artifact",
        lambda *args, **kwargs: {
            "schema_version": "1.0",
            "kind": "accepted_checkpoint_baseline",
            "accepted_at": "2026-05-12T00:00:00Z",
            "accepted_by": "harbor accept",
            "harbor_version": "1.4.1",
            "baseline": {"items": []},
        },
    )


def _run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return completed.stdout.strip()


def _init_git_repo(repo_root: Path) -> None:
    _run_git(repo_root, "init")
    _run_git(repo_root, "config", "user.email", "tests@example.com")
    _run_git(repo_root, "config", "user.name", "Harbor Tests")
    (repo_root / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _run_git(repo_root, "add", "tracked.txt")
    _run_git(repo_root, "commit", "-m", "init")


def _run_cli(argv):
    out = StringIO()
    err = StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        sys.argv = ["harbor"] + argv
        try:
            main()
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def _read_runtime_diagnostics(repo_root: Path):
    path = repo_root / ".harbor" / "state" / "change-window-diagnostics.jsonl"
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _status_entry(func_id: str, file_path: str, details: str):
    return SimpleNamespace(id=func_id, file_path=file_path, details=details)


def _status_report(
    *,
    drift=None,
    modified=None,
    contract_changed=None,
    contract_gap=None,
    skipped_no_contract=None,
    contract_parse_error=None,
    unsupported_syntax_advisory=None,
    untracked=None,
    missing=None,
):
    drift = list(drift or [])
    modified = list(modified or [])
    contract_changed = list(contract_changed or [])
    contract_gap = list(contract_gap or [])
    skipped_no_contract = list(skipped_no_contract or [])
    contract_parse_error = list(contract_parse_error or [])
    unsupported_syntax_advisory = list(unsupported_syntax_advisory or [])
    untracked = list(untracked or [])
    missing = list(missing or [])
    return SimpleNamespace(
        drift=drift,
        modified=modified,
        contract_changed=contract_changed,
        contract_gap=contract_gap,
        skipped_no_contract=skipped_no_contract,
        contract_parse_error=contract_parse_error,
        unsupported_syntax_advisory=unsupported_syntax_advisory,
        untracked=untracked,
        missing=missing,
        counts={
            "drift": len(drift),
            "modified": len(modified),
            "contract_changed": len(contract_changed),
            "contract_gap": len(contract_gap),
            "skipped_no_contract": len(skipped_no_contract),
            "contract_parse_error": len(contract_parse_error),
            "unsupported_syntax_advisory": len(unsupported_syntax_advisory),
            "untracked": len(untracked),
            "missing": len(missing),
        },
    )


def _ddt_report(*, violations=None, advisory=None):
    violations = list(violations or [])
    advisory = list(advisory or [])
    return SimpleNamespace(
        valid=[],
        violations=violations,
        advisory=advisory,
        counts={"valid": 0, "violations": len(violations), "advisory": len(advisory)},
    )


def _contract_report():
    return ContractImpactReport(
        level=ContractImpactLevel.NO_CONTRACT_IMPACT,
        categories=[],
        findings=[],
        summary_counts={
            ContractImpactLevel.NO_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value: 0,
            ContractImpactLevel.UNKNOWN.value: 0,
        },
        notable_findings=[],
    )


class _FakeDDTScanner:
    def scan_tests(self):
        return []


class _FakeDDTValidator:
    def validate(self, bindings):
        return _ddt_report()


class _FakeSyncEngine:
    def __init__(self, report):
        self._report = report

    def check_status(self, baseline_snapshot=None, baseline_source="runtime_cache"):
        return self._report


def _configure_finish_cli(monkeypatch, tmp_path: Path, *, status_report=None):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")
    report = status_report or _status_report()
    monkeypatch.setattr(cli_main, "SyncEngine", lambda: _FakeSyncEngine(report))
    monkeypatch.setattr(cli_main, "DDTScanner", _FakeDDTScanner)
    monkeypatch.setattr(cli_main, "DDTValidator", _FakeDDTValidator)
    monkeypatch.setattr(cli_main, "resolve_provider", lambda: SimpleNamespace(name="mock", model="mock-model"))


def _configure_accept_cli(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")

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
            return iter(
                [
                    SimpleNamespace(total=1, status="scanning", path="fake.py", items_count=0),
                    SimpleNamespace(total=1, status="parsed", path="fake.py", items_count=1),
                ]
            )

    monkeypatch.setattr(cli_main, "IndexBuilder", FakeBuilder)


def test_write_snapshot_creates_json_with_required_schema(tmp_path: Path):
    _init_git_repo(tmp_path)
    (tmp_path / "tracked.txt").write_text("v2\n", encoding="utf-8")
    (tmp_path / "new.txt").write_text("new\n", encoding="utf-8")

    target = write_change_window_snapshot(
        "checkpoint",
        repo_root=tmp_path,
        summary={"status": "pass", "counts": {"ci_failures": 0}},
        validation={"checkpoint": {"status": "pass"}},
    )

    assert target.parent == change_window_dir(tmp_path)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["event"] == "checkpoint"
    assert payload["timestamp"].endswith("Z")
    assert "git_head" in payload
    assert "workspace_dirty" in payload
    assert "changed_files" in payload
    assert "summary" in payload
    assert "validation" in payload
    assert "notes" in payload
    assert payload["workspace_dirty"] is True
    assert any(item["path"] == "tracked.txt" and item["status"] == "M" for item in payload["changed_files"])
    assert any(item["path"] == "new.txt" and item["status"] == "??" for item in payload["changed_files"])


def test_list_change_windows_sorts_newest_first_and_get_latest_filters_event(tmp_path: Path):
    base = datetime(2026, 5, 11, 20, 30, tzinfo=timezone.utc)
    write_change_window_snapshot(
        "checkpoint",
        repo_root=tmp_path,
        timestamp=base,
        summary={"status": "pass"},
        git_head="a1",
        workspace_dirty=False,
        changed_files=[],
    )
    write_change_window_snapshot(
        "accept",
        repo_root=tmp_path,
        timestamp=base + timedelta(minutes=5),
        summary={"accepted": True},
        git_head="a2",
        workspace_dirty=False,
        changed_files=[],
    )
    write_change_window_snapshot(
        "checkpoint",
        repo_root=tmp_path,
        timestamp=base + timedelta(minutes=10),
        summary={"status": "fail"},
        git_head="a3",
        workspace_dirty=True,
        changed_files=[{"path": "harbor/core/ci.py", "status": "M"}],
    )

    snapshots = list_change_windows(repo_root=tmp_path)
    assert [item.event for item in snapshots] == ["checkpoint", "accept", "checkpoint"]
    latest_checkpoint = get_latest_change_window("checkpoint", repo_root=tmp_path)
    assert latest_checkpoint is not None
    assert latest_checkpoint.summary["status"] == "fail"
    assert latest_checkpoint.timestamp == "2026-05-11T20:40:00Z"


def test_retention_keeps_latest_fifty_snapshots(tmp_path: Path):
    base = datetime(2026, 5, 11, 20, 0, tzinfo=timezone.utc)
    for index in range(55):
        write_change_window_snapshot(
            "checkpoint",
            repo_root=tmp_path,
            timestamp=base + timedelta(minutes=index),
            summary={"index": index},
            git_head=f"sha-{index}",
            workspace_dirty=bool(index % 2),
            changed_files=[],
        )

    snapshots = list_change_windows(repo_root=tmp_path)
    assert len(snapshots) == 50
    assert snapshots[0].summary["index"] == 54
    assert snapshots[-1].summary["index"] == 5


def test_bad_json_snapshot_is_skipped_with_warning(tmp_path: Path):
    target_dir = change_window_dir(tmp_path)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "broken.json").write_text("{not-json", encoding="utf-8")
    write_change_window_snapshot(
        "finish",
        repo_root=tmp_path,
        git_head="sha",
        workspace_dirty=False,
        changed_files=[],
        summary={"sync_context": False},
    )

    with pytest.warns(RuntimeWarning, match="Skipping invalid change window snapshot"):
        snapshots = list_change_windows(repo_root=tmp_path)

    assert len(snapshots) == 1
    assert snapshots[0].event == "finish"


def test_snapshot_does_not_store_file_content_or_diff_body(tmp_path: Path):
    _init_git_repo(tmp_path)
    secret_body = "VERY_SECRET_BODY"
    diff_body = "diff --git a/tracked.txt b/tracked.txt"
    (tmp_path / "tracked.txt").write_text(secret_body + "\n", encoding="utf-8")

    target = write_change_window_snapshot(
        "checkpoint",
        repo_root=tmp_path,
        summary={"status": "pass"},
        validation={"note": "git-status-only"},
    )

    rendered = target.read_text(encoding="utf-8")
    assert "VERY_SECRET_BODY" not in rendered
    assert diff_body not in rendered
    payload = json.loads(rendered)
    assert payload["changed_files"] == [{"path": "tracked.txt", "status": "M"}]


def test_checkpoint_ci_snapshot_write_failure_does_not_change_exit_code(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")
    monkeypatch.setenv("HARBOR_SECRET_TOKEN", "ULTRA_SECRET_TOKEN")
    status = _status_report(missing=[_status_entry("harbor.core.foo.gone", "harbor/core/foo.py", "removed")])

    class _FakeSyncEngine:
        def check_status(self, baseline_snapshot=None, baseline_source="runtime_cache"):
            return status

    class _FakeDDTScanner:
        def scan_tests(self):
            return []

    class _FakeDDTValidator:
        def validate(self, bindings):
            return _ddt_report()

    monkeypatch.setattr(cli_main, "SyncEngine", _FakeSyncEngine)
    monkeypatch.setattr(cli_main, "DDTScanner", _FakeDDTScanner)
    monkeypatch.setattr(cli_main, "DDTValidator", _FakeDDTValidator)
    monkeypatch.setattr(cli_main, "build_contract_impact_report", lambda records: _contract_report())
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    code, out, _ = _run_cli(["checkpoint", "--ci"])
    diagnostics = _read_runtime_diagnostics(tmp_path)

    assert code == 1
    assert "missing_function" in out
    assert diagnostics
    assert diagnostics[-1]["event"] == "checkpoint"
    assert diagnostics[-1]["error_type"] == "RuntimeError"
    assert diagnostics[-1]["error_message"] == "boom"
    assert diagnostics[-1]["command_context"] == "checkpoint"
    assert diagnostics[-1]["cwd"] == tmp_path.as_posix()
    assert diagnostics[-1]["intended_state_dir"].endswith("/.harbor/state/change-windows")
    rendered = json.dumps(diagnostics[-1], ensure_ascii=False)
    assert "ULTRA_SECRET_TOKEN" not in rendered
    assert "VERY_SECRET_BODY" not in rendered
    assert "diff --git" not in rendered


def test_checkpoint_ci_writes_snapshot_without_changing_pass_semantics(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")

    monkeypatch.setattr(cli_main, "SyncEngine", lambda: _FakeSyncEngine(_status_report()))
    monkeypatch.setattr(cli_main, "DDTScanner", _FakeDDTScanner)
    monkeypatch.setattr(cli_main, "DDTValidator", _FakeDDTValidator)
    monkeypatch.setattr(cli_main, "build_contract_impact_report", lambda records: _contract_report())

    code, out, _ = _run_cli(["checkpoint", "--ci", "--format", "json"])
    payload = json.loads(out)
    snapshots = list_change_windows(repo_root=tmp_path)

    assert code == 0
    assert payload["status"] == "pass"
    assert len(snapshots) == 1
    assert snapshots[0].event == "checkpoint"
    assert snapshots[0].summary["status"] == "pass"


def test_finish_writes_finish_snapshot_and_can_be_read(monkeypatch, tmp_path: Path):
    _configure_finish_cli(monkeypatch, tmp_path)

    code, out, _ = _run_cli(["finish"])
    latest = get_latest_change_window("finish", repo_root=tmp_path)

    assert code == 0
    assert "Harbor Finish:" in out
    assert latest is not None
    assert latest.event == "finish"
    assert latest.summary["sync_context"] is False
    assert latest.validation["command"] == "finish"
    json.dumps(latest.summary, ensure_ascii=False)
    assert list_change_windows(repo_root=tmp_path)[0].event == "finish"


def test_finish_sync_context_writes_finish_snapshot_and_can_be_read(monkeypatch, tmp_path: Path):
    _configure_finish_cli(monkeypatch, tmp_path)

    code, out, _ = _run_cli(["finish", "--sync-context"])
    latest = get_latest_change_window("finish", repo_root=tmp_path)

    assert code == 0
    assert "Context Sync:" in out
    assert latest is not None
    assert latest.event == "finish"
    assert latest.summary["sync_context"] is True
    assert latest.validation["sync_context"] is True


def test_accept_writes_accept_snapshot_and_can_be_read(monkeypatch, tmp_path: Path):
    _configure_accept_cli(monkeypatch, tmp_path)

    code, out, _ = _run_cli(["accept"])
    latest = get_latest_change_window("accept", repo_root=tmp_path)

    assert code == 0
    assert latest is not None
    assert latest.event == "accept"
    assert latest.summary["accepted"] is True
    assert latest.validation["command"] == "accept"
    assert "accepted" in json.dumps(latest.summary, ensure_ascii=False)
    assert "Accepted current Harbor checkpoint baseline artifact." in out


def test_finish_snapshot_write_failure_does_not_change_exit_code(monkeypatch, tmp_path: Path):
    _configure_finish_cli(monkeypatch, tmp_path)
    monkeypatch.setenv("HARBOR_SECRET_TOKEN", "ULTRA_SECRET_TOKEN")
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    code, out, _ = _run_cli(["finish"])
    diagnostics = _read_runtime_diagnostics(tmp_path)

    assert code == 0
    assert "Harbor Finish:" in out
    assert get_latest_change_window("finish", repo_root=tmp_path) is None
    assert diagnostics
    assert diagnostics[-1]["event"] == "finish"
    assert diagnostics[-1]["error_type"] == "RuntimeError"
    assert diagnostics[-1]["error_message"] == "boom"
    assert diagnostics[-1]["command_context"] == "finish"
    rendered = json.dumps(diagnostics[-1], ensure_ascii=False)
    assert "ULTRA_SECRET_TOKEN" not in rendered
    assert "VERY_SECRET_BODY" not in rendered
    assert "diff --git" not in rendered


def test_accept_snapshot_write_failure_does_not_change_exit_code(monkeypatch, tmp_path: Path):
    _configure_accept_cli(monkeypatch, tmp_path)
    monkeypatch.setenv("HARBOR_SECRET_TOKEN", "ULTRA_SECRET_TOKEN")
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    code, out, _ = _run_cli(["accept"])
    diagnostics = _read_runtime_diagnostics(tmp_path)

    assert code == 0
    assert "Accepted current Harbor checkpoint baseline artifact." in out
    assert get_latest_change_window("accept", repo_root=tmp_path) is None
    assert diagnostics
    assert diagnostics[-1]["event"] == "accept"
    assert diagnostics[-1]["error_type"] == "RuntimeError"
    assert diagnostics[-1]["error_message"] == "boom"
    assert diagnostics[-1]["command_context"] == "accept"
    rendered = json.dumps(diagnostics[-1], ensure_ascii=False)
    assert "ULTRA_SECRET_TOKEN" not in rendered
    assert "VERY_SECRET_BODY" not in rendered
    assert "diff --git" not in rendered


def test_accept_and_finish_invoke_snapshot_events(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")
    calls = []

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

    def _capture(event, **kwargs):
        calls.append((event, kwargs))
        return change_window_dir(tmp_path) / f"{event}.json"

    monkeypatch.setattr(cli_main, "IndexBuilder", FakeBuilder)
    monkeypatch.setattr(cli_main, "write_change_window_snapshot", _capture)
    monkeypatch.setattr(cli_main.SyncEngine, "check_status", lambda self: _status_report())
    monkeypatch.setattr(cli_main.DDTScanner, "scan_tests", lambda self: [])
    monkeypatch.setattr(cli_main.DDTValidator, "validate", lambda self, bindings: _ddt_report())
    monkeypatch.setattr(cli_main, "resolve_provider", lambda: SimpleNamespace(name="mock", model="mock-model"))

    accept_code, _, _ = _run_cli(["accept"])
    finish_code, _, _ = _run_cli(["finish"])

    assert accept_code == 0
    assert finish_code == 0
    assert [event for event, _ in calls] == ["accept", "finish"]
    assert calls[0][1]["summary"]["accepted"] is True
    assert calls[1][1]["summary"]["sync_context"] is False
