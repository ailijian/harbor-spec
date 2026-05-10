from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from harbor.core.contract_impact import ContractImpactLevel, contract_impact_report_to_dict
from harbor.core.doctor import FAIL, DoctorReport
from harbor.core.stale import ModuleStaleSummary
from harbor.utils.i18n import t


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
        """将通用 CI failure/advisory 项序列化为 machine-readable JSON-compatible dict。

        此函数是 Harbor CI JSON 输出序列化契约的一部分（用于 `stale --ci` / `doctor --ci`
        以及相关 payload 的稳定字段输出）。

        Behavior:
          - 输出固定包含 `kind`。
          - `module` / `view` / `check` / `status` / `reason` / `suggested_command`
            仅在字段值非 None 时输出（None 字段省略）。
          - 所有文本字段在输出前均进行 sanitize，避免暴露原始绝对路径或未脱敏文本片段。

        Side Effects:
          - 只读序列化；不写文件、不修改索引、不改变任何运行状态。
          - `writes_files` 语义不由本函数改变。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
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


@dataclass
class CheckpointCIItem:
    category: str
    reason: str
    func_id: Optional[str] = None
    file_path: Optional[str] = None
    suggested_action: Optional[str] = None

    def dedupe_key(self) -> Tuple[str, str]:
        func = str(self.func_id or "").strip()
        path = _normalize_checkpoint_key_path(self.file_path)
        return (func, path)

    def to_dict(self) -> dict:
        """将 checkpoint CI failure/advisory 项序列化为 machine-readable JSON-compatible dict。

        此函数输出 shape 是 `harbor checkpoint --ci --format json` 公开契约之一。

        Behavior:
          - 输出固定包含 `category` 与 `reason`。
          - `func_id` / `file_path` / `suggested_action` 仅在字段存在且非空时输出。
          - `file_path` 会进行路径脱敏与规范化，文本字段会执行 sanitize。

        Side Effects:
          - 只读序列化；不写文件、不触发修复、不刷新上下文、不接受 baseline。
          - `writes_files` 语义不由本函数改变。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        payload: Dict[str, object] = {
            "category": _sanitize_json_text(self.category),
            "reason": _sanitize_json_text(self.reason),
        }
        if self.func_id:
            payload["func_id"] = _sanitize_json_text(self.func_id)
        if self.file_path:
            payload["file_path"] = _sanitize_single_path(self.file_path)
        if self.suggested_action:
            payload["suggested_action"] = _sanitize_json_text(self.suggested_action)
        return payload


@dataclass
class CheckpointCIResult:
    command: str
    status: str
    exit_code: int
    summary: dict
    ci_failures: List[CheckpointCIItem]
    advisory: List[CheckpointCIItem]
    contract_impact: dict
    next_steps: List[str]
    ci: bool = True
    writes_files: bool = False


