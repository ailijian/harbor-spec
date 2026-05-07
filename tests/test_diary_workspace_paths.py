import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

from harbor.core.diary import DiaryManager


def _write_workspace_config(repo_root: Path, payload: dict) -> None:
    target = repo_root / ".harbor" / "config" / "harbor.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _month_pair() -> tuple[str, str]:
    now = datetime.utcnow()
    prev = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    return now.strftime("%Y-%m"), prev.strftime("%Y-%m")


def test_log_writes_only_canonical_path(tmp_path: Path) -> None:
    mgr = DiaryManager(repo_root=tmp_path)
    current_month, _ = _month_pair()
    ts = f"{current_month}-15T12:00:00Z"

    mgr.log(summary="phase-2e-a", ts=ts, visibility="repo")

    canonical = tmp_path / ".harbor" / "diary" / f"{current_month}.jsonl"
    legacy = tmp_path / "specs" / "diary" / f"{current_month}.jsonl"
    assert canonical.exists()
    assert not legacy.exists()


def test_load_active_reads_legacy_only_without_mutation(tmp_path: Path) -> None:
    current_month, _ = _month_pair()
    legacy_dir = tmp_path / "specs" / "diary"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    legacy_file = legacy_dir / f"{current_month}.jsonl"
    payload = {
        "ver": 1,
        "ts": f"{current_month}-02T08:00:00Z",
        "author": "tester",
        "type": "feature",
        "importance": "normal",
        "visibility": "repo",
        "summary": "legacy-only",
    }
    legacy_file.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    before = legacy_file.read_text(encoding="utf-8")

    mgr = DiaryManager(repo_root=tmp_path)
    rows = mgr.load_active(min_visibility="repo")

    assert len(rows) == 1
    assert rows[0].summary == "legacy-only"
    assert legacy_file.read_text(encoding="utf-8") == before


def test_dual_read_merge_with_stable_normalized_hash_dedupe(tmp_path: Path) -> None:
    current_month, _ = _month_pair()
    canonical_dir = tmp_path / ".harbor" / "diary"
    legacy_dir = tmp_path / "specs" / "diary"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    legacy_dir.mkdir(parents=True, exist_ok=True)

    duplicate_a = {
        "ver": 1,
        "ts": f"{current_month}-03T10:00:00Z",
        "author": "tester",
        "type": "chore",
        "importance": "normal",
        "visibility": "repo",
        "summary": "dup-entry",
        "details": "same",
    }
    # Same semantic object, different key order.
    duplicate_b = {
        "summary": "dup-entry",
        "visibility": "repo",
        "importance": "normal",
        "type": "chore",
        "author": "tester",
        "ts": f"{current_month}-03T10:00:00Z",
        "ver": 1,
        "details": "same",
    }
    canonical_only = {
        "ver": 1,
        "ts": f"{current_month}-04T10:00:00Z",
        "author": "tester",
        "type": "feature",
        "importance": "high",
        "visibility": "repo",
        "summary": "canonical-only",
    }
    legacy_only = {
        "ver": 1,
        "ts": f"{current_month}-05T10:00:00Z",
        "author": "tester",
        "type": "bugfix",
        "importance": "high",
        "visibility": "repo",
        "summary": "legacy-only",
    }

    (canonical_dir / f"{current_month}.jsonl").write_text(
        json.dumps(duplicate_a, ensure_ascii=False) + "\n" + json.dumps(canonical_only, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (legacy_dir / f"{current_month}.jsonl").write_text(
        json.dumps(duplicate_b, ensure_ascii=False) + "\n" + json.dumps(legacy_only, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    mgr = DiaryManager(repo_root=tmp_path)
    rows = mgr.load_active(min_visibility="repo")
    summaries = sorted([item.summary for item in rows])

    assert summaries == ["canonical-only", "dup-entry", "legacy-only"]


def test_load_active_keeps_recent_two_month_window(tmp_path: Path) -> None:
    current_month, _ = _month_pair()
    old_month = (datetime.utcnow().replace(day=1) - timedelta(days=95)).strftime("%Y-%m")
    canonical_dir = tmp_path / ".harbor" / "diary"
    canonical_dir.mkdir(parents=True, exist_ok=True)

    current_row = {
        "ver": 1,
        "ts": f"{current_month}-06T10:00:00Z",
        "author": "tester",
        "type": "feature",
        "importance": "normal",
        "visibility": "repo",
        "summary": "recent",
    }
    old_row = {
        "ver": 1,
        "ts": f"{old_month}-06T10:00:00Z",
        "author": "tester",
        "type": "feature",
        "importance": "normal",
        "visibility": "repo",
        "summary": "old",
    }
    (canonical_dir / f"{current_month}.jsonl").write_text(json.dumps(current_row, ensure_ascii=False) + "\n", encoding="utf-8")
    (canonical_dir / f"{old_month}.jsonl").write_text(json.dumps(old_row, ensure_ascii=False) + "\n", encoding="utf-8")

    mgr = DiaryManager(repo_root=tmp_path)
    rows = mgr.load_active(min_visibility="repo")
    summaries = [row.summary for row in rows]

    assert "recent" in summaries
    assert "old" not in summaries


def test_monthly_rotation_writes_canonical_month_file(tmp_path: Path) -> None:
    mgr = DiaryManager(repo_root=tmp_path)
    mgr.log(summary="m1", ts="2026-05-01T00:00:00Z", visibility="repo")
    mgr.log(summary="m2", ts="2026-06-01T00:00:00Z", visibility="repo")

    assert (tmp_path / ".harbor" / "diary" / "2026-05.jsonl").exists()
    assert (tmp_path / ".harbor" / "diary" / "2026-06.jsonl").exists()
    assert not (tmp_path / "specs" / "diary" / "2026-05.jsonl").exists()
    assert not (tmp_path / "specs" / "diary" / "2026-06.jsonl").exists()


def test_configured_diary_root_within_repo_is_used(tmp_path: Path) -> None:
    _write_workspace_config(
        tmp_path,
        {
            "workspace": {"root": ".harbor"},
            "diary": {"root": ".harbor/custom-diary"},
        },
    )
    mgr = DiaryManager(repo_root=tmp_path)
    mgr.log(summary="custom", ts="2026-07-01T00:00:00Z", visibility="repo")
    assert mgr.diary_dir == (tmp_path / ".harbor" / "custom-diary").resolve()
    assert (tmp_path / ".harbor" / "custom-diary" / "2026-07.jsonl").exists()


def test_workspace_outside_diary_paths_are_rejected(tmp_path: Path) -> None:
    _write_workspace_config(
        tmp_path,
        {
            "workspace": {"root": ".harbor"},
            "diary": {"root": "../outside"},
        },
    )
    with pytest.raises(ValueError, match="escapes repo root"):
        DiaryManager(repo_root=tmp_path)

    _write_workspace_config(
        tmp_path,
        {
            "workspace": {"root": ".harbor"},
            "diary": {"root": ".harbor/diary", "dir": "../outside-legacy"},
        },
    )
    with pytest.raises(ValueError, match="escapes repo root"):
        DiaryManager(repo_root=tmp_path)
