from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Set

from harbor.core.context_integrity import parse_frontmatter
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.stale import ModuleStaleSummary, check_module_derived_views_stale
from harbor.core.storage import HarborDB
from harbor.core.sync import SyncEngine
from harbor.core.workspace import load_workspace_config, load_workspace_paths, parse_workspace_export_options
from harbor.utils.i18n import t

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"


@dataclass
class DoctorCheckResult:
    name: str
    status: str
    details: List[str]
    suggestions: List[str]

    def to_dict(self) -> dict:
        """Serialize one doctor check result into stable JSON output.

        Behavior:
          - Converts internal status labels to stable lowercase JSON values.
          - Sanitizes detail and suggestion strings to avoid leaking
            machine-local absolute paths.
          - Preserves a fixed key set for CLI JSON consumers.

        Returns:
          dict: Stable JSON-compatible doctor check payload.

        Side Effects:
          - Writes no files.

        Idempotency:
          - Deterministic for the same check state.

        Security:
          - Must not expose machine-local absolute paths in JSON fields.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        return {
            "name": self.name,
            "status": _status_to_json(self.status),
            "details": [_sanitize_json_text(detail) for detail in self.details],
            "suggestions": [_sanitize_json_text(suggestion) for suggestion in self.suggestions],
        }


@dataclass
class DoctorReport:
    scope: str
    checks: List[DoctorCheckResult]

    def to_dict(self, *, command: str = "doctor") -> dict:
        """Serialize the aggregated doctor report into stable JSON output.

        Behavior:
          - Preserves stable top-level keys for CLI/CI JSON consumers.
          - Aggregates pass/warn/fail/skip counts from contained checks.
          - Marks output as advisory and read-only metadata.

        Args:
          command (str): Command name to expose in the JSON payload.

        Returns:
          dict: Stable JSON-compatible doctor report payload.

        Side Effects:
          - Writes no files.

        Idempotency:
          - Deterministic for the same report state.

        Security:
          - Must not expose machine-local absolute paths through nested checks.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        summary = {
            "pass": sum(1 for c in self.checks if c.status == PASS),
            "warn": sum(1 for c in self.checks if c.status == WARN),
            "fail": sum(1 for c in self.checks if c.status == FAIL),
            "skip": sum(1 for c in self.checks if c.status == SKIP),
        }
        overall_status = "pass"
        if summary["fail"] > 0:
            overall_status = "fail"
        elif summary["warn"] > 0:
            overall_status = "warn"

        return {
            "command": command,
            "scope": self.scope,
            "status": overall_status,
            "checks": [check.to_dict() for check in self.checks],
            "summary": summary,
            "advisory": True,
            "writes_files": False,
        }


def run_config_index_check() -> DoctorCheckResult:
    details: List[str] = []
    suggestions: List[str] = []
    harbor_root = Path(".harbor")
    if not harbor_root.exists():
        details.append(t("cli.doctor.detail.harbor_root_missing"))
        suggestions.append("harbor init")
        try:
            db = HarborDB(project_root=Path.cwd())
            record_count = len(db.get_all_files())
            if record_count <= 0:
                suggestions.append("harbor lock")
                suggestions.append("harbor adopt <path>")
            return DoctorCheckResult(
                name=t("cli.doctor.config_index"),
                status=WARN,
                details=details,
                suggestions=_unique(suggestions),
            )
        except Exception as ex:
            details.append(t("cli.doctor.detail.index_unavailable", error=str(ex)))
            return DoctorCheckResult(
                name=t("cli.doctor.config_index"),
                status=FAIL,
                details=details,
                suggestions=_unique(suggestions),
            )

    try:
        db = HarborDB(project_root=Path.cwd())
        record_count = len(db.get_all_files())
    except Exception as ex:
        return DoctorCheckResult(
            name=t("cli.doctor.config_index"),
            status=FAIL,
            details=[t("cli.doctor.detail.index_unavailable", error=str(ex))],
            suggestions=[],
        )

    if record_count <= 0:
        details.append(t("cli.doctor.detail.indexed_records_not_found"))
        suggestions.extend(["harbor lock", "harbor adopt <path>"])
        return DoctorCheckResult(
            name=t("cli.doctor.config_index"),
            status=WARN,
            details=details,
            suggestions=_unique(suggestions),
        )
    return DoctorCheckResult(
        name=t("cli.doctor.config_index"),
        status=PASS,
        details=[t("cli.doctor.detail.indexed_records_available", count=record_count)],
        suggestions=[],
    )