def build_checkpoint_ci_result(
    *,
    status_report,
    ddt_report,
    contract_impact_report,
    check_errors: Optional[Sequence[str]] = None,
) -> CheckpointCIResult:
    check_errors = list(check_errors or [])
    failures: List[CheckpointCIItem] = []
    advisory: List[CheckpointCIItem] = []

    for typ, binding, message in list(getattr(ddt_report, "violations", []) or []):
        failures.append(
            CheckpointCIItem(
                category="ddt_binding",
                func_id=str(getattr(binding, "func_id", "") or ""),
                file_path=str(getattr(binding, "file_path", "") or ""),
                reason=f"{typ}: {message}",
                suggested_action=t("cli.ci.checkpoint.action.ddt_binding"),
            )
        )
    for item in list(getattr(ddt_report, "advisory", []) or []):
        binding = getattr(item, "binding", None)
        advisory.append(
            CheckpointCIItem(
                category=str(getattr(item, "category", "") or "ddt_binding_advisory"),
                func_id=str(getattr(binding, "func_id", "") or ""),
                file_path=str(getattr(binding, "file_path", "") or ""),
                reason=str(getattr(item, "message", "") or ""),
                suggested_action=str(getattr(item, "suggested_action", "") or t("cli.ci.checkpoint.action.ddt_baseline_missing")),
            )
        )

    _push_status_failures(
        failures,
        items=list(getattr(status_report, "missing", []) or []),
        category="missing_function",
        reason=t("cli.ci.checkpoint.failure.missing"),
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "untracked", []) or []),
        category="untracked_function",
        reason=t("cli.ci.checkpoint.failure.untracked"),
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "drift", []) or []),
        category="possible_semantic_drift",
        reason=t("cli.ci.checkpoint.failure.drift"),
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "contract_gap", []) or []),
        category="contract_gap",
        reason=t("cli.ci.checkpoint.failure.contract_gap"),
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "contract_parse_error", []) or []),
        category="contract_parse_error",
        reason=t("cli.ci.checkpoint.failure.contract_parse_error"),
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "contract_changed", []) or []),
        category="contract_changed",
        reason=t("cli.ci.checkpoint.failure.contract_changed"),
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "modified", []) or []),
        category="contract_and_body_changed",
        reason=t("cli.ci.checkpoint.failure.contract_and_body_changed"),
    )
    for entry in list(getattr(status_report, "skipped_no_contract", []) or []):
        advisory.append(
            CheckpointCIItem(
                category="skipped_no_contract",
                func_id=str(getattr(entry, "id", "") or ""),
                file_path=str(getattr(entry, "file_path", "") or ""),
                reason=t("cli.ci.checkpoint.failure.skipped_no_contract"),
                suggested_action=t("cli.ci.checkpoint.action.review_and_rerun"),
            )
        )

    confirmed_contract_impact = 0
    possible_contract_impact = 0
    report_payload = contract_impact_report_to_dict(contract_impact_report)
    for finding in list(getattr(contract_impact_report, "findings", []) or []):
        level = getattr(finding, "level", None)
        if level == ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT:
            confirmed_contract_impact += 1
            failures.append(
                CheckpointCIItem(
                    category="confirmed_contract_impact",
                    func_id=str(getattr(finding, "func_id", "") or ""),
                    file_path=str(getattr(finding, "file_path", "") or ""),
                    reason=str(getattr(finding, "reason", "") or t("cli.ci.checkpoint.failure.confirmed_contract_impact")),
                    suggested_action=t("cli.ci.checkpoint.action.confirmed_contract_impact"),
                )
            )
        elif level == ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT:
            possible_contract_impact += 1
            advisory.append(
                CheckpointCIItem(
                    category="possible_contract_impact",
                    func_id=str(getattr(finding, "func_id", "") or ""),
                    file_path=str(getattr(finding, "file_path", "") or ""),
                    reason=str(getattr(finding, "reason", "") or t("cli.ci.checkpoint.failure.possible_contract_impact")),
                    suggested_action=t("cli.ci.checkpoint.action.possible_contract_impact"),
                )
            )
        elif level == ContractImpactLevel.UNKNOWN:
            advisory.append(
                CheckpointCIItem(
                    category="unknown_contract_impact",
                    func_id=str(getattr(finding, "func_id", "") or ""),
                    file_path=str(getattr(finding, "file_path", "") or ""),
                    reason=str(getattr(finding, "reason", "") or t("cli.ci.checkpoint.failure.unknown_contract_impact")),
                    suggested_action=t("cli.ci.checkpoint.action.unknown_contract_impact"),
                )
            )

    for err in check_errors:
        failures.append(
            CheckpointCIItem(
                category="checkpoint_internal_error",
                reason=str(err),
                suggested_action=t("cli.ci.checkpoint.action.internal_error"),
            )
        )

    deduped_failures = _dedupe_checkpoint_items(failures)
    deduped_advisory = _dedupe_checkpoint_items(advisory)
    exit_code = 1 if deduped_failures else 0
    status = "fail" if deduped_failures else "pass"
    summary = {
        "drift": len(list(getattr(status_report, "drift", []) or [])),
        "modified": len(list(getattr(status_report, "modified", []) or [])),
        "contract_changed": len(list(getattr(status_report, "contract_changed", []) or [])),
        "contract_gap": len(list(getattr(status_report, "contract_gap", []) or [])),
        "skipped_no_contract": len(list(getattr(status_report, "skipped_no_contract", []) or [])),
        "contract_parse_error": len(list(getattr(status_report, "contract_parse_error", []) or [])),
        "untracked": len(list(getattr(status_report, "untracked", []) or [])),
        "missing": len(list(getattr(status_report, "missing", []) or [])),
        "ddt_failures": len(list(getattr(ddt_report, "violations", []) or [])),
        "ddt_advisory": len(list(getattr(ddt_report, "advisory", []) or [])),
        "confirmed_contract_impact": confirmed_contract_impact,
        "possible_contract_impact": possible_contract_impact,
    }
    next_steps = _collect_checkpoint_next_steps(deduped_failures)
    return CheckpointCIResult(
        command="checkpoint",
        status=status,
        exit_code=exit_code,
        summary=summary,
        ci_failures=deduped_failures,
        advisory=deduped_advisory,
        contract_impact=report_payload,
        next_steps=next_steps,
    )


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
    """将通用 CIResult 序列化为 checkpoint 之外的公开 CI JSON payload。

    此函数用于 `stale --ci` / `doctor --ci` 等通用 CI 输出契约，返回 JSON-compatible dict。

    Output Contract:
      - 必含键：`command` / `ci` / `status` / `exit_code` / `writes_files` /
        `summary` / `ci_failures` / `advisory` / `next_steps`。
      - `writes_files` 固定为 `false`，表示 CI 门禁输出只读。
      - `summary`、`next_steps` 与条目文本会执行 sanitize（含路径/文本脱敏）。
      - `ci_failures` / `advisory` 的 item 形状由对应 `to_dict()` 契约保证；
        item 内 None 字段会按各自规则省略。

    Side Effects:
      - 只做序列化，不执行修复、不刷新上下文、不接受 baseline。
      - 不写文件、不改变运行状态；`writes_files` 不会被动态改写。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
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
    lines.append(t("cli.ci.title", command=result.command.upper()))
    lines.append(t("cli.ci.mode_enabled"))
    lines.append(
        t(
            "cli.ci.gate_with_exit",
            status=t(f"cli.ci.status.{result.status.lower()}"),
            exit_code=result.exit_code,
        )
    )
    lines.append(f"{t('cli.ci.writes_files')}: false")

    if result.ci_failures:
        lines.append("")
        lines.append(t("cli.ci.blocking_failures"))
        for failure in result.ci_failures:
            payload = failure.to_dict()
            if failure.kind == "view":
                lines.append(
                    f"- {payload.get('module', '')} {payload.get('view', '')} {payload.get('status', '')}: {payload.get('reason', '')}"
                )
            else:
                lines.append(f"- {payload.get('check', '')} {payload.get('status', '')}: {payload.get('reason', '')}")
            if payload.get("suggested_command"):
                lines.append(f"  {t('cli.ci.suggested')}: {payload['suggested_command']}")

    if result.advisory:
        lines.append("")
        lines.append(t("cli.ci.advisory"))
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
        lines.append(t("cli.ci.suggested_next_steps"))
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


def checkpoint_ci_result_to_dict(result: CheckpointCIResult) -> dict:
    """将 CheckpointCIResult 序列化为 `checkpoint --ci` 公开 CI JSON payload。

    此函数是 checkpoint CI JSON 输出契约的一部分，返回 JSON-compatible dict。

    Output Contract:
      - 必含键：`command` / `ci` / `status` / `exit_code` / `writes_files` /
        `summary` / `ci_failures` / `advisory` / `contract_impact` / `next_steps`。
      - `writes_files` 固定为 `false`。
      - `ci_failures` 承载阻断项（如 `contract_gap` / `contract_parse_error` /
        `possible_semantic_drift` / `contract_and_body_changed` / `modified` 等）。
      - `advisory` 保留非阻断项（包括 `ddt_version_baseline_missing`）。
      - 路径与文本字段在输出前会做 sanitize；item 内 None 字段按 item 规则省略。

    Side Effects:
      - 只做序列化，不执行修复、不刷新上下文、不接受 baseline。
      - 不写文件、不改变状态；`writes_files` 语义不被本函数改变。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    return {
        "command": result.command,
        "ci": True,
        "status": result.status,
        "exit_code": result.exit_code,
        "writes_files": False,
        "summary": _sanitize_summary(result.summary),
        "ci_failures": [item.to_dict() for item in result.ci_failures],
        "advisory": [item.to_dict() for item in result.advisory],
        "contract_impact": _sanitize_checkpoint_contract_impact(result.contract_impact),
        "next_steps": [_sanitize_json_text(step) for step in result.next_steps],
    }


