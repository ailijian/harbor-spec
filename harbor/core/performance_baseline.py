from __future__ import annotations

import os
import platform
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence

from harbor.core.audit import build_typescript_semantic_audit_preview
from harbor.core.ddt import DDTScanner
from harbor.core.l2 import collect_all_indexed_modules
from harbor.core.sync import SyncEngine
from harbor.core.verification import validate_typescript_ddt_preview
from harbor.core.workspace import load_workspace_config


@dataclass(frozen=True)
class RuntimeBaselineContextMetrics:
    scan_file_count: int
    indexed_target_count: int
    module_count: int
    ddt_binding_count: int
    preview_binding_count: int
    preview_audit_target_count: Optional[int]

    def to_dict(self) -> Dict[str, Optional[int]]:
        return {
            "scan_file_count": int(self.scan_file_count),
            "indexed_target_count": int(self.indexed_target_count),
            "module_count": int(self.module_count),
            "ddt_binding_count": int(self.ddt_binding_count),
            "preview_binding_count": int(self.preview_binding_count),
            "preview_audit_target_count": (
                int(self.preview_audit_target_count) if self.preview_audit_target_count is not None else None
            ),
        }


@dataclass(frozen=True)
class RuntimeMatrixEntry:
    command: str
    scenario: str
    status: str
    notes: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "scenario": self.scenario,
            "status": self.status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class RuntimeBaselineObservation:
    command: str
    argv: Sequence[str]
    scenario: str
    output_mode: str
    progress_rendered: bool
    writes_files: bool
    wall_time_seconds: float
    cpu_time_seconds: float
    exit_code: int
    scan_file_count: Optional[int]
    indexed_target_count: Optional[int]
    module_count: Optional[int]
    ddt_binding_count: Optional[int]
    preview_binding_count: Optional[int]
    preview_audit_target_count: Optional[int]
    cache_signal: str = "unknown"
    incremental_signal: str = "unknown"
    notes: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "argv": list(self.argv),
            "scenario": self.scenario,
            "output_mode": self.output_mode,
            "progress_rendered": bool(self.progress_rendered),
            "writes_files": bool(self.writes_files),
            "wall_time_seconds": round(float(self.wall_time_seconds), 6),
            "cpu_time_seconds": round(float(self.cpu_time_seconds), 6),
            "exit_code": int(self.exit_code),
            "scan_file_count": int(self.scan_file_count) if self.scan_file_count is not None else None,
            "indexed_target_count": int(self.indexed_target_count) if self.indexed_target_count is not None else None,
            "module_count": int(self.module_count) if self.module_count is not None else None,
            "ddt_binding_count": int(self.ddt_binding_count) if self.ddt_binding_count is not None else None,
            "preview_binding_count": int(self.preview_binding_count) if self.preview_binding_count is not None else None,
            "preview_audit_target_count": (
                int(self.preview_audit_target_count) if self.preview_audit_target_count is not None else None
            ),
            "cache_signal": self.cache_signal,
            "incremental_signal": self.incremental_signal,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class RuntimeHotspotAssessment:
    hotspot: str
    evidence: str
    recommendation: str
    quick_win_candidate: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hotspot": self.hotspot,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "quick_win_candidate": bool(self.quick_win_candidate),
        }


@dataclass(frozen=True)
class RuntimePerformanceBaselineReport:
    title: str
    generated_at: str
    repo_root: str
    scope: str
    environment: Dict[str, str]
    command_matrix: Sequence[RuntimeMatrixEntry]
    observations: Sequence[RuntimeBaselineObservation]
    hotspots: Sequence[RuntimeHotspotAssessment]
    quick_wins: Sequence[str]
    deferred_optimizations: Sequence[str]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return runtime_performance_baseline_report_to_dict(self)


