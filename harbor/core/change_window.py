from __future__ import annotations

import json
import subprocess
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from harbor.core.workspace import load_workspace_paths


CHANGE_WINDOW_SCHEMA_VERSION = "1.0"
CHANGE_WINDOW_EVENTS = {"checkpoint", "accept", "finish"}
DEFAULT_CHANGE_WINDOW_RETENTION = 50


@dataclass
class ChangeWindowSnapshot:
    schema_version: str
    event: str
    timestamp: str
    git_head: Optional[str]
    workspace_dirty: Optional[bool]
    changed_files: List[Dict[str, str]]
    summary: Dict[str, Any]
    validation: Dict[str, Any]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the current snapshot into a JSON-friendly change-window dict.

        Behavior:
          - Returns a JSON-friendly dict containing `schema_version`, `event`,
            `timestamp`, `git_head`, `workspace_dirty`, `changed_files`,
            `summary`, `validation`, and `notes`.
          - Serializes only the current in-memory object for runtime
            change-window state; it is not a source of truth.
          - Does not include file contents and does not include diff bodies.
          - Keeps field names stable for future `harbor log draft` evidence use.

        Side Effects:
          - Pure serialization only; writes no files, runs no git commands, and
            does not mutate object state.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: pure

        Returns:
          Dict[str, Any]: JSON-friendly snapshot payload for the current object
          only.
        """
        return asdict(self)


def write_change_window_snapshot(
    event: str,
    *,
    summary: Optional[Dict[str, Any]] = None,
    validation: Optional[Dict[str, Any]] = None,
    notes: Optional[Sequence[str]] = None,
    repo_root: Optional[Path] = None,
    timestamp: Optional[datetime] = None,
    git_head: Optional[str] = None,
    workspace_dirty: Optional[bool] = None,
    changed_files: Optional[List[Dict[str, str]]] = None,
    retention_limit: int = DEFAULT_CHANGE_WINDOW_RETENTION,
) -> Path:
    """Write one change-window snapshot under `.harbor/state/change-windows/`.

    Behavior:
      - Supports `checkpoint`, `accept`, and `finish` events only.
      - Fills the MVP schema with UTC timestamp, git metadata, lightweight summary,
        validation payload, and notes.
      - Creates the target directory when missing and keeps JSON output stable
        with `sort_keys=True`, `indent=2`, and `ensure_ascii=False`.
      - Writes runtime state under `.harbor/state/change-windows/`; this
        evidence is advisory and not a source of truth.
      - Produces stable snapshot fields for future `harbor log draft` evidence
        without writing Diary entries or executing `harbor log`.
      - Applies simple retention by deleting snapshots older than the newest
        `retention_limit` files.

    Side Effects:
      - Writes one runtime-state JSON file under `.harbor/state/change-windows/`.
      - May run lightweight git read commands (`rev-parse`, `status --short`) when
        git metadata is not provided explicitly.
      - May delete older snapshot files when retention is exceeded.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once

    Args:
      event: Change-window event name. Must be `checkpoint`, `accept`, or
        `finish`.
      summary: JSON-friendly command summary written into the snapshot.
      validation: JSON-friendly validation and command metadata.
      notes: Optional human-readable runtime notes stored with the snapshot.
      repo_root: Repository root used to resolve `.harbor/state/`.
      timestamp: UTC timestamp override for deterministic writes/tests.
      git_head: Optional git HEAD override.
      workspace_dirty: Optional workspace dirty override.
      changed_files: Optional changed-file summary override.
      retention_limit: Maximum number of newest snapshots to keep.

    Returns:
      Path: Path to the written runtime snapshot JSON file.
    """
    resolved_event = str(event or "").strip().lower()
    if resolved_event not in CHANGE_WINDOW_EVENTS:
        raise ValueError(f"Unsupported change window event: {event!r}")

    root = Path(repo_root or Path.cwd()).resolve()
    dt = (timestamp or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if git_head is None or workspace_dirty is None or changed_files is None:
        git_state = collect_git_workspace_state(root)
        if git_head is None:
            git_head = git_state["git_head"]
        if workspace_dirty is None:
            workspace_dirty = git_state["workspace_dirty"]
        if changed_files is None:
            changed_files = git_state["changed_files"]

    snapshot = ChangeWindowSnapshot(
        schema_version=CHANGE_WINDOW_SCHEMA_VERSION,
        event=resolved_event,
        timestamp=_format_iso8601_utc(dt),
        git_head=git_head,
        workspace_dirty=workspace_dirty,
        changed_files=_coerce_changed_files(changed_files or []),
        summary=_coerce_mapping(summary),
        validation=_coerce_mapping(validation),
        notes=[str(item) for item in list(notes or [])],
    )

    target_dir = change_window_dir(root)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{_format_snapshot_stamp(dt)}-{resolved_event}.json"
    target.write_text(
        json.dumps(snapshot.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    prune_change_windows(limit=retention_limit, repo_root=root)
    return target


def list_change_windows(limit: Optional[int] = None, *, repo_root: Optional[Path] = None) -> List[ChangeWindowSnapshot]:
    """List readable change-window snapshots from newest to oldest.

    Behavior:
      - Loads `*.json` snapshot files from `.harbor/state/change-windows/`.
      - Sorts snapshots by timestamp/filename descending.
      - Skips invalid JSON files with a runtime warning instead of failing.
      - Applies the optional `limit` after sorting.

    Side Effects:
      - Read-only filesystem access only; does not write or delete files.
    """
    root = Path(repo_root or Path.cwd()).resolve()
    target_dir = change_window_dir(root)
    if not target_dir.exists():
        return []

    rows: List[tuple[str, ChangeWindowSnapshot]] = []
    for path in target_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            snapshot = _snapshot_from_payload(payload)
        except Exception as exc:
            warnings.warn(
                f"Skipping invalid change window snapshot '{path.name}': {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue
        rows.append((path.name, snapshot))

    rows.sort(key=lambda item: (item[1].timestamp, item[0]), reverse=True)
    snapshots = [snapshot for _, snapshot in rows]
    if limit is None:
        return snapshots
    return snapshots[: max(int(limit), 0)]


def get_latest_change_window(
    event: Optional[str] = None,
    *,
    repo_root: Optional[Path] = None,
) -> Optional[ChangeWindowSnapshot]:
    """Return the newest readable snapshot, optionally filtered by event."""
    resolved_event = str(event or "").strip().lower()
    for snapshot in list_change_windows(repo_root=repo_root):
        if resolved_event and snapshot.event != resolved_event:
            continue
        return snapshot
    return None


def prune_change_windows(
    *,
    limit: int = DEFAULT_CHANGE_WINDOW_RETENTION,
    repo_root: Optional[Path] = None,
) -> List[Path]:
    """Delete change-window snapshots older than the newest `limit` files."""
    if limit < 0:
        raise ValueError("limit must be >= 0")

    root = Path(repo_root or Path.cwd()).resolve()
    target_dir = change_window_dir(root)
    if not target_dir.exists():
        return []

    files = sorted(target_dir.glob("*.json"), key=lambda item: item.name, reverse=True)
    removed: List[Path] = []
    for path in files[limit:]:
        path.unlink(missing_ok=True)
        removed.append(path)
    return removed


def collect_git_workspace_state(repo_root: Path) -> Dict[str, Any]:
    """Collect lightweight git metadata for change-window snapshots.

    Behavior:
      - Returns `git_head`, `workspace_dirty`, and `changed_files`.
      - Falls back to `None` / `[]` when git metadata is unavailable.
      - Stores only git status codes and paths, never file contents or diffs.

    Side Effects:
      - Executes read-only git commands in the target repository.
    """
    root = Path(repo_root).resolve()
    git_head = _run_git(root, "rev-parse", "HEAD")
    status_lines = _git_status_lines(root)
    if status_lines is None:
        workspace_dirty: Optional[bool] = None
        changed_files: List[Dict[str, str]] = []
    else:
        changed_files = [_parse_git_status_line(line) for line in status_lines if line.strip()]
        workspace_dirty = bool(changed_files)
    return {
        "git_head": git_head,
        "workspace_dirty": workspace_dirty,
        "changed_files": changed_files,
    }


def change_window_dir(repo_root: Path) -> Path:
    workspace_paths = load_workspace_paths(repo_root, enforce_write_safety=True)
    return workspace_paths.state_root / "change-windows"


def _coerce_mapping(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("snapshot payload sections must be JSON objects")
    return dict(payload)


def _coerce_changed_files(items: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        status = str(raw.get("status") or "").strip()
        path = str(raw.get("path") or "").replace("\\", "/").strip()
        if not path:
            continue
        normalized.append({"path": path, "status": status})
    return normalized


def _format_iso8601_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_snapshot_stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_git(repo_root: Path, *args: str) -> Optional[str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except Exception:
        return None

    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _git_status_lines(repo_root: Path) -> Optional[List[str]]:
    output = _run_git(repo_root, "status", "--short")
    if output is None:
        return None
    return output.splitlines()


def _parse_git_status_line(line: str) -> Dict[str, str]:
    raw = str(line.rstrip("\n"))
    if len(raw) < 2:
        return {"path": raw.strip().replace("\\", "/"), "status": ""}
    status = raw[:2]
    path = raw[2:].lstrip().replace("\\", "/")
    normalized_status = "??" if status == "??" else status.strip()
    return {"path": path, "status": normalized_status}


def _snapshot_from_payload(payload: Any) -> ChangeWindowSnapshot:
    if not isinstance(payload, dict):
        raise ValueError("snapshot JSON root must be an object")

    event = str(payload.get("event") or "").strip().lower()
    if event not in CHANGE_WINDOW_EVENTS:
        raise ValueError(f"invalid event: {event!r}")

    schema_version = str(payload.get("schema_version") or "")
    timestamp = str(payload.get("timestamp") or "").strip()
    if not schema_version:
        raise ValueError("schema_version is required")
    if not timestamp:
        raise ValueError("timestamp is required")

    summary = payload.get("summary") or {}
    validation = payload.get("validation") or {}
    notes = payload.get("notes") or []
    changed_files = payload.get("changed_files") or []
    if not isinstance(summary, dict):
        raise ValueError("summary must be an object")
    if not isinstance(validation, dict):
        raise ValueError("validation must be an object")
    if not isinstance(notes, list):
        raise ValueError("notes must be a list")
    if not isinstance(changed_files, list):
        raise ValueError("changed_files must be a list")

    workspace_dirty = payload.get("workspace_dirty")
    if workspace_dirty is not None:
        workspace_dirty = bool(workspace_dirty)

    git_head = payload.get("git_head")
    if git_head is not None:
        git_head = str(git_head)

    return ChangeWindowSnapshot(
        schema_version=schema_version,
        event=event,
        timestamp=timestamp,
        git_head=git_head,
        workspace_dirty=workspace_dirty,
        changed_files=_coerce_changed_files(changed_files),
        summary=dict(summary),
        validation=dict(validation),
        notes=[str(item) for item in notes],
    )