def run_workspace_status_check(sync_engine: Optional[SyncEngine] = None) -> DoctorCheckResult:
    try:
        report = (sync_engine or SyncEngine()).check_status()
    except Exception as ex:
        return DoctorCheckResult(
            name=t("cli.doctor.workspace_status"),
            status=FAIL,
            details=[t("cli.doctor.detail.workspace_status_failed", error=str(ex))],
            suggestions=[],
        )

    counts = getattr(report, "counts", None) or {
        "drift": len(getattr(report, "drift", [])),
        "modified": len(getattr(report, "modified", [])),
        "contract_changed": len(getattr(report, "contract_changed", [])),
        "untracked": len(getattr(report, "untracked", [])),
        "missing": len(getattr(report, "missing", [])),
    }
    changed_count = sum(int(v) for v in counts.values())
    if changed_count <= 0:
        return DoctorCheckResult(
            name=t("cli.doctor.workspace_status"),
            status=PASS,
            details=[t("cli.doctor.detail.no_drift")],
            suggestions=[],
        )

    details = [t("cli.doctor.detail.changed_records_detected", count=changed_count)]
    for key in ("drift", "modified", "contract_changed", "untracked", "missing"):
        value = int(counts.get(key, 0))
        if value > 0:
            details.append(f"{key}: {value}")
    return DoctorCheckResult(
        name=t("cli.doctor.workspace_status"),
        status=WARN,
        details=details,
        suggestions=["harbor checkpoint", "harbor finish"],
    )


def run_ddt_fast_check(
    scanner: Optional[DDTScanner] = None,
    validator: Optional[DDTValidator] = None,
) -> DoctorCheckResult:
    try:
        bindings = (scanner or DDTScanner()).scan_tests()
        report = (validator or DDTValidator()).validate(bindings)
    except Exception as ex:
        return DoctorCheckResult(
            name=t("cli.doctor.ddt_fast"),
            status=FAIL,
            details=[t("cli.doctor.detail.ddt_fast_failed", error=str(ex))],
            suggestions=[],
        )

    details = [t("cli.doctor.detail.bindings_scanned", count=len(bindings))]
    violations = getattr(report, "violations", []) or []
    if not violations:
        return DoctorCheckResult(
            name=t("cli.doctor.ddt_fast"),
            status=PASS,
            details=details,
            suggestions=[],
        )

    kinds = sorted({str(v[0]) for v in violations})
    details.append(t("cli.doctor.detail.violations", count=len(violations)))
    details.append(t("cli.doctor.detail.violation_types", types=", ".join(kinds)))
    suggestions = ["update DDT binding to explicit l3_version"]
    return DoctorCheckResult(
        name=t("cli.doctor.ddt_fast"),
        status=WARN,
        details=details,
        suggestions=suggestions,
    )


