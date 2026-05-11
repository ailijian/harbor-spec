from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from harbor.core.change_window import ChangeWindowSnapshot, collect_git_workspace_state, list_change_windows
from harbor.core.workspace import load_workspace_paths


DIARY_DRAFT_SCHEMA_VERSION = "1.0"
DIARY_DRAFT_KIND = "diary_draft"
DEFAULT_SNAPSHOT_LIMIT = 12
KNOWN_REPORT_COMMANDS = {"checkpoint", "stale", "doctor"}
VALIDATION_KEYS = ("pytest", "checkpoint", "stale", "doctor")
LOG_MARKER_TIMESTAMP_KEYS = (
    "timestamp",
    "ts",
    "last_log_timestamp",
    "last_log_ts",
    "snapshot_timestamp",
)


class LogDraftError(RuntimeError):
    """Raised when `harbor log draft` input or output constraints are violated."""


def build_diary_draft(
    *,
    repo_root: Optional[Path] = None,
    since_last_accept: bool = False,
    since_last_log: bool = False,
    from_report: Optional[Path] = None,
    snapshot_limit: int = DEFAULT_SNAPSHOT_LIMIT,
) -> Dict[str, Any]:
    """Build a deterministic diary draft from existing change-window evidence.

    Behavior:
      - Reads only existing evidence: change-window snapshots, optional report JSON,
        and current git status metadata.
      - Does not read source file contents, does not read diffs, and does not call
        LLM/network providers.
      - Never writes `.harbor/diary/**`; output file writes are handled separately.
      - Returns a stable JSON-friendly draft payload suitable for markdown or JSON
        rendering.

    Side Effects:
      - Read-only filesystem access for snapshots, reports, and optional log marker.
      - Read-only git commands through `collect_git_workspace_state`.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    root = Path(repo_root or Path.cwd()).resolve()
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    notes: List[str] = []

    latest_accept = _latest_accept_snapshot(root)
    marker_timestamp: Optional[str] = None

    if since_last_accept and since_last_log:
        raise LogDraftError("Choose only one boundary mode: --since-last-accept or --since-last-log.")

    if since_last_accept:
        if latest_accept is not None:
            notes.append(f"Using change-window evidence after the latest accept snapshot at {latest_accept.timestamp}.")
        else:
            notes.append("Evidence boundary uncertain: no accept snapshot found; fell back to recent change-window snapshots.")
    elif since_last_log:
        marker_timestamp = _read_last_log_marker_timestamp(workspace_paths.state_root / "log" / "last_log_marker.json")
        if marker_timestamp:
            notes.append(f"Using change-window evidence after the last log marker at {marker_timestamp}.")
        else:
            notes.append("No last log marker found; fell back to recent change-window snapshots.")
            notes.append("Evidence boundary uncertain because `--since-last-log` could not resolve a marker timestamp.")

    boundary_timestamp = latest_accept.timestamp if since_last_accept and latest_accept is not None else marker_timestamp
    selected_snapshots = _select_snapshots(
        list_change_windows(repo_root=root),
        boundary_timestamp=boundary_timestamp,
        limit=snapshot_limit,
    )

    if from_report is not None:
        reports = [_load_report_summary(Path(from_report), repo_root=root)]
        notes.append(f"Using explicit report evidence from {reports[0]['path']}.")
    else:
        reports = _discover_report_summaries(workspace_paths.reports_root, repo_root=root)

    git_state = collect_git_workspace_state(root)
    changed_files = _merge_changed_files(selected_snapshots, git_state.get("changed_files") or [])
    affected_areas = _classify_affected_areas(changed_files)
    validation = _derive_validation_statuses(selected_snapshots, reports)
    contract_impact = _infer_contract_impact(changed_files, reports, selected_snapshots)
    meaningful = bool(selected_snapshots or reports or changed_files)

    summary = _build_summary(
        meaningful=meaningful,
        changed_files=changed_files,
        affected_areas=affected_areas,
        since_last_accept=since_last_accept,
        since_last_log=since_last_log,
        from_report=reports[0]["command"] if from_report is not None and reports else None,
    )
    why = _build_why(
        meaningful=meaningful,
        contract_impact=contract_impact,
        notes=notes,
        changed_files=changed_files,
        reports=reports,
    )
    risks = _build_risks(
        meaningful=meaningful,
        notes=notes,
        validation=validation,
        latest_accept=latest_accept,
        from_report=from_report,
    )
    suggested_diary_entry = _build_suggested_diary_entry(
        summary=summary,
        why=why,
        affected_areas=affected_areas,
        contract_impact=contract_impact,
        validation=validation,
        meaningful=meaningful,
    )

    evidence_snapshots = [_snapshot_summary(snapshot) for snapshot in selected_snapshots]
    if latest_accept is not None and not any(
        item["event"] == "accept" and item["timestamp"] == latest_accept.timestamp for item in evidence_snapshots
    ):
        evidence_snapshots.append(_snapshot_summary(latest_accept, role="latest_accept_boundary"))
    evidence_snapshots = sorted(
        evidence_snapshots,
        key=lambda item: (str(item.get("timestamp") or ""), str(item.get("event") or "")),
        reverse=True,
    )

    return {
        "schema_version": DIARY_DRAFT_SCHEMA_VERSION,
        "kind": DIARY_DRAFT_KIND,
        "summary": summary,
        "why": why,
        "affected_areas": affected_areas,
        "contract_impact": contract_impact,
        "validation": validation,
        "evidence": {
            "snapshots": evidence_snapshots,
            "reports": reports,
            "changed_files": changed_files,
        },
        "risks": risks,
        "suggested_diary_entry": suggested_diary_entry,
    }


def render_diary_draft_markdown(payload: Dict[str, Any]) -> str:
    """Render a stable markdown diary draft from the JSON payload.

    Behavior:
      - Produces a deterministic markdown draft with the fixed MVP sections:
        Summary, Why, Affected Areas, Contract Impact, Validation,
        Change Window Evidence, Risks / Notes, and Suggested Diary Entry.
      - Renders only summary-level evidence already present in the payload.
      - Does not inject file contents, diff bodies, secrets, or environment values.

    Side Effects:
      - Pure rendering only; does not write files and does not mutate the payload.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: pure
    """
    evidence = dict(payload.get("evidence") or {})
    snapshots = list(evidence.get("snapshots") or [])
    reports = list(evidence.get("reports") or [])
    changed_files = list(evidence.get("changed_files") or [])
    affected = dict(payload.get("affected_areas") or {})
    validation = dict(payload.get("validation") or {})
    risks = [str(item) for item in list(payload.get("risks") or [])]

    latest_accept = next(
        (item for item in snapshots if item.get("event") == "accept" or item.get("role") == "latest_accept_boundary"),
        None,
    )
    checkpoint_snapshots = [item for item in snapshots if item.get("event") == "checkpoint"]
    finish_snapshots = [item for item in snapshots if item.get("event") == "finish"]

    lines = [
        "# Diary Draft",
        "",
        "## Summary",
        "",
        str(payload.get("summary") or ""),
        "",
        "## Why",
        "",
        str(payload.get("why") or ""),
        "",
        "## Affected Areas",
        "",
        f"- production code: {_format_area_list(affected.get('production_code') or [])}",
        f"- tests: {_format_area_list(affected.get('tests') or [])}",
        f"- generated context: {_format_area_list(affected.get('generated_context') or [])}",
        f"- reports: {_format_area_list(affected.get('reports') or [])}",
        f"- runtime state: {_format_area_list(affected.get('runtime_state') or [])}",
        f"- docs: {_format_area_list(affected.get('docs') or [])}",
        "",
        "## Contract Impact",
        "",
        str(payload.get("contract_impact") or "uncertain"),
        "",
        "## Validation",
        "",
        f"- pytest: {validation.get('pytest', 'unknown')}",
        f"- checkpoint: {validation.get('checkpoint', 'unknown')}",
        f"- stale: {validation.get('stale', 'unknown')}",
        f"- doctor: {validation.get('doctor', 'unknown')}",
        "",
        "## Change Window Evidence",
        "",
        f"- latest accept snapshot: {_format_snapshot_line(latest_accept)}",
        f"- checkpoint snapshots: {_format_snapshot_group(checkpoint_snapshots)}",
        f"- finish snapshots: {_format_snapshot_group(finish_snapshots)}",
        f"- changed files: {_format_changed_files(changed_files)}",
        f"- reports: {_format_reports(reports)}",
        "",
        "## Risks / Notes",
        "",
    ]
    if risks:
        for item in risks:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Suggested Diary Entry",
            "",
            str(payload.get("suggested_diary_entry") or ""),
        ]
    )
    return "\n".join(lines).strip() + "\n"


def serialize_diary_draft(payload: Dict[str, Any], output_format: str) -> str:
    """Serialize a diary draft payload as markdown or stable JSON.

    Behavior:
      - `markdown` returns the stable markdown draft body.
      - `json` returns one stable JSON object with `sort_keys=True`, `indent=2`,
        and `ensure_ascii=False`.
      - Rejects unsupported formats with `LogDraftError`.

    Side Effects:
      - Pure serialization only; writes no files and performs no network/LLM calls.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: pure
    """
    normalized_format = str(output_format or "markdown").strip().lower()
    if normalized_format == "markdown":
        return render_diary_draft_markdown(payload)
    if normalized_format == "json":
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    raise LogDraftError(f"Unsupported draft format: {output_format!r}")


def write_diary_draft_output(
    payload: Dict[str, Any],
    output_path: Path,
    *,
    output_format: str,
    repo_root: Optional[Path] = None,
) -> Path:
    """Write a rendered diary draft to a safe non-diary path inside the repo.

    Behavior:
      - Resolves the output path relative to the repository root.
      - Rejects paths outside the repository and rejects `.harbor/diary/**`.
      - Writes the rendered markdown/JSON draft to the requested non-diary path.
      - Never appends to `.harbor/diary/**` and never updates log markers.

    Side Effects:
      - Writes exactly one non-diary output file and may create parent directories.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once
    """
    root = Path(repo_root or Path.cwd()).resolve()
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    resolved = _resolve_output_path(Path(output_path), repo_root=root)
    _reject_diary_output_path(resolved, diary_root=workspace_paths.diary_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(serialize_diary_draft(payload, output_format), encoding="utf-8")
    return resolved


def _latest_accept_snapshot(repo_root: Path) -> Optional[ChangeWindowSnapshot]:
    for snapshot in list_change_windows(repo_root=repo_root):
        if snapshot.event == "accept":
            return snapshot
    return None


def _read_last_log_marker_timestamp(marker_path: Path) -> Optional[str]:
    if not marker_path.exists():
        return None
    try:
        payload = json.loads(marker_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    for key in LOG_MARKER_TIMESTAMP_KEYS:
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return None


def _select_snapshots(
    snapshots: Sequence[ChangeWindowSnapshot],
    *,
    boundary_timestamp: Optional[str],
    limit: int,
) -> List[ChangeWindowSnapshot]:
    rows = list(snapshots or [])
    if boundary_timestamp:
        rows = [snapshot for snapshot in rows if str(snapshot.timestamp) > str(boundary_timestamp)]
    return rows[: max(int(limit), 0)]


def _snapshot_summary(snapshot: ChangeWindowSnapshot, *, role: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "event": snapshot.event,
        "timestamp": snapshot.timestamp,
        "git_head": snapshot.git_head,
        "workspace_dirty": snapshot.workspace_dirty,
        "changed_files_count": len(list(snapshot.changed_files or [])),
    }
    if role:
        payload["role"] = role
    return payload


def _load_report_summary(path: Path, *, repo_root: Path) -> Dict[str, Any]:
    candidate = path if path.is_absolute() else (repo_root / path)
    resolved = candidate.resolve()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise LogDraftError(f"Failed to decode report '{resolved.as_posix()}' as UTF-8 JSON: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LogDraftError(f"Failed to parse JSON report '{resolved.as_posix()}': {exc}") from exc
    except OSError as exc:
        raise LogDraftError(f"Unable to read report '{resolved.as_posix()}': {exc}") from exc
    if not isinstance(payload, dict):
        raise LogDraftError(f"Report '{resolved.as_posix()}' must contain a JSON object.")

    command = str(payload.get("command") or "").strip().lower()
    if command not in KNOWN_REPORT_COMMANDS:
        raise LogDraftError(
            f"Unsupported report command for draft input: {command!r}. Expected checkpoint/stale/doctor JSON."
        )

    return {
        "path": _to_repo_relative_display(resolved, repo_root=repo_root),
        "command": command,
        "status": _normalize_report_status(payload.get("status")),
    }


def _discover_report_summaries(reports_root: Path, *, repo_root: Path) -> List[Dict[str, Any]]:
    if not reports_root.exists():
        return []
    summaries: List[Tuple[float, Dict[str, Any]]] = []
    for path in reports_root.rglob("*.json"):
        try:
            summary = _load_report_summary(path, repo_root=repo_root)
        except LogDraftError:
            continue
        try:
            stamp = path.stat().st_mtime
        except OSError:
            stamp = 0.0
        summaries.append((stamp, summary))
    summaries.sort(key=lambda item: (item[0], item[1]["path"]), reverse=True)

    selected: List[Dict[str, Any]] = []
    seen_commands = set()
    for _, summary in summaries:
        command = summary["command"]
        if command in seen_commands:
            continue
        seen_commands.add(command)
        selected.append(summary)
    return selected


def _normalize_report_status(value: Any) -> str:
    status = str(value or "unknown").strip().lower()
    if status in {"pass", "warn", "fail"}:
        return status
    return "unknown"


def _merge_changed_files(
    snapshots: Sequence[ChangeWindowSnapshot],
    current_changed_files: Sequence[Dict[str, str]],
) -> List[Dict[str, str]]:
    merged: Dict[Tuple[str, str], Dict[str, str]] = {}
    for snapshot in snapshots:
        for item in list(snapshot.changed_files or []):
            normalized = _normalize_changed_file(item)
            if normalized is not None:
                merged[(normalized["path"], normalized["status"])] = normalized
    for item in current_changed_files:
        normalized = _normalize_changed_file(item)
        if normalized is not None:
            merged[(normalized["path"], normalized["status"])] = normalized
    return sorted(merged.values(), key=lambda item: (item["path"], item["status"]))


def _normalize_changed_file(item: Any) -> Optional[Dict[str, str]]:
    if not isinstance(item, dict):
        return None
    path = str(item.get("path") or "").replace("\\", "/").strip()
    if not path:
        return None
    return {
        "path": path,
        "status": str(item.get("status") or "").strip(),
    }


def _classify_affected_areas(changed_files: Sequence[Dict[str, str]]) -> Dict[str, List[str]]:
    buckets: Dict[str, List[str]] = {
        "production_code": [],
        "tests": [],
        "generated_context": [],
        "reports": [],
        "runtime_state": [],
        "docs": [],
    }
    for item in changed_files:
        path = str(item.get("path") or "")
        bucket = _bucket_for_path(path)
        buckets[bucket].append(path)
    for key, values in list(buckets.items()):
        buckets[key] = sorted(dict.fromkeys(values))
    return buckets


def _bucket_for_path(path: str) -> str:
    normalized = str(path or "").replace("\\", "/").strip()
    lower = normalized.lower()
    if lower.startswith("tests/"):
        return "tests"
    if lower.startswith(".harbor/views/"):
        return "generated_context"
    if lower.startswith(".harbor/reports/"):
        return "reports"
    if lower.startswith(".harbor/state/"):
        return "runtime_state"
    if (
        lower == "agents.md"
        or lower.startswith("docs/")
        or lower.startswith(".harbor/rules/")
        or lower.endswith(".md")
        or lower.endswith(".rst")
    ):
        return "docs"
    return "production_code"


def _derive_validation_statuses(
    snapshots: Sequence[ChangeWindowSnapshot],
    reports: Sequence[Dict[str, Any]],
) -> Dict[str, str]:
    statuses = {key: "unknown" for key in VALIDATION_KEYS}
    for report in reports:
        command = str(report.get("command") or "").strip().lower()
        if command in {"checkpoint", "stale", "doctor"}:
            statuses[command] = _coerce_validation_status(report.get("status"))
    for snapshot in snapshots:
        validation = dict(snapshot.validation or {})
        summary = dict(snapshot.summary or {})
        if snapshot.event == "checkpoint" and statuses["checkpoint"] == "unknown":
            statuses["checkpoint"] = _coerce_validation_status(
                summary.get("status") or validation.get("status") or validation.get("checkpoint")
            )
        pytest_status = validation.get("pytest") or summary.get("pytest")
        if statuses["pytest"] == "unknown" and pytest_status is not None:
            statuses["pytest"] = _coerce_validation_status(pytest_status)
        for key in ("stale", "doctor"):
            if statuses[key] == "unknown" and validation.get(key) is not None:
                statuses[key] = _coerce_validation_status(validation.get(key))
    return statuses


def _coerce_validation_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"pass", "passed", "ok", "success", "true"}:
        return "pass"
    if normalized in {"fail", "failed", "error", "warn", "warning", "false"}:
        return "fail"
    return "unknown"


def _infer_contract_impact(
    changed_files: Sequence[Dict[str, str]],
    reports: Sequence[Dict[str, Any]],
    snapshots: Sequence[ChangeWindowSnapshot],
) -> str:
    if not changed_files and not reports and not snapshots:
        return "uncertain"

    yes_markers = (
        "harbor/cli/",
        "harbor/core/change_window.py",
        "harbor/core/ci.py",
        "harbor/core/stale.py",
        "harbor/core/doctor.py",
        "harbor/core/ddt.py",
        "harbor/core/audit.py",
        "harbor/core/log_draft.py",
        ".harbor/rules/",
        "docs/",
        "release",
        "agents.md",
    )
    uncertain_markers = ("tests/", ".harbor/reports/", ".harbor/state/")

    saw_uncertain = False
    for item in changed_files:
        path = str(item.get("path") or "").replace("\\", "/").strip().lower()
        if not path:
            continue
        if any(marker in path for marker in yes_markers):
            return "yes"
        if path.endswith(".json") or any(path.startswith(marker) for marker in uncertain_markers):
            saw_uncertain = True

    for report in reports:
        command = str(report.get("command") or "").strip().lower()
        if command in {"checkpoint", "stale", "doctor"}:
            return "yes"

    return "uncertain" if saw_uncertain else "no"


def _build_summary(
    *,
    meaningful: bool,
    changed_files: Sequence[Dict[str, str]],
    affected_areas: Dict[str, List[str]],
    since_last_accept: bool,
    since_last_log: bool,
    from_report: Optional[str],
) -> str:
    if not meaningful:
        return "No meaningful change window found for diary drafting."

    labels = [
        label
        for label, paths in (
            ("production code", affected_areas.get("production_code") or []),
            ("tests", affected_areas.get("tests") or []),
            ("generated context", affected_areas.get("generated_context") or []),
            ("reports", affected_areas.get("reports") or []),
            ("runtime state", affected_areas.get("runtime_state") or []),
            ("docs", affected_areas.get("docs") or []),
        )
        if paths
    ]
    area_text = ", ".join(labels[:3]) if labels else "workspace evidence"
    count = len(list(changed_files or []))
    if from_report:
        return f"Drafted from the explicit {from_report} report plus current change-window evidence across {area_text}."
    if since_last_accept:
        return f"Evidence since the latest accept snapshot suggests meaningful changes across {area_text} ({count} changed files observed)."
    if since_last_log:
        return f"Evidence since the last log marker suggests meaningful changes across {area_text} ({count} changed files observed)."
    return f"Recent change-window evidence suggests meaningful changes across {area_text} ({count} changed files observed)."


def _build_why(
    *,
    meaningful: bool,
    contract_impact: str,
    notes: Sequence[str],
    changed_files: Sequence[Dict[str, str]],
    reports: Sequence[Dict[str, Any]],
) -> str:
    if not meaningful:
        return "Evidence insufficient: no snapshots, relevant reports, or changed files were found."

    fragments: List[str] = []
    if changed_files:
        fragments.append(f"Changed file evidence is present ({len(list(changed_files))} paths).")
    if reports:
        fragments.append(
            "Validation/report evidence is available from "
            + ", ".join(sorted(dict.fromkeys(str(item.get("command") or "unknown") for item in reports)))
            + "."
        )
    if contract_impact == "yes":
        fragments.append("The affected paths suggest contract-relevant CLI, report, change-window, or public-doc behavior.")
    elif contract_impact == "uncertain":
        fragments.append("Contract impact remains uncertain because the evidence is path-level only and does not inspect file bodies.")
    if notes:
        fragments.append(" ".join(str(item) for item in notes))
    return " ".join(fragments).strip()


def _build_risks(
    *,
    meaningful: bool,
    notes: Sequence[str],
    validation: Dict[str, str],
    latest_accept: Optional[ChangeWindowSnapshot],
    from_report: Optional[Path],
) -> List[str]:
    risks: List[str] = []
    if not meaningful:
        risks.append("no meaningful change window found")
    for note in notes:
        risks.append(str(note))
    if latest_accept is None:
        risks.append("No accept snapshot is available in the current evidence set.")
    if from_report is None:
        risks.append("Report evidence is opportunistic; only clearly parseable checkpoint/stale/doctor JSON files are included.")
    for key in ("pytest", "checkpoint", "stale", "doctor"):
        if validation.get(key) == "unknown":
            risks.append(f"{key} status remains unknown because `harbor log draft` does not run validation commands.")
    return sorted(dict.fromkeys(risks))


def _build_suggested_diary_entry(
    *,
    summary: str,
    why: str,
    affected_areas: Dict[str, List[str]],
    contract_impact: str,
    validation: Dict[str, str],
    meaningful: bool,
) -> str:
    if not meaningful:
        return (
            "[Diary Draft]\n"
            "- Type: decision\n"
            "- Importance: normal\n"
            "- Visibility: repo\n"
            "- Module: workspace\n"
            "- Contract Impact: uncertain\n"
            "- Breaking Change: uncertain\n"
            "- Summary: No meaningful change window found.\n"
            "- Reason: Evidence insufficient for a stronger Diary recommendation.\n"
        )

    area_labels = [
        label
        for label, paths in (
            ("production code", affected_areas.get("production_code") or []),
            ("tests", affected_areas.get("tests") or []),
            ("generated context", affected_areas.get("generated_context") or []),
            ("reports", affected_areas.get("reports") or []),
            ("runtime state", affected_areas.get("runtime_state") or []),
            ("docs", affected_areas.get("docs") or []),
        )
        if paths
    ]
    areas = ", ".join(area_labels) if area_labels else "workspace evidence"
    return (
        "[Diary Draft]\n"
        "- Type: decision\n"
        "- Importance: high\n"
        "- Visibility: repo\n"
        f"- Module: {areas}\n"
        f"- Contract Impact: {contract_impact}\n"
        "- Breaking Change: uncertain\n"
        f"- Summary: {summary}\n"
        f"- Reason: {why}\n"
        "- Changes:\n"
        f"  - Evidence points to updates across {areas}.\n"
        "- Tests:\n"
        f"  - pytest: {validation.get('pytest', 'unknown')}\n"
        f"  - checkpoint: {validation.get('checkpoint', 'unknown')}\n"
        f"  - stale: {validation.get('stale', 'unknown')}\n"
        f"  - doctor: {validation.get('doctor', 'unknown')}\n"
        "- Risks:\n"
        "  - Evidence is summary-level only and excludes file bodies/diffs.\n"
    )


def _resolve_output_path(path: Path, *, repo_root: Path) -> Path:
    candidate = path if path.is_absolute() else (repo_root / path)
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise LogDraftError(
            f"Draft output path must stay within the repository: '{resolved.as_posix()}'."
        ) from exc
    return resolved


def _reject_diary_output_path(path: Path, *, diary_root: Path) -> None:
    try:
        path.relative_to(diary_root.resolve())
    except ValueError:
        return
    raise LogDraftError(
        "Refusing to write diary draft under `.harbor/diary/**`; use `.harbor/reports/**` or another non-diary repo path."
    )


def _to_repo_relative_display(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.resolve().as_posix()


def _format_area_list(items: Sequence[str]) -> str:
    values = [str(item) for item in list(items or []) if str(item).strip()]
    if not values:
        return "none"
    return ", ".join(values[:6]) + (" ..." if len(values) > 6 else "")


def _format_snapshot_line(snapshot: Optional[Dict[str, Any]]) -> str:
    if not snapshot:
        return "none"
    stamp = str(snapshot.get("timestamp") or "unknown")
    changed = int(snapshot.get("changed_files_count") or 0)
    return f"{stamp} ({changed} changed files)"


def _format_snapshot_group(rows: Sequence[Dict[str, Any]]) -> str:
    items = list(rows or [])
    if not items:
        return "none"
    stamps = [str(item.get("timestamp") or "unknown") for item in items[:3]]
    suffix = " ..." if len(items) > 3 else ""
    return f"{len(items)} snapshot(s): " + ", ".join(stamps) + suffix


def _format_changed_files(rows: Sequence[Dict[str, str]]) -> str:
    items = list(rows or [])
    if not items:
        return "none"
    display = [f"{item.get('status', '')} {item.get('path', '')}".strip() for item in items[:8]]
    suffix = " ..." if len(items) > 8 else ""
    return f"{len(items)} file(s): " + ", ".join(display) + suffix


def _format_reports(rows: Sequence[Dict[str, Any]]) -> str:
    items = list(rows or [])
    if not items:
        return "none"
    display = [f"{item.get('command', 'unknown')}:{item.get('status', 'unknown')}:{item.get('path', '')}" for item in items]
    return ", ".join(display)
