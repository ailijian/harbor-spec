from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from harbor.core.doctor import FAIL, DoctorReport
from harbor.core.stale import ModuleStaleSummary


@dataclass
class CIFailure:
    kind: str
    module: Optional[str] = None
    view: Optional[str] = None
    check: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    suggested_command: Optional[str] = None

    def to_dict(self) -> dict:
        payload: Dict[str, object] = {"kind": self.kind}
        if self.module is not None:
            payload["module"] = _sanitize_json_text(self.module)
        if self.view is not None:
            payload["view"] = _sanitize_json_text(self.view)
        if self.check is not None:
            payload["check"] = _sanitize_json_text(self.check)
        if self.status is not None:
            payload["status"] = _sanitize_json_text(self.status)
        if self.reason is not None:
            payload["reason"] = _sanitize_json_text(self.reason)
        if self.suggested_command is not None:
            payload["suggested_command"] = _sanitize_json_text(self.suggested_command)
        return payload


@dataclass
class CIResult:
    command: str
    status: str
    exit_code: int
    summary: dict
    ci_failures: List[CIFailure]
    advisory: List[CIFailure]
    next_steps: List[str]
    ci: bool = True
    writes_files: bool = False


def build_stale_ci_result(results: List[ModuleStaleSummary], scope: str) -> CIResult:
    ci_failures: List[CIFailure] = []
    advisory: List[CIFailure] = []
    modules_checked = 0

    for summary in sorted(results, key=lambda item: item.module):
        modules_checked += 1
        module = summary.module
        views = [
            ("l2_readme", summary.l2_readme),
            ("l2_readme_export", summary.l2_readme_export),
            ("module_capsule", summary.module_capsule),
        ]
        for view_name, view in views:
            row = CIFailure(
                kind="view",
                module=module,
                view=view_name,
                status=view.status,
                reason=view.reason,
                suggested_command=view.suggested_command,
            )
            # Canonical blockers in CI mode:
            # - l2_readme stale/unknown
            # - module_capsule stale/unknown
            if view_name in ("l2_readme", "module_capsule") and view.status in ("stale", "unknown"):
                ci_failures.append(row)
            elif view.status != "up_to_date":
                advisory.append(row)

    exit_code = 1 if ci_failures else 0
    status = "fail" if ci_failures else "pass"
    next_steps = _collect_next_steps(ci_failures, advisory)
    summary = {
        "scope": scope,
        "modules_checked": modules_checked,
        "ci_failures": len(ci_failures),
        "advisory_items": len(advisory),
    }
    return CIResult(
        command="stale",
        status=status,
        exit_code=exit_code,
        summary=summary,
        ci_failures=ci_failures,
        advisory=advisory,
        next_steps=next_steps,
    )


def build_doctor_ci_result(report: DoctorReport) -> CIResult:
    ci_failures: List[CIFailure] = []
    advisory: List[CIFailure] = []

    for check in report.checks:
        status = str(check.status or "").upper()
        details = "; ".join(check.details or [])
        suggested = (check.suggestions or [None])[0]
        row = CIFailure(
            kind="check",
            check=check.name,
            status=status,
            reason=details or None,
            suggested_command=suggested,
        )
        # P1-1A policy: doctor --ci blocks only explicit FAIL checks.
        if status == FAIL:
            ci_failures.append(row)
        elif status in ("WARN", "SKIP"):
            advisory.append(row)

    exit_code = 1 if ci_failures else 0
    status = "fail" if ci_failures else "pass"
    summary = {
        "scope": report.scope,
        "checks_total": len(report.checks),
        "fail": sum(1 for c in report.checks if str(c.status).upper() == "FAIL"),
        "warn": sum(1 for c in report.checks if str(c.status).upper() == "WARN"),
        "skip": sum(1 for c in report.checks if str(c.status).upper() == "SKIP"),
        "pass": sum(1 for c in report.checks if str(c.status).upper() == "PASS"),
    }
    next_steps = _collect_next_steps(ci_failures, advisory)
    return CIResult(
        command="doctor",
        status=status,
        exit_code=exit_code,
        summary=summary,
        ci_failures=ci_failures,
        advisory=advisory,
        next_steps=next_steps,
    )


def ci_result_to_dict(result: CIResult) -> dict:
    return {
        "command": result.command,
        "ci": True,
        "status": result.status,
        "exit_code": result.exit_code,
        "writes_files": False,
        "summary": _sanitize_summary(result.summary),
        "ci_failures": [item.to_dict() for item in result.ci_failures],
        "advisory": [item.to_dict() for item in result.advisory],
        "next_steps": [_sanitize_json_text(step) for step in result.next_steps],
    }


def format_ci_result(result: CIResult) -> str:
    lines = []
    lines.append(f"{result.command.upper()} CI mode enabled")
    lines.append(f"CI gate: {result.status.upper()} (exit {result.exit_code})")
    lines.append("writes_files: false")

    if result.ci_failures:
        lines.append("")
        lines.append("Blocking failures:")
        for failure in result.ci_failures:
            payload = failure.to_dict()
            if failure.kind == "view":
                lines.append(
                    f"- {payload.get('module', '')} {payload.get('view', '')} {payload.get('status', '')}: {payload.get('reason', '')}"
                )
            else:
                lines.append(f"- {payload.get('check', '')} {payload.get('status', '')}: {payload.get('reason', '')}")
            if payload.get("suggested_command"):
                lines.append(f"  Suggested: {payload['suggested_command']}")

    if result.advisory:
        lines.append("")
        lines.append("Advisory:")
        for item in result.advisory:
            payload = item.to_dict()
            if item.kind == "view":
                lines.append(
                    f"- {payload.get('module', '')} {payload.get('view', '')} {payload.get('status', '')}: {payload.get('reason', '')}"
                )
            else:
                lines.append(f"- {payload.get('check', '')} {payload.get('status', '')}: {payload.get('reason', '')}")

    if result.next_steps:
        lines.append("")
        lines.append("Suggested next steps:")
        for step in result.next_steps:
            lines.append(f"- {step}")
    return "\n".join(lines)


def _collect_next_steps(ci_failures: List[CIFailure], advisory: List[CIFailure]) -> List[str]:
    seen = set()
    out: List[str] = []

    def _push(cmd: Optional[str]) -> None:
        normalized = str(cmd or "").strip()
        if not normalized:
            return
        blocked_prefixes = ("harbor accept", "harbor log", "harbor lock")
        if normalized.startswith(blocked_prefixes):
            return
        allowed_prefixes = (
            "harbor docs",
            "harbor module seal",
            "harbor stale",
            "harbor doctor",
        )
        if not normalized.startswith(allowed_prefixes):
            return
        if normalized in seen:
            return
        seen.add(normalized)
        out.append(normalized)

    for item in ci_failures + advisory:
        _push(item.suggested_command)
    _push("harbor stale")
    _push("harbor doctor")
    return out


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


def _sanitize_summary(summary: dict) -> dict:
    out: Dict[str, object] = {}
    for key, value in summary.items():
        if isinstance(value, str):
            out[key] = _sanitize_json_text(value)
        else:
            out[key] = value
    return out