def run_derived_views_check(modules: List[str]) -> DoctorCheckResult:
    """检查模块派生视图状态并汇总为 Doctor 结果。

    Args:
        modules: 需要检查的模块列表（repo-relative module path）。

    Returns:
        DoctorCheckResult: 派生视图检查结果。
            - 当存在 stale/unknown 或 legacy metadata 提示时，状态为 WARN。
            - `disabled` 视图仅记录详情，不单独抬升为 WARN。
    """
    if not modules:
        return DoctorCheckResult(
            name=t("cli.doctor.derived_views"),
            status=PASS,
            details=[t("cli.doctor.detail.no_modules_in_scope")],
            suggestions=[],
        )

    stale_details: List[str] = []
    suggestions: List[str] = []
    status = PASS
    workspace_paths = load_workspace_paths(Path.cwd(), enforce_write_safety=True)
    for module in modules:
        summary: ModuleStaleSummary = check_module_derived_views_stale(module)
        for view_name, view_result in (
            (t("cli.stale.l2"), summary.l2_readme),
            (t("cli.stale.l2_export"), summary.l2_readme_export),
            (t("cli.stale.capsule"), summary.module_capsule),
        ):
            if view_result.status == "up_to_date":
                continue
            if view_result.status == "disabled":
                stale_details.append(
                    f"{summary.module} {view_name} {t('cli.doctor.status.disabled')}: {view_result.reason or t('cli.doctor.status.disabled')}"
                )
                continue
            status = _merge_status(status, WARN)
            detail_status = _derived_view_detail_status(view_result.status)
            reason = view_result.reason or detail_status
            stale_details.append(f"{summary.module} {view_name} {detail_status}: {reason}")
            if view_result.suggested_command:
                suggestions.append(view_result.suggested_command)

        module_rel = summary.module.strip("/")
        l2_path = workspace_paths.l2_view_root / module_rel / "README.md"
        capsule_dir = workspace_paths.modules_view_root / module_rel
        frontmatter_checks = [
            (l2_path, f"{summary.module} {t('cli.stale.l2')}"),
            (capsule_dir / "module-card.md", f"{summary.module} module-card.md"),
            (capsule_dir / "review-checklist.md", f"{summary.module} review-checklist.md"),
            (capsule_dir / "debug-playbook.md", f"{summary.module} debug-playbook.md"),
        ]
        for check_path, label in frontmatter_checks:
            if not check_path.exists():
                continue
            parsed = _parse_generated_frontmatter_safely(check_path)
            if parsed is None:
                status = _merge_status(status, WARN)
                stale_details.append(
                    f"{label} frontmatter {t('cli.doctor.status.unknown')}: {t('cli.doctor.detail.frontmatter_missing_or_parse_failed')}"
                )
                continue
            if not parsed:
                status = _merge_status(status, WARN)
                stale_details.append(f"{label} frontmatter {t('cli.doctor.status.unknown')}: {t('cli.doctor.detail.frontmatter_empty')}")

    legacy_meta = Path(".harbor") / "l2_meta.json"
    if legacy_meta.exists():
        status = _merge_status(status, WARN)
        stale_details.append(t("cli.doctor.derived_views.legacy_meta_detected"))
        stale_details.append(t("cli.doctor.derived_views.legacy_meta_canonical"))

    legacy_diary_pattern = Path("specs") / "diary"
    has_legacy_diary_jsonl = any(path.is_file() for path in legacy_diary_pattern.glob("*.jsonl"))
    if has_legacy_diary_jsonl:
        status = _merge_status(status, WARN)
        stale_details.append(t("cli.doctor.derived_views.legacy_diary_advisory"))
        stale_details.append(t("cli.doctor.derived_views.legacy_diary_canonical"))
        stale_details.append(t("cli.doctor.derived_views.legacy_diary_new_writes"))
        stale_details.append(t("cli.doctor.derived_views.legacy_diary_no_auto_migration"))

    if status == PASS and not stale_details:
        return DoctorCheckResult(
            name=t("cli.doctor.derived_views"),
            status=PASS,
            details=[t("cli.doctor.detail.derived_views_up_to_date")],
            suggestions=[],
        )
    return DoctorCheckResult(
        name=t("cli.doctor.derived_views"),
        status=status,
        details=stale_details,
        suggestions=_unique(suggestions),
    )


