from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from harbor.adapters.base import ContractSubject
from harbor.core.contract_impact import ContractImpactLevel, contract_impact_report_to_dict
from harbor.core.advice_config import AdviceSettings
from harbor.core.doctor import FAIL, DoctorReport
from harbor.core.repair_guidance import (
    RepairGuidance,
    guidance_for_checkpoint_category,
    guidance_for_doctor_item,
    guidance_for_stale_item,
)
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
    guidance: Optional[RepairGuidance] = None

    def to_dict(self, *, include_guidance: bool = True) -> dict:
        """将通用 CI failure/advisory 项序列化为 machine-readable JSON-compatible dict。

        此函数是 Harbor CI JSON 输出序列化契约的一部分（用于 `stale --ci` / `doctor --ci`
        以及相关 payload 的稳定字段输出）。

        Behavior:
          - 输出固定包含 `kind`。
          - `module` / `view` / `check` / `status` / `reason` / `suggested_command`
            仅在字段值非 None 时输出（None 字段省略）。
          - `guidance` 为 optional additive field：
            仅在 `include_guidance=True` 且 guidance 存在时输出；
            advice=off 路径会传入 `include_guidance=False`，因此不输出 `guidance`。
          - guidance 只提供 deterministic 元数据建议，不调用 LLM，不改变既有字段语义。
          - guidance 不改变 gate 语义：不改变 `exit_code`、blocking/failure 归类或 advisory 归类。
          - 所有文本字段在输出前均进行 sanitize，避免暴露原始绝对路径或未脱敏文本片段。

        Side Effects:
          - 只读序列化；不写文件、不修改索引、不改变任何运行状态。
          - `writes_files` 语义不由本函数改变。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Args:
          include_guidance (bool): 是否输出可选 guidance 附加字段；
            `advice=off` 路径会传入 False，因此不输出 guidance。

        Returns:
          dict: JSON-compatible item dict；None 字段省略；guidance 仅为 deterministic
            advisory metadata，不改变 exit_code/blocking/advisory 语义。
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
        if include_guidance and self.guidance is not None:
            payload["guidance"] = self.guidance.to_dict()
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
    advice_mode: str = "basic"
    include_in_ci_json: bool = True
    include_in_text: bool = True


@dataclass
class CheckpointCIItem:
    category: str
    reason: str
    func_id: Optional[str] = None
    file_path: Optional[str] = None
    target_id: Optional[str] = None
    language: Optional[str] = None
    symbol_kind: Optional[str] = None
    adapter: Optional[str] = None
    suggested_action: Optional[str] = None
    guidance: Optional[RepairGuidance] = None

    def dedupe_key(self) -> Tuple[str, str]:
        func = str(self.func_id or "").strip()
        path = _normalize_checkpoint_key_path(self.file_path)
        return (func, path)

    def to_dict(self, *, include_guidance: bool = True) -> dict:
        """将 checkpoint CI failure/advisory 项序列化为 machine-readable JSON-compatible dict。

        此函数输出 shape 是 `harbor checkpoint --ci --format json` 公开契约之一。

        Behavior:
          - 输出固定包含 `category` 与 `reason`。
          - `func_id` / `file_path` / `suggested_action` 仅在字段存在且非空时输出。
          - `target_id` / `language` / `symbol_kind` / `adapter` 为 additive 字段：
            仅在条目具备对应 identity 信息时输出，不改变既有 gate 语义。
          - `file_path` 会进行路径脱敏与规范化，文本字段会执行 sanitize。
          - `guidance` 为 optional additive field：
            仅在 `include_guidance=True` 且 guidance 存在时输出；
            advice=off 路径会传入 `include_guidance=False`，因此不输出 `guidance`。
          - guidance 为 deterministic metadata，不调用 LLM，不改变既有字段语义。
          - guidance 不改变 `exit_code` / blocking / advisory 判定。

        Side Effects:
          - 只读序列化；不写文件、不触发修复、不刷新上下文、不接受 baseline。
          - `writes_files` 语义不由本函数改变。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Args:
          include_guidance (bool): 是否输出可选 guidance 附加字段；
            `advice=off` 路径会传入 False，因此不输出 guidance。

        Returns:
          dict: JSON-compatible checkpoint item dict；None/空字段按规则省略；
            additive identity 字段（`target_id`/`language`/`symbol_kind`/`adapter`）
            仅在可用时输出，guidance 仅为 deterministic advisory metadata，
            不改变 exit_code/blocking/advisory 语义。
        """
        payload: Dict[str, object] = {
            "category": _sanitize_json_text(self.category),
            "reason": _sanitize_json_text(self.reason),
        }
        if self.func_id:
            payload["func_id"] = _sanitize_json_text(self.func_id)
        if self.file_path:
            payload["file_path"] = _sanitize_single_path(self.file_path)
        if self.target_id:
            payload["target_id"] = _sanitize_json_text(self.target_id)
        if self.language:
            payload["language"] = _sanitize_json_text(self.language)
        if self.symbol_kind:
            payload["symbol_kind"] = _sanitize_json_text(self.symbol_kind)
        if self.adapter:
            payload["adapter"] = _sanitize_json_text(self.adapter)
        if self.suggested_action:
            payload["suggested_action"] = _sanitize_json_text(self.suggested_action)
        if include_guidance and self.guidance is not None:
            payload["guidance"] = self.guidance.to_dict()
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
    advice_mode: str = "basic"
    include_in_ci_json: bool = True
    include_in_text: bool = True


def build_checkpoint_ci_result(
    *,
    status_report,
    ddt_report,
    contract_impact_report,
    check_errors: Optional[Sequence[str]] = None,
    advice_settings: Optional[AdviceSettings] = None,
) -> CheckpointCIResult:
    settings = advice_settings or AdviceSettings()
    check_errors = list(check_errors or [])
    failures: List[CheckpointCIItem] = []
    advisory: List[CheckpointCIItem] = []

    for typ, binding, message in list(getattr(ddt_report, "violations", []) or []):
        defaults = _ddt_identity_defaults(str(getattr(binding, "func_id", "") or ""))
        identity = _derive_checkpoint_identity(
            func_id=str(getattr(binding, "func_id", "") or ""),
            file_path=str(getattr(binding, "file_path", "") or ""),
            source=binding,
            default_language=defaults["language"],
            default_adapter=defaults["adapter"],
        )
        failures.append(
            CheckpointCIItem(
                category="ddt_binding",
                func_id=str(getattr(binding, "func_id", "") or ""),
                file_path=str(getattr(binding, "file_path", "") or ""),
                target_id=identity["target_id"],
                language=identity["language"],
                symbol_kind=identity["symbol_kind"],
                adapter=identity["adapter"],
                reason=f"{typ}: {message}",
                suggested_action=t("cli.ci.checkpoint.action.ddt_binding"),
                guidance=guidance_for_checkpoint_category("ddt_binding") if settings.enabled else None,
            )
        )
    for item in list(getattr(ddt_report, "advisory", []) or []):
        binding = getattr(item, "binding", None)
        defaults = _ddt_identity_defaults(str(getattr(binding, "func_id", "") or ""))
        identity = _derive_checkpoint_identity(
            func_id=str(getattr(binding, "func_id", "") or ""),
            file_path=str(getattr(binding, "file_path", "") or ""),
            source=binding,
            default_language=defaults["language"],
            default_adapter=defaults["adapter"],
        )
        advisory.append(
            CheckpointCIItem(
                category=str(getattr(item, "category", "") or "ddt_binding_advisory"),
                func_id=str(getattr(binding, "func_id", "") or ""),
                file_path=str(getattr(binding, "file_path", "") or ""),
                target_id=identity["target_id"],
                language=identity["language"],
                symbol_kind=identity["symbol_kind"],
                adapter=identity["adapter"],
                reason=str(getattr(item, "message", "") or ""),
                suggested_action=str(getattr(item, "suggested_action", "") or t("cli.ci.checkpoint.action.ddt_baseline_missing")),
                guidance=(
                    guidance_for_checkpoint_category(str(getattr(item, "category", "") or "ddt_binding_advisory"))
                    if settings.enabled
                    else None
                ),
            )
        )

    _push_status_failures(
        failures,
        items=list(getattr(status_report, "missing", []) or []),
        category="missing_function",
        reason=t("cli.ci.checkpoint.failure.missing"),
        include_guidance=settings.enabled,
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "untracked", []) or []),
        category="untracked_function",
        reason=t("cli.ci.checkpoint.failure.untracked"),
        include_guidance=settings.enabled,
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "drift", []) or []),
        category="possible_semantic_drift",
        reason=t("cli.ci.checkpoint.failure.drift"),
        include_guidance=settings.enabled,
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "contract_gap", []) or []),
        category="contract_gap",
        reason=t("cli.ci.checkpoint.failure.contract_gap"),
        include_guidance=settings.enabled,
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "contract_parse_error", []) or []),
        category="contract_parse_error",
        reason=t("cli.ci.checkpoint.failure.contract_parse_error"),
        include_guidance=settings.enabled,
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "contract_changed", []) or []),
        category="contract_changed",
        reason=t("cli.ci.checkpoint.failure.contract_changed"),
        include_guidance=settings.enabled,
    )
    _push_status_failures(
        failures,
        items=list(getattr(status_report, "modified", []) or []),
        category="contract_and_body_changed",
        reason=t("cli.ci.checkpoint.failure.contract_and_body_changed"),
        include_guidance=settings.enabled,
    )
    for entry in list(getattr(status_report, "skipped_no_contract", []) or []):
        identity = _derive_checkpoint_identity(
            func_id=str(getattr(entry, "id", "") or ""),
            file_path=str(getattr(entry, "file_path", "") or ""),
            source=entry,
            default_language="python",
            default_adapter="python",
        )
        advisory.append(
            CheckpointCIItem(
                category="skipped_no_contract",
                func_id=str(getattr(entry, "id", "") or ""),
                file_path=str(getattr(entry, "file_path", "") or ""),
                target_id=identity["target_id"],
                language=identity["language"],
                symbol_kind=identity["symbol_kind"],
                adapter=identity["adapter"],
                reason=_checkpoint_reason_for_entry(
                    category="skipped_no_contract",
                    default_reason=t("cli.ci.checkpoint.failure.skipped_no_contract"),
                    entry=entry,
                ),
                suggested_action=t("cli.ci.checkpoint.action.review_and_rerun"),
                guidance=(
                    guidance_for_checkpoint_category("skipped_no_contract", language=identity["language"])
                    if settings.enabled
                    else None
                ),
            )
        )
    for entry in list(getattr(status_report, "unsupported_syntax_advisory", []) or []):
        identity = _derive_checkpoint_identity(
            func_id=str(getattr(entry, "id", "") or ""),
            file_path=str(getattr(entry, "file_path", "") or ""),
            source=entry,
            default_language="python",
            default_adapter="python",
        )
        advisory.append(
            CheckpointCIItem(
                category="unsupported_syntax_advisory",
                func_id=str(getattr(entry, "id", "") or ""),
                file_path=str(getattr(entry, "file_path", "") or ""),
                target_id=identity["target_id"],
                language=identity["language"],
                symbol_kind=identity["symbol_kind"],
                adapter=identity["adapter"],
                reason=_checkpoint_reason_for_entry(
                    category="unsupported_syntax_advisory",
                    default_reason="TypeScript MVP parser could not safely classify this target.",
                    entry=entry,
                ),
                suggested_action=t("cli.ci.checkpoint.action.review_and_rerun"),
                guidance=(
                    guidance_for_checkpoint_category("unsupported_syntax_advisory", language=identity["language"])
                    if settings.enabled
                    else None
                ),
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
                    target_id=str(getattr(finding, "target_id", "") or ""),
                    language=str(getattr(finding, "language", "") or ""),
                    symbol_kind=str(getattr(finding, "symbol_kind", "") or ""),
                    adapter=str(getattr(finding, "adapter", "") or ""),
                    reason=str(getattr(finding, "reason", "") or t("cli.ci.checkpoint.failure.confirmed_contract_impact")),
                    suggested_action=t("cli.ci.checkpoint.action.confirmed_contract_impact"),
                    guidance=guidance_for_checkpoint_category("confirmed_contract_impact") if settings.enabled else None,
                )
            )
        elif level == ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT:
            possible_contract_impact += 1
            advisory.append(
                CheckpointCIItem(
                    category="possible_contract_impact",
                    func_id=str(getattr(finding, "func_id", "") or ""),
                    file_path=str(getattr(finding, "file_path", "") or ""),
                    target_id=str(getattr(finding, "target_id", "") or ""),
                    language=str(getattr(finding, "language", "") or ""),
                    symbol_kind=str(getattr(finding, "symbol_kind", "") or ""),
                    adapter=str(getattr(finding, "adapter", "") or ""),
                    reason=str(getattr(finding, "reason", "") or t("cli.ci.checkpoint.failure.possible_contract_impact")),
                    suggested_action=t("cli.ci.checkpoint.action.possible_contract_impact"),
                    guidance=guidance_for_checkpoint_category("possible_contract_impact") if settings.enabled else None,
                )
            )
        elif level == ContractImpactLevel.UNKNOWN:
            advisory.append(
                CheckpointCIItem(
                    category="unknown_contract_impact",
                    func_id=str(getattr(finding, "func_id", "") or ""),
                    file_path=str(getattr(finding, "file_path", "") or ""),
                    target_id=str(getattr(finding, "target_id", "") or ""),
                    language=str(getattr(finding, "language", "") or ""),
                    symbol_kind=str(getattr(finding, "symbol_kind", "") or ""),
                    adapter=str(getattr(finding, "adapter", "") or ""),
                    reason=str(getattr(finding, "reason", "") or t("cli.ci.checkpoint.failure.unknown_contract_impact")),
                    suggested_action=t("cli.ci.checkpoint.action.unknown_contract_impact"),
                    guidance=guidance_for_checkpoint_category("unknown_contract_impact") if settings.enabled else None,
                )
            )

    for err in check_errors:
        failures.append(
            CheckpointCIItem(
                category="checkpoint_internal_error",
                reason=str(err),
                suggested_action=t("cli.ci.checkpoint.action.internal_error"),
                guidance=guidance_for_checkpoint_category("checkpoint_internal_error") if settings.enabled else None,
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
        "unsupported_syntax_advisory": len(list(getattr(status_report, "unsupported_syntax_advisory", []) or [])),
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
        advice_mode=settings.mode,
        include_in_ci_json=settings.include_in_ci_json,
        include_in_text=settings.include_in_text,
    )


def build_stale_ci_result(
    results: List[ModuleStaleSummary], scope: str, advice_settings: Optional[AdviceSettings] = None
) -> CIResult:
    settings = advice_settings or AdviceSettings()
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
                guidance=(
                    guidance_for_stale_item(kind="view", view=view_name, status=view.status) if settings.enabled else None
                ),
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
        advice_mode=settings.mode,
        include_in_ci_json=settings.include_in_ci_json,
        include_in_text=settings.include_in_text,
    )


def build_doctor_ci_result(report: DoctorReport, advice_settings: Optional[AdviceSettings] = None) -> CIResult:
    settings = advice_settings or AdviceSettings()
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
            guidance=guidance_for_doctor_item(check=check.name, status=status.lower()) if settings.enabled else None,
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
        advice_mode=settings.mode,
        include_in_ci_json=settings.include_in_ci_json,
        include_in_text=settings.include_in_text,
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
      - guidance 是 optional additive field：
        advice=basic 且 include_in_ci_json=true 时可输出 guidance；
        advice=off 时不输出 guidance。
      - guidance 不改变已有字段语义，不改变 `exit_code` / blocking/failure / advisory 归类。
      - guidance 为 deterministic metadata，不调用 LLM。

    Side Effects:
      - 只做序列化，不执行修复、不刷新上下文、不接受 baseline。
      - 不写文件、不改变运行状态；`writes_files` 不会被动态改写。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only

    Args:
      result (CIResult): 通用 CI 结果对象（stale/doctor）。

    Returns:
      dict: 单一 JSON-compatible payload。`writes_files` 固定 false，
        guidance 为 optional additive field（advice=off 不输出），且不改变
        exit_code / blocking-failure / advisory 语义。
    """
    include_guidance = result.advice_mode == "basic" and result.include_in_ci_json
    return {
        "command": result.command,
        "ci": True,
        "status": result.status,
        "exit_code": result.exit_code,
        "writes_files": False,
        "summary": _sanitize_summary(result.summary),
        "ci_failures": [item.to_dict(include_guidance=include_guidance) for item in result.ci_failures],
        "advisory": [item.to_dict(include_guidance=include_guidance) for item in result.advisory],
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
      - guidance 是 optional additive field：
        advice=basic 且 include_in_ci_json=true 时可输出 guidance；
        advice=off 时不输出 guidance。
      - guidance 不改变既有字段语义，不改变 `exit_code` / blocking/failure / advisory 归类。
      - guidance 为 deterministic metadata，不调用 LLM。

    Side Effects:
      - 只做序列化，不执行修复、不刷新上下文、不接受 baseline。
      - 不写文件、不改变状态；`writes_files` 语义不被本函数改变。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only

    Args:
      result (CheckpointCIResult): checkpoint CI 结果对象。

    Returns:
      dict: 单一 JSON-compatible payload。`writes_files` 固定 false，
        guidance 为 optional additive field（advice=off 不输出），且不改变
        exit_code / blocking-failure / advisory 语义。
    """
    include_guidance = result.advice_mode == "basic" and result.include_in_ci_json
    return {
        "command": result.command,
        "ci": True,
        "status": result.status,
        "exit_code": result.exit_code,
        "writes_files": False,
        "summary": _sanitize_summary(result.summary),
        "ci_failures": [item.to_dict(include_guidance=include_guidance) for item in result.ci_failures],
        "advisory": [item.to_dict(include_guidance=include_guidance) for item in result.advisory],
        "contract_impact": _sanitize_checkpoint_contract_impact(result.contract_impact),
        "next_steps": [_sanitize_json_text(step) for step in result.next_steps],
    }


def format_checkpoint_ci_result(result: CheckpointCIResult) -> str:
    lines: List[str] = []
    show_guidance = result.advice_mode == "basic" and result.include_in_text
    lines.append(t("cli.ci.checkpoint.title"))
    lines.append(t("cli.ci.mode_enabled"))
    lines.append(t("cli.ci.gate", status=t(f"cli.ci.status.{result.status.lower()}")))
    lines.append(f"{t('cli.ci.writes_files')}: false")
    if result.ci_failures:
        lines.append("")
        lines.append(t("cli.ci.blocking_failures"))
        for item in result.ci_failures:
            payload = item.to_dict(include_guidance=show_guidance)
            target = payload.get("func_id") or payload.get("file_path")
            label = t(f"cli.ci.checkpoint.category.{payload['category']}")
            if target:
                lines.append(f"- {label}: {target}")
            else:
                lines.append(f"- {label}: {payload.get('reason', '')}")
            if show_guidance:
                _append_checkpoint_guidance_lines(lines, payload)
    if result.advisory:
        lines.append("")
        lines.append(t("cli.ci.advisory"))
        for item in result.advisory:
            payload = item.to_dict(include_guidance=show_guidance)
            target = payload.get("func_id") or payload.get("file_path")
            label = t(f"cli.ci.checkpoint.category.{payload['category']}")
            if target:
                lines.append(f"- {label}: {target}")
            else:
                lines.append(f"- {label}: {payload.get('reason', '')}")
            if show_guidance:
                _append_checkpoint_guidance_lines(lines, payload)
    if result.next_steps:
        lines.append("")
        lines.append(t("cli.ci.next_steps"))
        for step in result.next_steps:
            lines.append(f"- {step}")
    return "\n".join(lines)


def _append_checkpoint_guidance_lines(lines: List[str], payload: dict) -> None:
    guidance = payload.get("guidance")
    if not isinstance(guidance, dict):
        return
    entries = [
        ("Reason", payload.get("reason")),
        ("Action", guidance.get("recommended_action")),
        ("Do not", guidance.get("anti_action")),
        ("Skill", guidance.get("suggested_skill")),
        ("Decision required", guidance.get("decision_required")),
    ]
    shown = 0
    for label, value in entries:
        if value in (None, "", []):
            continue
        lines.append(f"  {label}: {value}")
        shown += 1
        if shown >= 5:
            break
    lines.append("  Full guidance: harbor next --from <report.json>")


def _push_status_failures(
    failures: List[CheckpointCIItem],
    *,
    items: Sequence[object],
    category: str,
    reason: str,
    include_guidance: bool,
) -> None:
    for entry in items:
        identity = _derive_checkpoint_identity(
            func_id=str(getattr(entry, "id", "") or ""),
            file_path=str(getattr(entry, "file_path", "") or ""),
            source=entry,
            default_language="python",
            default_adapter="python",
        )
        if not _is_blocking_checkpoint_target(identity["symbol_kind"]):
            continue
        failures.append(
            CheckpointCIItem(
                category=category,
                func_id=str(getattr(entry, "id", "") or ""),
                file_path=str(getattr(entry, "file_path", "") or ""),
                target_id=identity["target_id"],
                language=identity["language"],
                symbol_kind=identity["symbol_kind"],
                adapter=identity["adapter"],
                reason=_checkpoint_reason_for_entry(category=category, default_reason=reason, entry=entry),
                suggested_action=t("cli.ci.checkpoint.action.review_and_rerun"),
                guidance=(
                    guidance_for_checkpoint_category(category, language=identity["language"])
                    if include_guidance
                    else None
                ),
            )
        )


def _checkpoint_reason_for_entry(*, category: str, default_reason: str, entry: object) -> str:
    language = str(getattr(entry, "language", "") or "").strip().lower()
    if language != "typescript":
        return default_reason
    if category == "contract_gap":
        return "Required TypeScript contract source is missing or not contract-like."
    if category == "skipped_no_contract":
        return "No contract required for this TypeScript target; semantic comparison skipped."
    if category == "unsupported_syntax_advisory":
        return "TypeScript MVP parser could not safely classify this target."
    return default_reason


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
        "unsupported_syntax_advisory": 13,
        "ddt_version_baseline_missing": 14,
        "ddt_binding_advisory": 15,
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


def _ddt_identity_defaults(func_id: str) -> Dict[str, str]:
    normalized = str(func_id or "").strip().lower()
    if normalized.startswith("typescript:"):
        return {"language": "typescript", "adapter": "typescript"}
    return {"language": "python", "adapter": "python"}


def _is_blocking_checkpoint_target(symbol_kind: Optional[str]) -> bool:
    normalized = str(symbol_kind or "").strip().lower()
    if not normalized:
        return True
    return normalized in {"function", "method"}


def _derive_checkpoint_identity(
    *,
    func_id: str,
    file_path: str,
    source: Any,
    default_language: str,
    default_adapter: str,
) -> Dict[str, Optional[str]]:
    source_target_id = str(getattr(source, "target_id", "") or "").strip()
    source_language = str(getattr(source, "language", "") or "").strip().lower() or default_language
    source_symbol_kind = str(getattr(source, "symbol_kind", "") or "").strip().lower()
    source_adapter = str(getattr(source, "adapter", "") or "").strip().lower() or source_language or default_adapter
    normalized_path = _sanitize_single_path(file_path or "").strip()
    func_id_text = str(func_id or "").strip()

    if source_target_id:
        return {
            "target_id": source_target_id,
            "language": source_language or None,
            "symbol_kind": source_symbol_kind or None,
            "adapter": source_adapter or None,
        }

    if func_id_text.startswith("typescript:") or func_id_text.startswith("python:"):
        parsed = _parse_target_id(func_id_text)
        return {
            "target_id": func_id_text,
            "language": parsed["language"] or source_language or None,
            "symbol_kind": parsed["symbol_kind"] or source_symbol_kind or None,
            "adapter": (parsed["language"] or source_adapter or default_adapter) or None,
        }

    qualified_name, symbol_kind = _derive_qualified_name_and_symbol_kind(
        func_id=func_id_text,
        file_path=normalized_path,
        fallback_symbol_kind=source_symbol_kind,
    )
    if not normalized_path or not qualified_name:
        return {
            "target_id": None,
            "language": source_language or None,
            "symbol_kind": source_symbol_kind or None,
            "adapter": source_adapter or None,
        }

    target_id = ContractSubject.make_target_id(
        language=source_language or default_language,
        file_path=normalized_path,
        symbol_kind=symbol_kind,
        qualified_name=qualified_name,
    )
    return {
        "target_id": target_id,
        "language": source_language or None,
        "symbol_kind": symbol_kind,
        "adapter": source_adapter or None,
    }


def _parse_target_id(target_id: str) -> Dict[str, str]:
    parts = str(target_id or "").split(":", 3)
    if len(parts) != 4:
        return {"language": "", "symbol_kind": ""}
    return {"language": parts[0].strip().lower(), "symbol_kind": parts[2].strip().lower()}


def _derive_qualified_name_and_symbol_kind(
    *,
    func_id: str,
    file_path: str,
    fallback_symbol_kind: str,
) -> Tuple[str, str]:
    normalized_symbol_kind = str(fallback_symbol_kind or "").strip().lower()
    if normalized_symbol_kind:
        symbol_kind = normalized_symbol_kind
    else:
        symbol_kind = "function"

    module_qual = _module_qual_from_file_path(file_path)
    qualified_name = func_id
    if module_qual and func_id.startswith(module_qual + "."):
        qualified_name = func_id[len(module_qual) + 1 :]
    if "." in qualified_name and not normalized_symbol_kind:
        symbol_kind = "method"
    return qualified_name, symbol_kind


def _module_qual_from_file_path(file_path: str) -> str:
    normalized = str(file_path or "").strip().replace("\\", "/")
    if not normalized:
        return ""
    if normalized.endswith(".py"):
        normalized = normalized[:-3]
    return ".".join(part for part in normalized.split("/") if part)
