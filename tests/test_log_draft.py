import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import harbor.core.log_draft as log_draft
from harbor.core.change_window import change_window_dir, write_change_window_snapshot
from harbor.core.log_draft import (
    LogDraftError,
    build_diary_draft,
    build_saved_diary_draft_output_path,
    serialize_diary_draft,
    write_diary_draft_output,
    write_latest_diary_draft_cache,
)


def _write_report(repo_root: Path, relative_path: str, payload: dict) -> Path:
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return target


def _write_snapshot(
    repo_root: Path,
    event: str,
    timestamp: datetime,
    *,
    changed_files=None,
    summary=None,
    validation=None,
) -> Path:
    return write_change_window_snapshot(
        event,
        repo_root=repo_root,
        timestamp=timestamp,
        git_head="abc123",
        workspace_dirty=bool(changed_files),
        changed_files=list(changed_files or []),
        summary=summary or {},
        validation=validation or {},
    )


def test_build_diary_draft_collects_required_fields_and_evidence(monkeypatch, tmp_path: Path):
    base = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    secret_body = "VERY_SECRET_VALUE"
    (tmp_path / "tracked.txt").write_text(secret_body + "\n", encoding="utf-8")

    _write_snapshot(
        tmp_path,
        "accept",
        base,
        changed_files=[],
        summary={"accepted": True},
        validation={"command": "accept"},
    )
    _write_snapshot(
        tmp_path,
        "checkpoint",
        base + timedelta(minutes=5),
        changed_files=[
            {"path": "harbor/cli/main.py", "status": "M"},
            {"path": "tests/test_log_draft.py", "status": "??"},
            {"path": ".harbor/reports/checkpoint-task-c.json", "status": "M"},
        ],
        summary={"status": "pass"},
        validation={"command": "checkpoint"},
    )
    _write_snapshot(
        tmp_path,
        "finish",
        base + timedelta(minutes=10),
        changed_files=[{"path": "docs/task-c-notes.md", "status": "M"}],
        summary={"sync_context": False},
        validation={"command": "finish"},
    )
    _write_report(
        tmp_path,
        ".harbor/reports/checkpoint-task-c.json",
        {"command": "checkpoint", "status": "pass", "writes_files": False},
    )

    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {
            "git_head": "head123",
            "workspace_dirty": True,
            "changed_files": [{"path": "docs/release-task-c.md", "status": "M"}],
        },
    )

    payload = build_diary_draft(repo_root=tmp_path)
    rendered_json = serialize_diary_draft(payload, "json")
    rendered_markdown = serialize_diary_draft(payload, "markdown")

    assert payload["schema_version"] == "1.0"
    assert payload["kind"] == "diary_draft"
    assert payload["contract_impact"] == "yes"
    assert set(payload["validation"].keys()) == {"pytest", "checkpoint", "stale", "doctor"}
    assert payload["validation"]["checkpoint"] == "pass"
    assert payload["affected_areas"]["production_code"] == ["harbor/cli/main.py"]
    assert payload["affected_areas"]["tests"] == ["tests/test_log_draft.py"]
    assert payload["affected_areas"]["reports"] == [".harbor/reports/checkpoint-task-c.json"]
    assert "docs/task-c-notes.md" in payload["affected_areas"]["docs"]
    assert any(item["command"] == "checkpoint" for item in payload["evidence"]["reports"])
    assert any(item["event"] == "checkpoint" for item in payload["evidence"]["snapshots"])
    assert any(item["path"] == "docs/release-task-c.md" and item["status"] == "M" for item in payload["evidence"]["changed_files"])
    assert "VERY_SECRET_VALUE" not in rendered_json
    assert "VERY_SECRET_VALUE" not in rendered_markdown
    assert "diff --git" not in rendered_json
    assert "diff --git" not in rendered_markdown
    assert "# Diary Draft" in rendered_markdown
    assert "## Change Window Evidence" in rendered_markdown


