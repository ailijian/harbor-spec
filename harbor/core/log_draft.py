from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from harbor.core.change_window import ChangeWindowSnapshot, collect_git_workspace_state, list_change_windows
from harbor.core.workspace import load_workspace_paths


DIARY_DRAFT_SCHEMA_VERSION = "1.0"
DIARY_DRAFT_KIND = "diary_draft"
LATEST_DRAFT_WRAPPER_SCHEMA_VERSION = "1.0"
WRITTEN_DIARY_ENTRY_SCHEMA_VERSION = "1.0"
WRITTEN_DIARY_ENTRY_KIND = "written_diary_entry"
DEFAULT_SNAPSHOT_LIMIT = 12
DEFAULT_LOG_DRAFT_SAVE_PREFIX = "log-draft"
KNOWN_REPORT_COMMANDS = {"checkpoint", "stale", "doctor"}
VALIDATION_KEYS = ("pytest", "checkpoint", "stale", "doctor")
SAFE_EXCERPT_MAX_LEN = 1000
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


def build_saved_diary_draft_output_path(
    *,
    output_format: str,
    repo_root: Optional[Path] = None,
    created_at: Optional[datetime] = None,
) -> Path:
    """Build a timestamped safe reports path for `harbor log draft --save`.

    Behavior:
      - Uses the canonical reports root from workspace config.
      - Uses `log-draft-YYYYMMDD-HHMMSS.<ext>` where ext follows the draft format.
      - Returns only the computed path; does not write files.

    Side Effects:
      - Pure path calculation only.
    """
    root = Path(repo_root or Path.cwd()).resolve()
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    normalized_format = str(output_format or "markdown").strip().lower()
    extension = "json" if normalized_format == "json" else "md"
    stamp = (created_at or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    return workspace_paths.reports_root / f"{DEFAULT_LOG_DRAFT_SAVE_PREFIX}-{stamp}.{extension}"


def write_latest_diary_draft_cache(
    payload: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Best-effort write of latest diary draft runtime cache under `.harbor/state/log/`.

    Behavior:
      - Always attempts to write both `latest-draft.md` and `latest-draft.json`.
      - JSON cache uses a stable wrapper schema that embeds the raw draft payload.
      - Markdown cache always stores the rendered markdown preview even if the
        caller requested JSON stdout elsewhere.
      - JSON cache wrapper uses stable English keys:
        `schema_version`, `kind`, `created_at`, `source`, `draft`,
        `markdown_path`.
      - Cache writes target runtime state only and may overwrite previous
        latest-draft cache files.
      - Cache write failures are downgraded to warnings and never raise.
      - Cache writes do not write `.harbor/reports/**`, do not write
        `.harbor/diary/**`, do not update `last_log_marker`, and do not change
        the primary draft stdout / exit semantics.

    Side Effects:
      - May create `.harbor/state/log/` and write up to two runtime cache files.
      - May overwrite existing latest-draft runtime cache files.

    Returns:
      Dict[str, Any]: Best-effort cache result with:
      - `markdown_path`: absolute `Path` when markdown cache write succeeded,
        else `None`
      - `json_path`: absolute `Path` when JSON cache write succeeded, else
        `None`
      - `markdown_path_display`: repo-relative display path for CLI messages
      - `json_path_display`: repo-relative display path for CLI messages
      - `warnings`: list of non-fatal cache write diagnostics

    Raises:
      None: Cache failures are converted to warnings so callers can preserve
      successful draft generation output.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: overwrite-runtime-state
    @harbor.behavior: writes latest draft runtime cache only; safe additive
      helper for `harbor log draft`; does not write reports/diary and does not
      change caller exit semantics on cache failure
    """
    root = Path(repo_root or Path.cwd()).resolve()
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    log_root = workspace_paths.state_root / "log"
    markdown_path = log_root / "latest-draft.md"
    json_path = log_root / "latest-draft.json"
    timestamp = created_at or datetime.now(timezone.utc)
    markdown_display = _to_repo_relative_display(markdown_path, repo_root=root)
    json_display = _to_repo_relative_display(json_path, repo_root=root)

    result: Dict[str, Any] = {
        "markdown_path": None,
        "json_path": None,
        "markdown_path_display": markdown_display,
        "json_path_display": json_display,
        "warnings": [],
    }

    try:
        log_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        result["warnings"].append(
            f"Failed to create latest draft cache directory '{_to_repo_relative_display(log_root, repo_root=root)}': {exc}"
        )
        return result

    markdown_text = render_diary_draft_markdown(payload)
    latest_wrapper = {
        "schema_version": LATEST_DRAFT_WRAPPER_SCHEMA_VERSION,
        "kind": DIARY_DRAFT_KIND,
        "created_at": timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "harbor log draft",
        "draft": payload,
        "markdown_path": markdown_display,
    }

    try:
        markdown_path.write_text(markdown_text, encoding="utf-8")
        result["markdown_path"] = markdown_path
    except OSError as exc:
        result["warnings"].append(
            f"Failed to write latest draft markdown cache '{markdown_display}': {exc}"
        )

    try:
        json_path.write_text(json.dumps(latest_wrapper, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        result["json_path"] = json_path
    except OSError as exc:
        result["warnings"].append(
            f"Failed to write latest draft JSON cache '{json_display}': {exc}"
        )

    return result


def resolve_draft_source(
    *,
    repo_root: Optional[Path] = None,
    from_draft: Optional[Path] = None,
    from_latest_draft: bool = False,
) -> Dict[str, Any]:
    """Resolve and parse one authorized draft source for `harbor log write`.

    Behavior:
      - Default source and `--from-latest-draft` both use latest draft runtime
        cache:
          1) `.harbor/state/log/latest-draft.json`
          2) fallback `.harbor/state/log/latest-draft.md`
      - `--from-draft <path>` accepts only:
          - `.harbor/reports/**`
          - `.harbor/state/log/latest-draft.md`
          - `.harbor/state/log/latest-draft.json`
      - Rejects:
          - `.harbor/diary/**`
          - `.env`, `.env.*`
          - `secrets/**`
          - paths outside repo root
          - traversal/unauthorized paths
      - JSON source supports both latest-draft wrapper schema and direct draft
        payload object.
      - Markdown source is returned as text for summary-level extraction only.

    Side Effects:
      - Read-only file access only.
      - Does not write diary, reports, cache, or marker files.

    Returns:
      Dict[str, Any] with stable keys:
      - `source_path`: absolute source path
      - `source_path_display`: repo-relative source path when possible
      - `source_kind`: `json` or `markdown`
      - `draft_payload`: parsed draft object when available, else `None`
      - `markdown_text`: markdown text when source is markdown, else `None`
    """
    root = Path(repo_root or Path.cwd()).resolve()
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    log_root = workspace_paths.state_root / "log"
    latest_json = log_root / "latest-draft.json"
    latest_md = log_root / "latest-draft.md"

    if from_draft is not None and from_latest_draft:
        raise LogDraftError("Choose only one draft source: --from-draft or --from-latest-draft.")

    if from_draft is not None:
        source_path = _resolve_allowed_from_draft_path(
            Path(from_draft),
            repo_root=root,
            reports_root=workspace_paths.reports_root,
            latest_md=latest_md,
            latest_json=latest_json,
            diary_root=workspace_paths.diary_root,
        )
    else:
        source_path = _resolve_latest_draft_source(latest_json=latest_json, latest_md=latest_md, repo_root=root)

    return _read_draft_source_file(source_path, repo_root=root)


def build_written_diary_entry(
    *,
    repo_root: Optional[Path] = None,
    from_draft: Optional[Path] = None,
    from_latest_draft: bool = False,
    write_source: str = "harbor log write",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build one structured written diary entry payload from an authorized draft.

    Behavior:
      - Resolves exactly one approved draft source using the same allowlist rules
        as `harbor log write`.
      - Builds one mixed-schema payload that keeps legacy reader fields
        (`ver/ts/author/type/importance/visibility/summary/details`) alongside
        new structured governance fields.
      - Never embeds full markdown bodies, source file bodies, diff bodies, or
        secret-like env values in the returned entry payload.
      - Sanitizes `evidence.changed_files` down to path/status summaries.

    Side Effects:
      - Pure data assembly only; does not write diary files or markers.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: pure
    """
    resolved = resolve_draft_source(
        repo_root=repo_root,
        from_draft=from_draft,
        from_latest_draft=from_latest_draft,
    )
    root = Path(repo_root or Path.cwd()).resolve()
    timestamp = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    draft_payload = dict(resolved.get("draft_payload") or {})
    markdown_text = str(resolved.get("markdown_text") or "")

    if draft_payload:
        summary = _safe_excerpt(str(draft_payload.get("summary") or ""), max_len=300)
        why = _safe_excerpt(str(draft_payload.get("why") or ""), max_len=SAFE_EXCERPT_MAX_LEN)
        suggested = _safe_excerpt(str(draft_payload.get("suggested_diary_entry") or ""), max_len=SAFE_EXCERPT_MAX_LEN)
        details = suggested or why or summary
        if not summary:
            summary = _safe_excerpt(details, max_len=240) or "Written diary entry from latest draft."
        affected_areas = _sanitize_affected_areas(draft_payload.get("affected_areas"))
        contract_impact = _normalize_contract_impact(draft_payload.get("contract_impact"))
        validation = _sanitize_validation(draft_payload.get("validation"))
        evidence = _sanitize_evidence(draft_payload.get("evidence"))
        risks = _sanitize_risks(draft_payload.get("risks"))
    else:
        sections = _extract_markdown_summary_sections(markdown_text)
        summary = (
            sections.get("suggested_diary_entry")
            or sections.get("summary")
            or sections.get("why")
            or sections.get("fallback")
            or "Written diary entry from markdown draft."
        )
        details = sections.get("suggested_diary_entry") or sections.get("summary") or sections.get("fallback") or summary
        affected_areas = {}
        contract_impact = "uncertain"
        validation = {}
        evidence = {"changed_files": []}
        risks = []

    entry: Dict[str, Any] = {
        "schema_version": WRITTEN_DIARY_ENTRY_SCHEMA_VERSION,
        "kind": WRITTEN_DIARY_ENTRY_KIND,
        "timestamp": timestamp,
        "source": str(write_source or "harbor log write"),
        "source_draft": _to_repo_relative_display(Path(resolved["source_path"]), repo_root=root),
        "affected_areas": affected_areas,
        "contract_impact": contract_impact,
        "validation": validation,
        "evidence": evidence,
        "risks": risks,
        "ver": 1,
        "ts": timestamp,
        "author": "harbor",
        "type": "decision",
        "importance": "medium",
        "visibility": "repo",
        "summary": _safe_excerpt(summary, max_len=240) or "Written diary entry from draft.",
        "details": _safe_excerpt(details, max_len=SAFE_EXCERPT_MAX_LEN) or "No additional details.",
    }
    return {"entry": entry, "source": resolved}