@contextmanager
def _pushd(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def collect_runtime_baseline_context_metrics(repo_root: Path) -> RuntimeBaselineContextMetrics:
    """Collect repository-wide context counts for performance baseline reporting.

    Behavior:
      - Collects current snapshot size, indexed module count, DDT binding count,
        and preview counts without changing workspace files.
      - Falls back to `None` only for semantic-audit preview targets when the
        preview is disabled or unavailable.

    Args:
      repo_root (Path): Repository root to inspect.

    Returns:
      RuntimeBaselineContextMetrics: Read-only count snapshot used by Task 7
        runtime baseline reports.

    @harbor.scope: public
    @harbor.l3_strictness: standard
    @harbor.idempotency: read-only
    """
    root = Path(repo_root).resolve()
    with _pushd(root):
        sync_engine = SyncEngine()
        snapshot = sync_engine.collect_current_snapshot()
        scan_file_count = len(snapshot)
        indexed_target_count = sum(len(items) for items in snapshot.values())
        module_count = len(collect_all_indexed_modules(prefer_fresh_source=True))
        ddt_binding_count = len(DDTScanner().scan_tests())

        loaded = load_workspace_config(root)
        config = dict(loaded.get("config") or {})

        preview_report = validate_typescript_ddt_preview(root, config)
        preview_binding_count = int(getattr(preview_report, "bindings_count", 0) or 0) if preview_report else 0

        preview_audit_target_count: Optional[int] = None
        try:
            status_report = sync_engine.check_status()
            semantic_preview = build_typescript_semantic_audit_preview(root, status_report, config=config)
        except Exception:
            semantic_preview = None
        if semantic_preview is not None:
            preview_audit_target_count = int(getattr(semantic_preview, "targets_count", 0) or 0)

        return RuntimeBaselineContextMetrics(
            scan_file_count=scan_file_count,
            indexed_target_count=indexed_target_count,
            module_count=module_count,
            ddt_binding_count=ddt_binding_count,
            preview_binding_count=preview_binding_count,
            preview_audit_target_count=preview_audit_target_count,
        )


def build_runtime_baseline_observation(
    *,
    command: str,
    argv: Sequence[str],
    scenario: str,
    output_mode: str,
    progress_rendered: bool,
    writes_files: bool,
    wall_time_seconds: float,
    cpu_time_seconds: float,
    exit_code: int,
    context_metrics: RuntimeBaselineContextMetrics,
    cache_signal: str = "unknown",
    incremental_signal: str = "unknown",
    notes: Optional[Sequence[str]] = None,
) -> RuntimeBaselineObservation:
    return RuntimeBaselineObservation(
        command=command,
        argv=tuple(argv),
        scenario=scenario,
        output_mode=output_mode,
        progress_rendered=progress_rendered,
        writes_files=writes_files,
        wall_time_seconds=wall_time_seconds,
        cpu_time_seconds=cpu_time_seconds,
        exit_code=exit_code,
        scan_file_count=context_metrics.scan_file_count,
        indexed_target_count=context_metrics.indexed_target_count,
        module_count=context_metrics.module_count,
        ddt_binding_count=context_metrics.ddt_binding_count,
        preview_binding_count=context_metrics.preview_binding_count,
        preview_audit_target_count=context_metrics.preview_audit_target_count,
        cache_signal=cache_signal,
        incremental_signal=incremental_signal,
        notes=tuple(notes or ()),
    )


def build_runtime_performance_baseline_report(
    *,
    scope: str,
    repo_root: Path,
    command_matrix: Sequence[RuntimeMatrixEntry],
    observations: Sequence[RuntimeBaselineObservation],
    hotspots: Sequence[RuntimeHotspotAssessment],
    quick_wins: Sequence[str],
    deferred_optimizations: Sequence[str],
    recommendation: str,
    generated_at: Optional[str] = None,
) -> RuntimePerformanceBaselineReport:
    root = Path(repo_root).resolve()
    return RuntimePerformanceBaselineReport(
        title="Harbor-spec Runtime Performance Baseline Report",
        generated_at=generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        repo_root=root.as_posix(),
        scope=scope,
        environment={
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
            "executable": Path(sys.executable).as_posix(),
        },
        command_matrix=tuple(command_matrix),
        observations=tuple(observations),
        hotspots=tuple(hotspots),
        quick_wins=tuple(quick_wins),
        deferred_optimizations=tuple(deferred_optimizations),
        recommendation=recommendation,
    )


def runtime_performance_baseline_report_to_dict(report: RuntimePerformanceBaselineReport) -> Dict[str, Any]:
    return {
        "title": report.title,
        "generated_at": report.generated_at,
        "repo_root": report.repo_root,
        "scope": report.scope,
        "environment": dict(report.environment),
        "command_matrix": [entry.to_dict() for entry in report.command_matrix],
        "observations": [item.to_dict() for item in report.observations],
        "hotspots": [item.to_dict() for item in report.hotspots],
        "quick_wins": list(report.quick_wins),
        "deferred_optimizations": list(report.deferred_optimizations),
        "recommendation": report.recommendation,
        "writes_files": False,
    }


def format_runtime_performance_baseline_report(report: RuntimePerformanceBaselineReport) -> str:
    lines: List[str] = [
        f"# {report.title}",
        "",
        f"- Generated at: `{report.generated_at}`",
        f"- Scope: `{report.scope}`",
        f"- Repo root: `{report.repo_root}`",
        f"- Python: `{report.environment.get('python_version', 'unknown')}`",
        f"- Platform: `{report.environment.get('platform', 'unknown')}`",
        "",
        "## Command Matrix",
        "",
    ]
    for entry in report.command_matrix:
        lines.append(f"- `{entry.command}` | scenario=`{entry.scenario}` | status=`{entry.status}`")
        for note in entry.notes:
            lines.append(f"  - {note}")
    lines.extend(
        [
            "",
            "## Observations",
            "",
            "| Command | Scenario | Format | Progress | Wall(s) | CPU(s) | Exit | Files | Targets | Modules | DDT | Preview Bindings | Preview Audit Targets | Cache | Incremental |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in report.observations:
        lines.append(
            "| "
            + " | ".join(
                [
                    item.command,
                    item.scenario,
                    item.output_mode,
                    "yes" if item.progress_rendered else "no",
                    f"{item.wall_time_seconds:.3f}",
                    f"{item.cpu_time_seconds:.3f}",
                    str(item.exit_code),
                    _render_metric_cell(item.scan_file_count),
                    _render_metric_cell(item.indexed_target_count),
                    _render_metric_cell(item.module_count),
                    _render_metric_cell(item.ddt_binding_count),
                    _render_metric_cell(item.preview_binding_count),
                    _render_metric_cell(item.preview_audit_target_count),
                    item.cache_signal,
                    item.incremental_signal,
                ]
            )
            + " |"
        )
        for note in item.notes:
            lines.append(f"- Note `{item.command}`: {note}")
    lines.extend(["", "## Hotspots", ""])
    for hotspot in report.hotspots:
        lines.append(f"- `{hotspot.hotspot}`")
        lines.append(f"  - Evidence: {hotspot.evidence}")
        lines.append(f"  - Recommendation: {hotspot.recommendation}")
        lines.append(f"  - Quick win: {'yes' if hotspot.quick_win_candidate else 'no'}")
    lines.extend(["", "## Quick Wins", ""])
    for item in report.quick_wins:
        lines.append(f"- {item}")
    lines.extend(["", "## Deferred Structural Optimizations", ""])
    for item in report.deferred_optimizations:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommendation", "", f"- {report.recommendation}", ""])
    return "\n".join(lines)


def _render_metric_cell(value: Optional[int]) -> str:
    return str(int(value)) if value is not None else "n/a"
