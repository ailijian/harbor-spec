from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.stale import ModuleStaleSummary, check_module_derived_views_stale
from harbor.core.storage import HarborDB
from harbor.core.sync import SyncEngine
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
        details.append("Harbor root (.harbor/) not found in current workspace.")
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
            details.append(f"Index/database unavailable: {ex}")
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
            details=[f"Index/database unavailable: {ex}"],
            suggestions=[],
        )

    if record_count <= 0:
        details.append("Indexed records not found.")
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
        details=[f"Indexed records available: {record_count}"],
        suggestions=[],
    )


def run_workspace_status_check(sync_engine: Optional[SyncEngine] = None) -> DoctorCheckResult:
    try:
        report = (sync_engine or SyncEngine()).check_status()
    except Exception as ex:
        return DoctorCheckResult(
            name=t("cli.doctor.workspace_status"),
            status=FAIL,
            details=[f"Workspace status check failed: {ex}"],
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
            details=["No Harbor drift detected."],
            suggestions=[],
        )

    details = [f"Changed records detected: {changed_count}"]
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
            details=[f"DDT fast check failed: {ex}"],
            suggestions=[],
        )

    details = [f"Bindings scanned: {len(bindings)}"]
    violations = getattr(report, "violations", []) or []
    if not violations:
        return DoctorCheckResult(
            name=t("cli.doctor.ddt_fast"),
            status=PASS,
            details=details,
            suggestions=[],
        )

    kinds = sorted({str(v[0]) for v in violations})
    details.append(f"Violations: {len(violations)}")
    details.append(f"Types: {', '.join(kinds)}")
    suggestions = ["update DDT binding to explicit l3_version"]
    return DoctorCheckResult(
        name=t("cli.doctor.ddt_fast"),
        status=WARN,
        details=details,
        suggestions=suggestions,
    )


def run_derived_views_check(modules: List[str]) -> DoctorCheckResult:
    if not modules:
        return DoctorCheckResult(
            name=t("cli.doctor.derived_views"),
            status=PASS,
            details=["No modules in selected scope."],
            suggestions=[],
        )

    stale_details: List[str] = []
    suggestions: List[str] = []
    status = PASS
    for module in modules:
        summary: ModuleStaleSummary = check_module_derived_views_stale(module)
        for view_name, view_result in (
            (t("cli.stale.l2"), summary.l2_readme),
            (t("cli.stale.capsule"), summary.module_capsule),
        ):
            if view_result.status == "up_to_date":
                continue
            status = WARN
            detail_status = _derived_view_detail_status(view_result.status)
            reason = view_result.reason or detail_status
            stale_details.append(f"{summary.module} {view_name} {detail_status}: {reason}")
            if view_result.suggested_command:
                suggestions.append(view_result.suggested_command)

    if status == PASS:
        return DoctorCheckResult(
            name=t("cli.doctor.derived_views"),
            status=PASS,
            details=["All derived context views are up to date."],
            suggestions=[],
        )
    return DoctorCheckResult(
        name=t("cli.doctor.derived_views"),
        status=WARN,
        details=stale_details,
        suggestions=_unique(suggestions),
    )


def run_skill_reference_check(skills_root: Path = Path(".agents") / "skills") -> DoctorCheckResult:
    if not skills_root.exists():
        return DoctorCheckResult(
            name=t("cli.doctor.skill_refs"),
            status=SKIP,
            details=[".agents/skills not found."],
            suggestions=[],
        )

    pattern = re.compile(r"docs/harbor/modules/([A-Za-z0-9_\-./]+)/((?:module-card|review-checklist|debug-playbook)\.md)")
    missing_details: List[str] = []
    suggestions: List[str] = []

    for skill_file in skills_root.glob("harbor-debug-*/SKILL.md"):
        try:
            text = skill_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for module, file_name in pattern.findall(text):
            rel = Path("docs/harbor/modules") / module / file_name
            if not rel.exists():
                missing_details.append(
                    f"{skill_file.as_posix()} references missing capsule file: {rel.as_posix()}"
                )
                suggestions.append(f"harbor module seal {module.strip('/')} --write")

    if not missing_details:
        return DoctorCheckResult(
            name=t("cli.doctor.skill_refs"),
            status=PASS,
            details=["Optional skill references look valid."],
            suggestions=[],
        )
    return DoctorCheckResult(
        name=t("cli.doctor.skill_refs"),
        status=WARN,
        details=missing_details,
        suggestions=_unique(suggestions),
    )


def build_doctor_report(scope: str, modules: List[str]) -> DoctorReport:
    checks = [
        run_config_index_check(),
        run_workspace_status_check(),
        run_ddt_fast_check(),
        run_derived_views_check(modules),
        run_skill_reference_check(),
    ]
    return DoctorReport(scope=scope, checks=checks)


def format_doctor_report(report: DoctorReport) -> str:
    lines: List[str] = [t("cli.doctor.title"), f"Scope: {report.scope}", ""]
    for check in report.checks:
        lines.append(f"{check.name}: {_status_text(check.status)}")
        for detail in check.details:
            lines.append(f"- {detail}")
        if check.suggestions:
            lines.append("Suggested:")
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
    base = ["harbor finish --sync-context", "harbor stale", "harbor log", "harbor accept"]
    dynamic: List[str] = []
    for check in checks:
        if check.status in (WARN, FAIL):
            dynamic.extend(check.suggestions)
    return _unique(dynamic + base) if dynamic else []


def _status_to_json(status: str) -> str:
    mapping = {
        PASS: "pass",
        WARN: "warn",
        FAIL: "fail",
        SKIP: "skip",
    }
    return mapping.get(status, status.lower())


def _derived_view_detail_status(status: str) -> str:
    if status == "unknown":
        return "unknown"
    if status == "stale":
        return "stale"
    if status == "up_to_date":
        return "up to date"
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
    candidate = Path(path_text)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            return candidate.name or path_text.replace("\\", "/")
    return path_text.replace("\\", "/")


def _unique(values: List[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
