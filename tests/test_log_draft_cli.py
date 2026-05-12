import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pytest

import harbor.cli.main as cli_main
import harbor.core.log_draft as log_draft
from harbor.cli.main import main
from harbor.core.change_window import write_change_window_snapshot


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


@pytest.fixture(autouse=True)
def _isolate_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _write_snapshot(
    repo_root: Path,
    event: str,
    timestamp: datetime,
    *,
    changed_files=None,
    summary=None,
    validation=None,
) -> None:
    write_change_window_snapshot(
        event,
        repo_root=repo_root,
        timestamp=timestamp,
        git_head="abc123",
        workspace_dirty=bool(changed_files),
        changed_files=list(changed_files or []),
        summary=summary or {},
        validation=validation or {},
    )


def _write_report(repo_root: Path, relative_path: str, payload: dict) -> Path:
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return target


def run_cmd(argv):
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


def _seed_draft_evidence(repo_root: Path) -> None:
    base = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    _write_snapshot(
        repo_root,
        "accept",
        base,
        changed_files=[],
        summary={"accepted": True},
        validation={"command": "accept"},
    )
    _write_snapshot(
        repo_root,
        "checkpoint",
        base.replace(minute=5),
        changed_files=[
            {"path": "harbor/core/log_draft.py", "status": "M"},
            {"path": "tests/test_log_draft_cli.py", "status": "??"},
        ],
        summary={"status": "pass"},
        validation={"command": "checkpoint"},
    )
    _write_report(
        repo_root,
        ".harbor/reports/checkpoint-task-c.json",
        {"command": "checkpoint", "status": "pass", "writes_files": False},
    )