def test_since_last_accept_filters_older_snapshots(monkeypatch, tmp_path: Path):
    base = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    _write_snapshot(
        tmp_path,
        "checkpoint",
        base,
        changed_files=[{"path": "harbor/core/old.py", "status": "M"}],
        summary={"status": "pass"},
    )
    _write_snapshot(
        tmp_path,
        "accept",
        base + timedelta(minutes=5),
        changed_files=[],
        summary={"accepted": True},
    )
    _write_snapshot(
        tmp_path,
        "finish",
        base + timedelta(minutes=10),
        changed_files=[{"path": "harbor/core/new.py", "status": "M"}],
        summary={"sync_context": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    payload = build_diary_draft(repo_root=tmp_path, since_last_accept=True)
    snapshot_timestamps = {item["timestamp"] for item in payload["evidence"]["snapshots"]}
    changed_paths = {item["path"] for item in payload["evidence"]["changed_files"]}

    assert "2026-05-11T12:00:00Z" not in snapshot_timestamps
    assert "harbor/core/old.py" not in changed_paths
    assert "harbor/core/new.py" in changed_paths
    assert "latest accept snapshot" in serialize_diary_draft(payload, "markdown")


def test_since_last_accept_falls_back_when_accept_snapshot_is_missing(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "checkpoint",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[{"path": "harbor/core/log_draft.py", "status": "M"}],
        summary={"status": "pass"},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": None, "workspace_dirty": False, "changed_files": []},
    )

    payload = build_diary_draft(repo_root=tmp_path, since_last_accept=True)

    assert any("Evidence boundary uncertain" in item for item in payload["risks"])
    assert any(item["event"] == "checkpoint" for item in payload["evidence"]["snapshots"])


def test_since_last_log_without_marker_falls_back_to_recent_snapshots(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "finish",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[{"path": "docs/task-c.md", "status": "M"}],
        summary={"sync_context": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": None, "workspace_dirty": False, "changed_files": []},
    )

    payload = build_diary_draft(repo_root=tmp_path, since_last_log=True)

    assert any("No last log marker found" in item for item in payload["risks"])
    assert any(item["event"] == "finish" for item in payload["evidence"]["snapshots"])


def test_build_diary_draft_classifies_diary_paths_separately(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "finish",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[
            {"path": ".harbor/diary/2026-05.jsonl", "status": "M"},
            {"path": ".harbor/state/log/latest-draft.json", "status": "M"},
        ],
        summary={"sync_context": False},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )

    payload = build_diary_draft(repo_root=tmp_path)
    rendered_markdown = serialize_diary_draft(payload, "markdown")

    assert payload["affected_areas"]["diary"] == [".harbor/diary/2026-05.jsonl"]
    assert payload["affected_areas"]["runtime_state"] == [".harbor/state/log/latest-draft.json"]
    assert payload["affected_areas"]["production_code"] == []
    assert any(
        item["path"] == ".harbor/diary/2026-05.jsonl" and item["status"] == "M"
        for item in payload["evidence"]["changed_files"]
    )
    assert "production code" not in payload["summary"]
    assert "diary" in payload["summary"]
    assert "- Module: diary, runtime state" in payload["suggested_diary_entry"]
    assert "- diary: .harbor/diary/2026-05.jsonl" in rendered_markdown


def test_bad_snapshot_json_is_skipped_without_crashing(monkeypatch, tmp_path: Path):
    target_dir = change_window_dir(tmp_path)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "broken.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": None, "workspace_dirty": False, "changed_files": []},
    )

    with pytest.warns(RuntimeWarning, match="Skipping invalid change window snapshot"):
        payload = build_diary_draft(repo_root=tmp_path)

    assert payload["summary"] == "No meaningful change window found for diary drafting."
    assert payload["contract_impact"] == "uncertain"


def test_from_report_requires_valid_json(monkeypatch, tmp_path: Path):
    broken = tmp_path / ".harbor" / "reports" / "broken.json"
    broken.parent.mkdir(parents=True, exist_ok=True)
    broken.write_text("{bad-json", encoding="utf-8")
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": None, "workspace_dirty": False, "changed_files": []},
    )

    with pytest.raises(LogDraftError, match="Failed to parse JSON report"):
        build_diary_draft(repo_root=tmp_path, from_report=broken)


def test_auto_discovery_skips_non_utf8_reports(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "checkpoint",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[{"path": "harbor/core/log_draft.py", "status": "M"}],
        summary={"status": "pass"},
    )
    utf16_report = tmp_path / ".harbor" / "reports" / "utf16-report.json"
    utf16_report.parent.mkdir(parents=True, exist_ok=True)
    utf16_report.write_text('{"command":"checkpoint","status":"pass"}', encoding="utf-16")
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": None, "workspace_dirty": False, "changed_files": []},
    )

    payload = build_diary_draft(repo_root=tmp_path)

    assert payload["summary"] != "No meaningful change window found for diary drafting."
    assert all(item["path"] != ".harbor/reports/utf16-report.json" for item in payload["evidence"]["reports"])