def format_checkpoint_ci_result(result: CheckpointCIResult) -> str:
    lines: List[str] = []
    lines.append(t("cli.ci.checkpoint.title"))
    lines.append(t("cli.ci.mode_enabled"))
    lines.append(t("cli.ci.gate", status=t(f"cli.ci.status.{result.status.lower()}")))
    lines.append(f"{t('cli.ci.writes_files')}: false")
    if result.ci_failures:
        lines.append("")
        lines.append(t("cli.ci.blocking_failures"))
        for item in result.ci_failures:
            payload = item.to_dict()
            target = payload.get("func_id") or payload.get("file_path")
            label = t(f"cli.ci.checkpoint.category.{payload['category']}")
            if target:
                lines.append(f"- {label}: {target}")
            else:
                lines.append(f"- {label}: {payload.get('reason', '')}")
    if result.advisory:
        lines.append("")
        lines.append(t("cli.ci.advisory"))
        for item in result.advisory:
            payload = item.to_dict()
            target = payload.get("func_id") or payload.get("file_path")
            label = t(f"cli.ci.checkpoint.category.{payload['category']}")
            if target:
                lines.append(f"- {label}: {target}")
            else:
                lines.append(f"- {label}: {payload.get('reason', '')}")
    if result.next_steps:
        lines.append("")
        lines.append(t("cli.ci.next_steps"))
        for step in result.next_steps:
            lines.append(f"- {step}")
    return "\n".join(lines)