def run_skill_reference_check(skills_root: Path = Path(".agents") / "skills") -> DoctorCheckResult:
    if not skills_root.exists():
        return DoctorCheckResult(
            name=t("cli.doctor.skill_refs"),
            status=SKIP,
            details=[t("cli.doctor.detail.skills_not_found")],
            suggestions=[],
        )

    canonical_pattern = re.compile(
        r"\.harbor/views/modules/([A-Za-z0-9_\-./]+)/((?:module-card|review-checklist|debug-playbook)\.md)"
    )
    legacy_pattern = re.compile(r"docs/harbor/modules/([A-Za-z0-9_\-./]+)/((?:module-card|review-checklist|debug-playbook)\.md)")
    missing_details: List[str] = []
    suggestions: List[str] = []
    config = (load_workspace_config(Path.cwd()).get("config") or {})
    export_options = parse_workspace_export_options(config)
    export_enabled = bool((((export_options.get("views", {}) or {}).get("docs", {}) or {}).get("enabled")))

    for skill_file in skills_root.glob("harbor-debug-*/SKILL.md"):
        try:
            text = skill_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for module, file_name in canonical_pattern.findall(text):
            rel = Path(".harbor/views/modules") / module / file_name
            if not rel.exists():
                missing_details.append(
                    f"{skill_file.as_posix()} references missing capsule file: {rel.as_posix()}"
                )
                suggestions.append(f"harbor module seal {module.strip('/')} --write")
        for module, file_name in legacy_pattern.findall(text):
            rel = Path("docs/harbor/modules") / module / file_name
            if not rel.exists():
                missing_details.append(
                    f"{skill_file.as_posix()} references missing legacy capsule file: {rel.as_posix()}"
                )
                suggestions.append(f"harbor module seal {module.strip('/')} --write")
                continue
            if not export_enabled:
                missing_details.append(
                    f"{skill_file.as_posix()} references legacy capsule path (non-canonical): {rel.as_posix()}"
                )

    if not missing_details:
        return DoctorCheckResult(
            name=t("cli.doctor.skill_refs"),
            status=PASS,
            details=[t("cli.doctor.detail.skill_refs_valid")],
            suggestions=[],
        )
    return DoctorCheckResult(
        name=t("cli.doctor.skill_refs"),
        status=WARN,
        details=missing_details,
        suggestions=_unique(suggestions),
    )


def build_doctor_report(
    scope: str,
    modules: List[str],
    *,
    on_phase_start: Optional[Callable[[str], None]] = None,
) -> DoctorReport:
    checks = [
        _emit_doctor_phase(on_phase_start, "config_index", run_config_index_check),
        _emit_doctor_phase(on_phase_start, "workspace_status", run_workspace_status_check),
        _emit_doctor_phase(on_phase_start, "ddt_fast", run_ddt_fast_check),
        _emit_doctor_phase(on_phase_start, "derived_views", run_derived_views_check, modules),
        _emit_doctor_phase(on_phase_start, "skill_refs", run_skill_reference_check),
    ]
    return DoctorReport(scope=scope, checks=checks)


def _emit_doctor_phase(
    callback: Optional[Callable[[str], None]],
    phase_name: str,
    fn: Callable,
    *args,
):
    if callback is not None:
        callback(phase_name)
    return fn(*args)


def format_doctor_report(report: DoctorReport) -> str:
    lines: List[str] = [t("cli.doctor.title"), f"{t('cli.doctor.scope_label')}: {report.scope}", ""]
    for check in report.checks:
        lines.append(f"{check.name}: {_status_text(check.status)}")
        for detail in check.details:
            lines.append(f"- {detail}")
        if check.suggestions:
            lines.append(t("cli.doctor.suggested"))
            for suggestion in check.suggestions:
                lines.append(f"- {suggestion}")
        lines.append("")

    warn_count = sum(1 for c in report.checks if c.status == WARN)
    fail_count = sum(1 for c in report.checks if c.status == FAIL)
    if fail_count > 0:
        lines.append(t("cli.doctor.summary.warnings", count=warn_count + fail_count))
    elif warn_count > 0:
        lines.append(t("cli.doctor.summary.warnings", count=warn_count))
    else:
        lines.append(t("cli.doctor.summary.healthy"))
    lines.append(t("cli.doctor.no_changes_made"))

    suggested = _collect_next_steps(report.checks)
    if suggested:
        lines.append("")
        lines.append(t("cli.doctor.suggested_next_steps"))
        for cmd in suggested:
            lines.append(f"- {cmd}")
    return "\n".join(lines)