def test_write_diary_draft_output_writes_reports_and_rejects_diary_root(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "checkpoint",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[{"path": "harbor/core/log_draft.py", "status": "M"}],
        summary={"status": "pass"},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": None, "workspace_dirty": False, "changed_files": []},
    )
    payload = build_diary_draft(repo_root=tmp_path)

    target = write_diary_draft_output(
        payload,
        Path(".harbor/reports/log-draft-task-c.md"),
        output_format="markdown",
        repo_root=tmp_path,
    )

    assert target == (tmp_path / ".harbor" / "reports" / "log-draft-task-c.md").resolve()
    assert target.exists()
    assert "# Diary Draft" in target.read_text(encoding="utf-8")

    with pytest.raises(LogDraftError, match="Refusing to write diary draft under `.harbor/diary/\\*\\*`"):
        write_diary_draft_output(
            payload,
            Path(".harbor/diary/2026-05.jsonl"),
            output_format="json",
            repo_root=tmp_path,
        )


def test_write_latest_diary_draft_cache_writes_markdown_and_json_wrapper(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "checkpoint",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[{"path": "harbor/core/log_draft.py", "status": "M"}],
        summary={"status": "pass"},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    payload = build_diary_draft(repo_root=tmp_path)

    result = write_latest_diary_draft_cache(
        payload,
        repo_root=tmp_path,
        created_at=datetime(2026, 5, 11, 12, 30, tzinfo=timezone.utc),
    )

    markdown_path = tmp_path / ".harbor" / "state" / "log" / "latest-draft.md"
    json_path = tmp_path / ".harbor" / "state" / "log" / "latest-draft.json"
    wrapper = json.loads(json_path.read_text(encoding="utf-8"))

    assert result["warnings"] == []
    assert result["markdown_path"] == markdown_path
    assert result["json_path"] == json_path
    assert "# Diary Draft" in markdown_path.read_text(encoding="utf-8")
    assert wrapper["schema_version"] == "1.0"
    assert wrapper["kind"] == "diary_draft"
    assert wrapper["created_at"] == "2026-05-11T12:30:00Z"
    assert wrapper["source"] == "harbor log draft"
    assert wrapper["markdown_path"] == ".harbor/state/log/latest-draft.md"
    assert wrapper["draft"]["kind"] == "diary_draft"
    assert set(wrapper.keys()) == {"created_at", "draft", "kind", "markdown_path", "schema_version", "source"}


def test_write_latest_diary_draft_cache_failure_is_warning_only(monkeypatch, tmp_path: Path):
    _write_snapshot(
        tmp_path,
        "checkpoint",
        datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        changed_files=[{"path": "harbor/core/log_draft.py", "status": "M"}],
        summary={"status": "pass"},
    )
    monkeypatch.setattr(
        log_draft,
        "collect_git_workspace_state",
        lambda repo_root: {"git_head": "head123", "workspace_dirty": False, "changed_files": []},
    )
    payload = build_diary_draft(repo_root=tmp_path)
    original_write_text = Path.write_text

    def _failing_write_text(self, data, *args, **kwargs):
        if self.name in {"latest-draft.md", "latest-draft.json"}:
            raise OSError("disk full")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _failing_write_text)

    result = write_latest_diary_draft_cache(payload, repo_root=tmp_path)

    assert result["markdown_path"] is None
    assert result["json_path"] is None
    assert len(result["warnings"]) == 2
    assert any("latest draft markdown cache" in warning for warning in result["warnings"])
    assert any("latest draft JSON cache" in warning for warning in result["warnings"])


def test_build_saved_diary_draft_output_path_uses_reports_root_and_format(tmp_path: Path):
    path_md = build_saved_diary_draft_output_path(
        output_format="markdown",
        repo_root=tmp_path,
        created_at=datetime(2026, 5, 11, 12, 34, 56, tzinfo=timezone.utc),
    )
    path_json = build_saved_diary_draft_output_path(
        output_format="json",
        repo_root=tmp_path,
        created_at=datetime(2026, 5, 11, 12, 34, 56, tzinfo=timezone.utc),
    )

    assert path_md == tmp_path / ".harbor" / "reports" / "log-draft-20260511-123456.md"
    assert path_json == tmp_path / ".harbor" / "reports" / "log-draft-20260511-123456.json"