def test_log_draft_default_outputs_markdown_and_does_not_call_log_write(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    monkeypatch.setattr(cli_main.DiaryManager, "log", lambda self, **kwargs: (_ for _ in ()).throw(AssertionError("must not write diary")))

    code, out, err = run_cmd(["log", "draft"])

    assert code == 0
    assert "# Diary Draft" in out
    assert "## Suggested Diary Entry" in out
    assert "Next steps:" in out
    assert "harbor log write" in out
    assert "harbor log draft --save" in out
    assert "harbor log write --yes" in out
    assert "Latest draft cache updated:" in err
    assert (tmp_path / ".harbor" / "state" / "log" / "latest-draft.md").exists()
    assert (tmp_path / ".harbor" / "state" / "log" / "latest-draft.json").exists()
    assert not (tmp_path / ".harbor" / "diary").exists()


def test_log_draft_json_output_is_stable(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert err == ""
    assert payload["schema_version"] == "1.0"
    assert payload["kind"] == "diary_draft"
    assert set(payload.keys()) == {
        "affected_areas",
        "boundary_note",
        "boundary_source",
        "boundary_timestamp",
        "contract_impact",
        "draft_status",
        "evidence",
        "kind",
        "risks",
        "schema_version",
        "suggested_diary_entry",
        "summary",
        "validation",
        "why",
    }
    assert out.strip() == json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    assert "harbor log write --yes" not in out
    assert "harbor log draft --save" not in out


def test_log_draft_output_writes_reports_file_and_keeps_stdout(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {
            "git_head": "head123",
            "workspace_dirty": True,
            "changed_files": [{"path": "docs/task-c.md", "status": "M"}],
        },
    )

    code, out, err = run_cmd(["log", "draft", "--output", ".harbor/reports/draft.md"])

    assert code == 0
    assert "# Diary Draft" in out
    assert "Latest draft cache updated:" in err
    assert "Draft saved to: .harbor/reports/draft.md" in err
    assert (tmp_path / ".harbor" / "reports" / "draft.md").exists()
    assert not (tmp_path / ".harbor" / "diary").exists()


def test_log_draft_save_writes_timestamped_markdown_copy(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    monkeypatch.setattr(
        cli_main,
        "build_saved_diary_draft_output_path",
        lambda **kwargs: tmp_path / ".harbor" / "reports" / "log-draft-20260511-123456.md",
    )

    code, out, err = run_cmd(["log", "draft", "--save"])

    assert code == 0
    assert "# Diary Draft" in out
    assert "Draft saved to: .harbor/reports/log-draft-20260511-123456.md" in err
    assert (tmp_path / ".harbor" / "reports" / "log-draft-20260511-123456.md").exists()


def test_log_draft_save_json_writes_timestamped_json_copy_without_polluting_stdout(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    monkeypatch.setattr(
        cli_main,
        "build_saved_diary_draft_output_path",
        lambda **kwargs: tmp_path / ".harbor" / "reports" / "log-draft-20260511-123456.json",
    )

    code, out, err = run_cmd(["log", "draft", "--save", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert payload["kind"] == "diary_draft"
    assert err == ""
    assert (tmp_path / ".harbor" / "reports" / "log-draft-20260511-123456.json").exists()


def test_log_draft_output_path_takes_precedence_over_save(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    monkeypatch.setattr(
        cli_main,
        "build_saved_diary_draft_output_path",
        lambda **kwargs: tmp_path / ".harbor" / "reports" / "should-not-exist.md",
    )

    code, out, err = run_cmd(["log", "draft", "--save", "--output", ".harbor/reports/explicit.md"])

    assert code == 0
    assert "# Diary Draft" in out
    assert "Explicit output path takes precedence over --save: .harbor/reports/explicit.md" in err
    assert (tmp_path / ".harbor" / "reports" / "explicit.md").exists()
    assert not (tmp_path / ".harbor" / "reports" / "should-not-exist.md").exists()


def test_log_draft_output_rejects_diary_path(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--output", ".harbor/diary/2026-05.jsonl"])

    assert code == 1
    assert out == ""
    assert "Refusing to write diary draft under `.harbor/diary/**`" in err


def test_log_draft_since_last_accept_filters_to_post_accept_evidence(monkeypatch, tmp_path: Path):
    base = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    _write_snapshot(
        tmp_path,
        "checkpoint",
        base,
        changed_files=[{"path": "harbor/core/old.py", "status": "M"}],
        summary={"status": "pass"},
    )
    _write_snapshot(tmp_path, "accept", base.replace(minute=5), changed_files=[], summary={"accepted": True})
    _write_snapshot(
        tmp_path,
        "finish",
        base.replace(minute=10),
        changed_files=[{"path": "harbor/core/new.py", "status": "M"}],
        summary={"sync_context": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--since-last-accept", "--format", "json"])
    payload = json.loads(out)
    changed_paths = {item["path"] for item in payload["evidence"]["changed_files"]}

    assert code == 0
    assert err == ""
    assert "harbor/core/new.py" in changed_paths
    assert "harbor/core/old.py" not in changed_paths


def test_log_draft_default_json_prefers_last_log_marker_boundary(monkeypatch, tmp_path: Path):
    base = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    marker = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"last_log_at":"2026-05-11T12:20:00Z"}\n', encoding="utf-8")
    _write_snapshot(
        tmp_path,
        "checkpoint",
        base.replace(minute=10),
        changed_files=[{"path": "harbor/core/too-old.py", "status": "M"}],
        summary={"status": "pass"},
    )
    _write_snapshot(
        tmp_path,
        "finish",
        base.replace(minute=30),
        changed_files=[{"path": "harbor/core/fresh.py", "status": "M"}],
        summary={"sync_context": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--format", "json"])
    payload = json.loads(out)
    changed_paths = {item["path"] for item in payload["evidence"]["changed_files"]}

    assert code == 0
    assert err == ""
    assert payload["boundary_source"] == "last_log_marker"
    assert payload["boundary_timestamp"] == "2026-05-11T12:20:00Z"
    assert "using last log marker" in payload["boundary_note"]
    assert "harbor/core/fresh.py" in changed_paths
    assert "harbor/core/too-old.py" not in changed_paths


def test_log_draft_json_reports_invalid_marker_fallback_without_polluting_json(monkeypatch, tmp_path: Path):
    base = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    marker = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"last_snapshot":"2026-05-11T12:00:00Z"}\n', encoding="utf-8")
    _write_snapshot(tmp_path, "accept", base.replace(minute=5), changed_files=[], summary={"accepted": True})
    _write_snapshot(
        tmp_path,
        "finish",
        base.replace(minute=10),
        changed_files=[{"path": "harbor/core/post_accept.py", "status": "M"}],
        summary={"sync_context": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert payload["boundary_source"] == "latest_accept"
    assert "has only snapshot metadata and no parseable log timestamp" in payload["boundary_note"]
    assert "falling back to latest accept" in payload["boundary_note"]
    assert out.strip().startswith("{")
    assert err == ""


def test_log_draft_save_does_not_modify_existing_marker(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    marker = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"last_log_at":"2026-05-11T12:00:00Z","diary_path":".harbor/diary/2026-05.jsonl"}\n', encoding="utf-8")
    before = marker.read_text(encoding="utf-8")
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    monkeypatch.setattr(
        cli_main,
        "build_saved_diary_draft_output_path",
        lambda **kwargs: tmp_path / ".harbor" / "reports" / "log-draft-20260511-123456.md",
    )

    code, out, err = run_cmd(["log", "draft", "--save"])

    assert code == 0
    assert "# Diary Draft" in out
    assert "Draft saved to: .harbor/reports/log-draft-20260511-123456.md" in err
    assert marker.read_text(encoding="utf-8") == before


def test_log_draft_from_report_bad_json_returns_clear_error(monkeypatch, tmp_path: Path):
    bad = tmp_path / ".harbor" / "reports" / "broken.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("{bad-json", encoding="utf-8")
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--from-report", str(bad)])

    assert code == 1
    assert out == ""
    assert "Failed to parse JSON report" in err


def test_log_draft_cache_warning_does_not_fail_command(monkeypatch, tmp_path: Path):
    _seed_draft_evidence(tmp_path)
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    monkeypatch.setattr(
        cli_main,
        "write_latest_diary_draft_cache",
        lambda payload, **kwargs: {
            "markdown_path": None,
            "json_path": None,
            "markdown_path_display": ".harbor/state/log/latest-draft.md",
            "json_path_display": ".harbor/state/log/latest-draft.json",
            "warnings": ["disk full"],
        },
    )

    code, out, err = run_cmd(["log", "draft"])

    assert code == 0
    assert "# Diary Draft" in out
    assert "Latest draft cache warning: disk full" in err


def test_log_draft_reports_only_outputs_insufficient_evidence_without_write_hints(monkeypatch, tmp_path: Path):
    marker = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"last_log_at":"2026-05-11T12:20:00Z"}\n', encoding="utf-8")
    _write_report(
        tmp_path,
        ".harbor/reports/checkpoint-only.json",
        {"command": "checkpoint", "status": "pass", "writes_files": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft"])

    assert code == 0
    assert "No meaningful new change evidence was found" in out
    assert "No writable Diary Draft was generated." in out
    assert "Suggested Diary Entry" not in out
    assert "harbor log write" not in out
    assert "Latest draft cache updated:" not in err
    assert not (tmp_path / ".harbor" / "state" / "log" / "latest-draft.md").exists()
    assert not (tmp_path / ".harbor" / "state" / "log" / "latest-draft.json").exists()


def test_log_draft_diary_only_outputs_insufficient_evidence_without_write_hints(monkeypatch, tmp_path: Path):
    marker = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"last_log_at":"2026-05-11T12:20:00Z"}\n', encoding="utf-8")
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {
            "git_head": "head123",
            "workspace_dirty": True,
            "changed_files": [{"path": ".harbor/diary/2026-05.jsonl", "status": "M"}],
        },
    )

    code, out, err = run_cmd(["log", "draft"])

    assert code == 0
    assert "only diary file updates were detected" in out
    assert "No writable Diary Draft was generated." in out
    assert "Suggested Diary Entry" not in out
    assert "harbor log write" not in out
    assert err == ""


def test_log_draft_reports_only_json_is_pure_and_marks_insufficient_evidence(monkeypatch, tmp_path: Path):
    marker = tmp_path / ".harbor" / "state" / "log" / "last_log_marker.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"last_log_at":"2026-05-11T12:20:00Z"}\n', encoding="utf-8")
    _write_report(
        tmp_path,
        ".harbor/reports/checkpoint-only.json",
        {"command": "checkpoint", "status": "pass", "writes_files": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--format", "json"])
    payload = json.loads(out)

    assert code == 0
    assert err == ""
    assert payload["draft_status"] == "insufficient_evidence"
    assert payload["suggested_diary_entry"] == ""
    assert "No meaningful new change evidence was found since the last log marker." in payload["summary"]
    assert "auto-discovered reports remain supplementary only." in payload["summary"]


def test_log_draft_snapshot_only_still_outputs_writable_draft(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "checkpoint",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[],
        summary={"status": "pass"},
        validation={"checkpoint": "pass"},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft"])

    assert code == 0
    assert "## Suggested Diary Entry" in out
    assert "harbor log write" in out
    assert "Latest draft cache updated:" in err


def test_log_draft_from_report_still_generates_writable_draft(monkeypatch, tmp_path: Path):
    report = _write_report(
        tmp_path,
        ".harbor/reports/checkpoint-explicit.json",
        {"command": "checkpoint", "status": "pass", "writes_files": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    code, out, err = run_cmd(["log", "draft", "--from-report", str(report)])

    assert code == 0
    assert "## Suggested Diary Entry" in out
    assert "harbor log write" in out
    assert "Latest draft cache updated:" in err