def _status_text(status: str) -> str:
    mapping = {
        PASS: t("cli.doctor.pass"),
        WARN: t("cli.doctor.warn"),
        FAIL: t("cli.doctor.fail"),
        SKIP: t("cli.doctor.skip"),
    }
    return mapping.get(status, status)


def _collect_next_steps(checks: List[DoctorCheckResult]) -> List[str]:
    base = [
        "harbor checkpoint",
        "harbor finish --sync-context",
        "harbor stale",
        "harbor doctor",
    ]
    dynamic: List[str] = []
    for check in checks:
        if check.status in (WARN, FAIL):
            dynamic.extend(check.suggestions)
    return _filter_safe_next_steps(_unique(dynamic + base)) if dynamic else []


def _filter_safe_next_steps(steps: List[str]) -> List[str]:
    out: List[str] = []
    blocked_prefixes = ("harbor accept", "harbor log", "harbor lock")
    for step in steps:
        normalized = str(step or "").strip()
        if not normalized:
            continue
        if normalized.startswith(blocked_prefixes):
            continue
        out.append(normalized)
    return out


def _status_to_json(status: str) -> str:
    mapping = {
        PASS: "pass",
        WARN: "warn",
        FAIL: "fail",
        SKIP: "skip",
    }
    return mapping.get(status, status.lower())


def _merge_status(current: str, incoming: str) -> str:
    rank = {PASS: 0, WARN: 1, FAIL: 2}
    cur_rank = rank.get(current, 0)
    incoming_rank = rank.get(incoming, 0)
    return current if cur_rank >= incoming_rank else incoming


def _derived_view_detail_status(status: str) -> str:
    """将内部 view status 归一化为可展示文本。

    Args:
        status: 视图状态值，如 ``up_to_date``、``stale``、``unknown``、``disabled``。

    Returns:
        str: 面向文本输出的状态描述；未知值会执行 ``_`` 到空格的退化转换。
    """
    if status == "disabled":
        return t("cli.doctor.status.disabled")
    if status == "unknown":
        return t("cli.doctor.status.unknown")
    if status == "stale":
        return t("cli.doctor.status.stale")
    if status == "up_to_date":
        return t("cli.doctor.status.up_to_date")
    return (status or "stale").replace("_", " ")


_WINDOWS_ABS_PATH_RE = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"']+")
_POSIX_ABS_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:[^ \t\r\n\"']+)")


def _sanitize_json_text(value: str) -> str:
    def _replace(match: re.Match) -> str:
        return _sanitize_single_path(match.group(0))

    sanitized = _WINDOWS_ABS_PATH_RE.sub(_replace, value)
    sanitized = _POSIX_ABS_PATH_RE.sub(_replace, sanitized)
    return sanitized


def _sanitize_single_path(path_text: str) -> str:
    raw = str(path_text or "").strip()
    if not raw:
        return ""
    normalized = raw.replace("\\", "/")
    repo_root = Path.cwd().resolve()
    if re.match(r"(?i)^[a-z]:/", normalized) or normalized.startswith("//"):
        marker = f"/{repo_root.name.lower()}/"
        lower = normalized.lower()
        idx = lower.find(marker)
        if idx != -1:
            rel = normalized[idx + len(marker) :].strip("/")
            if rel:
                return rel
        base = Path(normalized.rstrip("/")).name or Path(normalized).name
        return base or normalized
    candidate = Path(normalized)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(repo_root).as_posix()
        except Exception:
            return candidate.name or normalized
    return normalized


def _unique(values: List[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _parse_generated_frontmatter_safely(path: Path) -> Optional[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    parsed = parse_frontmatter(text)
    return parsed