def _push_status_failures(failures: List[CheckpointCIItem], *, items: Sequence[object], category: str, reason: str) -> None:
    for entry in items:
        failures.append(
            CheckpointCIItem(
                category=category,
                func_id=str(getattr(entry, "id", "") or ""),
                file_path=str(getattr(entry, "file_path", "") or ""),
                reason=reason,
                suggested_action=t("cli.ci.checkpoint.action.review_and_rerun"),
            )
        )


def _dedupe_checkpoint_items(items: Sequence[CheckpointCIItem]) -> List[CheckpointCIItem]:
    priority = {
        "checkpoint_internal_error": 0,
        "ddt_binding": 1,
        "contract_and_body_changed": 2,
        "contract_changed": 3,
        "possible_semantic_drift": 4,
        "missing_function": 5,
        "untracked_function": 6,
        "contract_gap": 7,
        "contract_parse_error": 8,
        "confirmed_contract_impact": 9,
        "possible_contract_impact": 10,
        "unknown_contract_impact": 11,
        "skipped_no_contract": 12,
        "ddt_version_baseline_missing": 13,
        "ddt_binding_advisory": 14,
    }
    selected: Dict[Tuple[str, str], CheckpointCIItem] = {}
    out: List[CheckpointCIItem] = []
    for item in items:
        key = item.dedupe_key()
        if not key[0] and not key[1]:
            out.append(item)
            continue
        prev = selected.get(key)
        if prev is None or priority.get(item.category, 99) < priority.get(prev.category, 99):
            selected[key] = item
    out.extend(selected.values())
    return sorted(out, key=lambda it: (it.category, it.file_path or "", it.func_id or "", it.reason))


def _collect_checkpoint_next_steps(ci_failures: Sequence[CheckpointCIItem]) -> List[str]:
    if not ci_failures:
        return [
            t("cli.ci.checkpoint.next_steps.pass"),
            t("cli.ci.checkpoint.next_steps.rerun"),
        ]
    return [
        t("cli.ci.checkpoint.next_steps.review_blocking_failures"),
        t("cli.ci.checkpoint.next_steps.run_targeted_tests"),
        t("cli.ci.checkpoint.next_steps.rerun"),
    ]


def _sanitize_checkpoint_contract_impact(payload: dict) -> dict:
    out: Dict[str, object] = {}
    for key, value in (payload or {}).items():
        if isinstance(value, str):
            out[key] = _sanitize_json_text(value)
        elif isinstance(value, list):
            out[key] = [_sanitize_checkpoint_contract_impact(v) if isinstance(v, dict) else _sanitize_json_text(v) if isinstance(v, str) else v for v in value]
        elif isinstance(value, dict):
            out[key] = _sanitize_checkpoint_contract_impact(value)
        else:
            out[key] = value
    return out


def _normalize_checkpoint_key_path(path_text: Optional[str]) -> str:
    raw = str(path_text or "").strip()
    if not raw:
        return ""
    return _sanitize_single_path(raw).strip().lower()