def write_diary_entry_from_draft(
    *,
    repo_root: Optional[Path] = None,
    from_draft: Optional[Path] = None,
    from_latest_draft: bool = False,
    write_source: str = "harbor log write",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Write one structured diary entry from an approved draft source.

    Behavior:
      - Uses the same approved draft source resolution as `harbor log write`.
      - Appends exactly one structured JSON line to canonical
        `.harbor/diary/YYYY-MM.jsonl`.
      - Attempts a best-effort `last_log_marker.json` refresh after diary write.
      - Marker write failure must not roll back the already-written diary entry
        and is returned as a warning instead.

    Side Effects:
      - Writes canonical diary JSONL.
      - May write runtime marker state under `.harbor/state/log/`.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once
    """
    root = Path(repo_root or Path.cwd()).resolve()
    built = build_written_diary_entry(
        repo_root=root,
        from_draft=from_draft,
        from_latest_draft=from_latest_draft,
        write_source=write_source,
        now=now,
    )
    entry_payload = dict(built["entry"])
    source_meta = dict(built["source"])

    from harbor.core.diary import DiaryManager

    diary_manager = DiaryManager(repo_root=root)
    diary_path = diary_manager.append_json_line(entry_payload, ts=entry_payload["ts"])
    marker_result = write_last_log_marker(
        entry_payload=entry_payload,
        diary_path=diary_path,
        draft_source_path=Path(source_meta["source_path"]),
        repo_root=root,
    )
    return {
        "entry": entry_payload,
        "diary_path": diary_path,
        "diary_path_display": _to_repo_relative_display(diary_path, repo_root=root),
        "source_draft_display": _to_repo_relative_display(Path(source_meta["source_path"]), repo_root=root),
        "marker_path": marker_result.get("marker_path"),
        "marker_path_display": marker_result.get("marker_path_display"),
        "warnings": list(marker_result.get("warnings") or []),
    }


def write_last_log_marker(
    *,
    entry_payload: Dict[str, Any],
    diary_path: Path,
    draft_source_path: Path,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Best-effort update of `.harbor/state/log/last_log_marker.json`.

    Behavior:
      - Writes one stable English-key JSON object describing the most recent
        successful diary write.
      - Uses runtime state only; marker data is not source-of-truth memory.
      - Marker write failure is downgraded to a warning so callers do not roll
        back the already-written diary entry.

    Side Effects:
      - May create `.harbor/state/log/` and overwrite `last_log_marker.json`.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: overwrite-runtime-state
    """
    root = Path(repo_root or Path.cwd()).resolve()
    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    marker_path = workspace_paths.state_root / "log" / "last_log_marker.json"
    marker_display = _to_repo_relative_display(marker_path, repo_root=root)
    warnings: List[str] = []

    evidence = dict(entry_payload.get("evidence") or {})
    last_git_head = _extract_latest_git_head(evidence)
    last_snapshot = _extract_latest_snapshot_timestamp(evidence)
    payload = {
        "schema_version": "1.0",
        "last_log_at": str(entry_payload.get("ts") or entry_payload.get("timestamp") or ""),
        "last_draft_path": _to_repo_relative_display(draft_source_path, repo_root=root),
        "last_git_head": last_git_head or "",
        "last_snapshot": last_snapshot or "",
        "diary_path": _to_repo_relative_display(diary_path, repo_root=root),
    }
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        warnings.append(f"Failed to write last log marker '{marker_display}': {exc}")
    return {"marker_path": marker_path, "marker_path_display": marker_display, "warnings": warnings}


def build_log_write_preview(
    *,
    repo_root: Optional[Path] = None,
    from_draft: Optional[Path] = None,
    from_latest_draft: bool = False,
) -> Dict[str, str]:
    """Build summary-level preview data for interactive `harbor log write`.

    Behavior:
      - Resolves one approved draft source and derives summary-level preview
        fields only.
      - Returns summary/details/source metadata suitable for confirmation UI.
      - Does not expose full markdown bodies, file bodies, or diff bodies.

    Side Effects:
      - Read-only draft source access only.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    built = build_written_diary_entry(
        repo_root=repo_root,
        from_draft=from_draft,
        from_latest_draft=from_latest_draft,
        write_source="harbor log write",
    )
    entry = dict(built["entry"])
    source = dict(built["source"])
    return {
        "summary": str(entry.get("summary") or ""),
        "details": str(entry.get("details") or ""),
        "source_draft": str(source.get("source_path_display") or ""),
    }


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


def _resolve_latest_draft_source(*, latest_json: Path, latest_md: Path, repo_root: Path) -> Path:
    if latest_json.exists():
        return latest_json.resolve()
    if latest_md.exists():
        return latest_md.resolve()
    raise LogDraftError(
        "No latest draft found. Run `harbor log draft` first (or `harbor log draft --since-last-accept`)."
    )


def _resolve_allowed_from_draft_path(
    path: Path,
    *,
    repo_root: Path,
    reports_root: Path,
    latest_md: Path,
    latest_json: Path,
    diary_root: Path,
) -> Path:
    candidate = path if path.is_absolute() else (repo_root / path)
    resolved = candidate.resolve()
    try:
        rel = resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise LogDraftError(f"Unsafe --from-draft path (outside repo): '{resolved.as_posix()}'.") from exc
    rel_posix = rel.as_posix()
    rel_lower = rel_posix.lower()

    if _is_within(resolved, diary_root.resolve()):
        raise LogDraftError("Unsafe --from-draft path: `.harbor/diary/**` is not allowed.")
    if _is_env_or_secrets_path(rel_lower):
        raise LogDraftError("Unsafe --from-draft path: env/secrets paths are not allowed.")

    allowed = (
        _is_within(resolved, reports_root.resolve())
        or resolved == latest_md.resolve()
        or resolved == latest_json.resolve()
    )
    if not allowed:
        raise LogDraftError(
            "Unsafe --from-draft path: only `.harbor/reports/**` or `.harbor/state/log/latest-draft.md|json` are allowed."
        )
    if not resolved.exists() or not resolved.is_file():
        raise LogDraftError(f"Draft source file not found: '{rel_posix}'.")
    return resolved


def _read_draft_source_file(path: Path, *, repo_root: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    display = _to_repo_relative_display(path, repo_root=repo_root)
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise LogDraftError(f"Failed to decode draft JSON '{display}' as UTF-8: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise LogDraftError(f"Failed to parse draft JSON '{display}': {exc}") from exc
        if not isinstance(payload, dict):
            raise LogDraftError(f"Draft JSON '{display}' must contain an object.")
        if isinstance(payload.get("draft"), dict):
            draft_payload = dict(payload.get("draft") or {})
        else:
            draft_payload = dict(payload)
        return {
            "source_path": path,
            "source_path_display": display,
            "source_kind": "json",
            "draft_payload": draft_payload,
            "markdown_text": None,
        }
    if suffix in {".md", ".markdown"}:
        try:
            markdown_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise LogDraftError(f"Failed to decode markdown draft '{display}' as UTF-8: {exc}") from exc
        except OSError as exc:
            raise LogDraftError(f"Unable to read markdown draft '{display}': {exc}") from exc
        return {
            "source_path": path,
            "source_path_display": display,
            "source_kind": "markdown",
            "draft_payload": None,
            "markdown_text": markdown_text,
        }
    raise LogDraftError(f"Unsupported draft source format for '{display}'. Use .json or .md.")


def _extract_markdown_summary_sections(markdown_text: str) -> Dict[str, str]:
    sections = {
        "suggested_diary_entry": _safe_excerpt(_extract_markdown_section(markdown_text, "Suggested Diary Entry"), max_len=SAFE_EXCERPT_MAX_LEN),
        "summary": _safe_excerpt(_extract_markdown_section(markdown_text, "Summary"), max_len=SAFE_EXCERPT_MAX_LEN),
        "why": _safe_excerpt(_extract_markdown_section(markdown_text, "Why"), max_len=SAFE_EXCERPT_MAX_LEN),
    }
    fallback = _extract_first_safe_text_block(markdown_text)
    if fallback:
        sections["fallback"] = fallback
    return sections


def _extract_markdown_section(markdown_text: str, heading: str) -> str:
    lines = str(markdown_text or "").splitlines()
    target = heading.strip().lower()
    in_section = False
    collected: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            normalized = stripped.lstrip("#").strip().lower()
            if in_section:
                break
            in_section = normalized == target
            continue
        if in_section:
            collected.append(line)
    return "\n".join(collected).strip()


def _extract_first_safe_text_block(markdown_text: str) -> str:
    sanitized = _sanitize_markdown_text(markdown_text)
    if not sanitized:
        return ""
    block: List[str] = []
    for raw_line in sanitized.splitlines():
        line = raw_line.strip()
        if not line:
            if block:
                break
            continue
        if line.startswith("#"):
            continue
        block.append(line)
        if len(" ".join(block)) >= SAFE_EXCERPT_MAX_LEN:
            break
    return _safe_excerpt(" ".join(block), max_len=SAFE_EXCERPT_MAX_LEN)


def _sanitize_markdown_text(markdown_text: str) -> str:
    out: List[str] = []
    in_fence = False
    for raw_line in str(markdown_text or "").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        lower = stripped.lower()
        if lower.startswith("diff --git") or lower.startswith("index ") or lower.startswith("@@"):
            continue
        if lower.startswith("--- ") or lower.startswith("+++ "):
            continue
        if re.match(r"^[A-Z0-9_]{2,}\s*=\s*.+$", stripped):
            continue
        stripped = re.sub(
            r"(?i)\b(secret|token|password|passwd|api[_-]?key|credential)\b\s*[:=]\s*[^\s]+",
            r"\1=[REDACTED]",
            stripped,
        )
        out.append(stripped)
    return "\n".join(out).strip()


def _safe_excerpt(text: str, *, max_len: int = SAFE_EXCERPT_MAX_LEN) -> str:
    cleaned = " ".join(_sanitize_markdown_text(text).split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


def _sanitize_affected_areas(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    output: Dict[str, Any] = {}
    for key, val in value.items():
        key_s = str(key)
        if isinstance(val, list):
            output[key_s] = [str(item) for item in val]
        elif isinstance(val, dict):
            output[key_s] = {str(k): str(v) for k, v in val.items()}
        else:
            output[key_s] = str(val)
    return output


def _normalize_contract_impact(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"yes", "no", "uncertain"}:
        return normalized
    return "uncertain"


def _sanitize_validation(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    output: Dict[str, str] = {}
    for key, val in value.items():
        output[str(key)] = str(val)
    return output


def _sanitize_evidence(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {"changed_files": []}
    changed_files: List[Dict[str, str]] = []
    for item in list(value.get("changed_files") or []):
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").replace("\\", "/").strip()
        if not path:
            continue
        changed_files.append({"path": path, "status": str(item.get("status") or "").strip()})
    output: Dict[str, Any] = {"changed_files": changed_files}
    snapshots: List[Dict[str, Any]] = []
    for item in list(value.get("snapshots") or []):
        if not isinstance(item, dict):
            continue
        snapshots.append(
            {
                "event": str(item.get("event") or ""),
                "timestamp": str(item.get("timestamp") or ""),
                "git_head": str(item.get("git_head") or ""),
            }
        )
    if snapshots:
        output["snapshots"] = snapshots
    reports: List[Dict[str, Any]] = []
    for item in list(value.get("reports") or []):
        if not isinstance(item, dict):
            continue
        reports.append(
            {
                "command": str(item.get("command") or ""),
                "status": str(item.get("status") or ""),
                "path": str(item.get("path") or ""),
            }
        )
    if reports:
        output["reports"] = reports
    return output


def _sanitize_risks(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    risks: List[str] = []
    for item in value:
        excerpt = _safe_excerpt(str(item), max_len=200)
        if excerpt:
            risks.append(excerpt)
    return risks


def _extract_latest_git_head(evidence: Dict[str, Any]) -> Optional[str]:
    snapshots = list(evidence.get("snapshots") or [])
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        git_head = str(snapshot.get("git_head") or "").strip()
        if git_head:
            return git_head
    return None


def _extract_latest_snapshot_timestamp(evidence: Dict[str, Any]) -> Optional[str]:
    snapshots = [item for item in list(evidence.get("snapshots") or []) if isinstance(item, dict)]
    snapshots = sorted(snapshots, key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    if not snapshots:
        return None
    stamp = str(snapshots[0].get("timestamp") or "").strip()
    return stamp or None


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _is_env_or_secrets_path(rel_lower: str) -> bool:
    normalized = rel_lower.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    name = parts[-1] if parts else normalized
    if name == ".env" or name.startswith(".env."):
        return True
    return bool(parts and parts[0] == "secrets")


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
