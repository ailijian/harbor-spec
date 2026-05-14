from __future__ import annotations

import re
from collections import Counter
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
    export_mode: Optional[str] = None
    public_surface_evidence: Optional[str] = None
    data_contract_kind: Optional[str] = None
    schema_source_kind: Optional[str] = None
    source_confidence_summary: Optional[str] = None
    contract_source_kinds: Optional[List[str]] = None
    contract_source_fingerprints: Optional[List[str]] = None
    suggested_action: Optional[str] = None
    guidance: Optional[RepairGuidance] = None

    def dedupe_key(self) -> Tuple[str, str]:
        func = str(self.func_id or "").strip()
        path = _normalize_checkpoint_key_path(self.file_path)
        return (func, path)

    def to_dict(self, *, include_guidance: bool = True) -> dict:
        """将 checkpoint CI failure/advisory 项序列化为 machine-readable JSON-compatible dict。

        此函数输出 shape 是 `harbor checkpoint --ci --format json` 公开契约之一。

        Output Contract:
          - 稳定核心字段为 `category` 与 `reason`；二者始终输出。
          - 兼容字段 `func_id` / `file_path` / `suggested_action` 在存在且非空时输出，
            保持既有 Python/checkpoint 消费方兼容。
          - additive identity metadata 包括 `target_id` / `language` / `symbol_kind` / `adapter`：
            仅在条目已携带对应 identity 时附加输出，不替换既有 `func_id` 语义。
          - additive TypeScript/public-surface metadata 包括 `export_mode` /
            `public_surface_evidence` / `data_contract_kind` / `schema_source_kind` /
            `source_confidence_summary` / `contract_source_kinds` /
            `contract_source_fingerprints`；仅在条目具备对应信息时输出。
          - `guidance` 为既有公开 optional field：仅在 `include_guidance=True`
            且 guidance 存在时输出，其值来自 `RepairGuidance.to_dict()`。
          - 所有文本与路径字段在输出前都会 sanitize；None/空字段按规则省略。

        Behavior:
          - 输出固定包含 `category` 与 `reason`。
          - `func_id` / `file_path` / `suggested_action` 仅在字段存在且非空时输出。
          - `target_id` / `language` / `symbol_kind` / `adapter` 为 additive identity 字段：
            仅在条目具备对应 identity 信息时输出，不改变既有 gate 语义。
          - `export_mode` / `public_surface_evidence` / `data_contract_kind` /
            `schema_source_kind` / `source_confidence_summary` /
            `contract_source_kinds` / `contract_source_fingerprints` 为 additive metadata 字段：
            仅在条目具备对应 TypeScript/source 信息时输出，不改变现有 category/reason 判定。
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
            稳定保留核心字段 `category` / `reason` 与兼容字段 `func_id` / `file_path`；
            additive identity 与 TypeScript/source metadata 仅在可用时输出；
            guidance 为既有 optional public field，且不改变
            exit_code/blocking/advisory 语义。
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
        if self.export_mode:
            payload["export_mode"] = _sanitize_json_text(self.export_mode)
        if self.public_surface_evidence:
            payload["public_surface_evidence"] = _sanitize_json_text(self.public_surface_evidence)
        if self.data_contract_kind:
            payload["data_contract_kind"] = _sanitize_json_text(self.data_contract_kind)
        if self.schema_source_kind:
            payload["schema_source_kind"] = _sanitize_json_text(self.schema_source_kind)
        if self.source_confidence_summary:
            payload["source_confidence_summary"] = _sanitize_json_text(self.source_confidence_summary)
        if self.contract_source_kinds:
            payload["contract_source_kinds"] = _sanitize_string_list(self.contract_source_kinds)
        if self.contract_source_fingerprints:
            payload["contract_source_fingerprints"] = _sanitize_string_list(self.contract_source_fingerprints)
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
    baseline_source: Optional[str] = None
    baseline_path: Optional[str] = None
    baseline_found: bool = False


def build_checkpoint_ci_result(
    *,
    status_report,
    ddt_report,
    contract_impact_report,
    check_errors: Optional[Sequence[str]] = None,
    advice_settings: Optional[AdviceSettings] = None,
    baseline_source: Optional[str] = None,
    baseline_path: Optional[str] = None,
    baseline_found: bool = False,
    baseline_error_category: Optional[str] = None,
    baseline_error_reason: Optional[str] = None,
) -> CheckpointCIResult:
    settings = advice_settings or AdviceSettings()
    check_errors = list(check_errors or [])
    failures: List[CheckpointCIItem] = []
    advisory: List[CheckpointCIItem] = []

    if baseline_error_category:
        failures.append(
            CheckpointCIItem(
                category=str(baseline_error_category),
                file_path=baseline_path,
                reason=str(baseline_error_reason or ""),
                suggested_action=(
                    t("cli.ci.checkpoint.action.accepted_baseline_missing")
                    if baseline_error_category == "accepted_baseline_missing"
                    else t("cli.ci.checkpoint.action.accepted_baseline_invalid")
                ),
                guidance=guidance_for_checkpoint_category(str(baseline_error_category)) if settings.enabled else None,
            )
        )

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
                export_mode=_get_optional_text(entry, "export_mode"),
                public_surface_evidence=_get_optional_text(entry, "public_surface_evidence"),
                data_contract_kind=_get_optional_text(entry, "data_contract_kind"),
                schema_source_kind=_get_optional_text(entry, "schema_source_kind"),
                source_confidence_summary=_get_optional_text(entry, "source_confidence_summary"),
                contract_source_kinds=_get_optional_list(entry, "contract_source_kinds"),
                contract_source_fingerprints=_get_optional_list(entry, "contract_source_fingerprints"),
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
                export_mode=_get_optional_text(entry, "export_mode"),
                public_surface_evidence=_get_optional_text(entry, "public_surface_evidence"),
                data_contract_kind=_get_optional_text(entry, "data_contract_kind"),
                schema_source_kind=_get_optional_text(entry, "schema_source_kind"),
                source_confidence_summary=_get_optional_text(entry, "source_confidence_summary"),
                contract_source_kinds=_get_optional_list(entry, "contract_source_kinds"),
                contract_source_fingerprints=_get_optional_list(entry, "contract_source_fingerprints"),
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
    unknown_contract_impact = 0
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
            unknown_contract_impact += 1
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
        "accepted_baseline_missing": 1 if baseline_error_category == "accepted_baseline_missing" else 0,
        "accepted_baseline_invalid": 1 if baseline_error_category == "accepted_baseline_invalid" else 0,
        "drift": len(list(getattr(status_report, "drift", []) or [])),
        "modified": len(list(getattr(status_report, "modified", []) or [])),
        "contract_changed": len(list(getattr(status_report, "contract_changed", []) or [])),
        "contract_gap": len(list(getattr(status_report, "contract_gap", []) or [])),
        "skipped_no_contract": len(list(getattr(status_report, "skipped_no_contract", []) or [])),
        "unsupported_syntax_advisory": len(list(getattr(status_report, "unsupported_syntax_advisory", []) or [])),
        "contract_parse_error": len(list(getattr(status_report, "contract_parse_error", []) or [])),
        "untracked": len(list(getattr(status_report, "untracked", []) or [])),
        "missing": len(list(getattr(status_report, "missing", []) or [])),
        "ddt_bindings": len(list(getattr(ddt_report, "valid", []) or []))
        + len(list(getattr(ddt_report, "violations", []) or []))
        + len(list(getattr(ddt_report, "advisory", []) or [])),
        "ddt_failures": len(list(getattr(ddt_report, "violations", []) or [])),
        "ddt_advisory": len(list(getattr(ddt_report, "advisory", []) or [])),
        "confirmed_contract_impact": confirmed_contract_impact,
        "possible_contract_impact": possible_contract_impact,
        "unknown_contract_impact": unknown_contract_impact,
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
        baseline_source=baseline_source,
        baseline_path=baseline_path,
        baseline_found=baseline_found,
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
        `baseline_source` / `baseline_path` / `baseline_found` / `summary` /
        `ci_failures` / `advisory` / `contract_impact` / `next_steps`。
      - `writes_files` 固定为 `false`。
      - `baseline_source` / `baseline_path` / `baseline_found` 是稳定的 checkpoint CI baseline 字段：
        分别表示 baseline 来源、repo-relative artifact 路径以及 accepted artifact 是否成功加载。
      - 当 accepted artifact 缺失或非法时，payload 仍稳定输出上述 baseline 字段，
        并通过 `summary` 与 `ci_failures` 暴露 `accepted_baseline_missing` /
        `accepted_baseline_invalid` 分类。
      - `ci_failures` 承载阻断项（如 `contract_gap` / `contract_parse_error` /
        `possible_semantic_drift` / `contract_and_body_changed` / `modified` 等）。
      - `advisory` 保留非阻断项（包括 `ddt_version_baseline_missing`）。
      - 路径与文本字段在输出前会做 sanitize；item 内 None 字段按 item 规则省略。
      - `ci_failures` / `advisory` item 可稳定包含 additive identity 与 adapter metadata，
        例如 `target_id` / `language` / `symbol_kind` / `adapter` /
        `contract_source_kinds` / `contract_source_fingerprints`；这些字段不破坏旧输出消费。
      - `contract_impact` 保留 checkpoint contract-impact 摘要；TypeScript additive metadata
        与 identity 相关信息仅作附加公开字段，不改变既有 gate 语义。
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
        baseline 字段稳定存在；guidance 与 identity / TypeScript additive metadata
        为 optional additive field（advice=off 不输出 guidance），且不改变
        exit_code / blocking-failure / advisory 语义。
    """
    include_guidance = result.advice_mode == "basic" and result.include_in_ci_json
    return {
        "command": result.command,
        "ci": True,
        "status": result.status,
        "exit_code": result.exit_code,
        "writes_files": False,
        "baseline_source": _sanitize_json_text(str(result.baseline_source or "")),
        "baseline_path": _sanitize_single_path(result.baseline_path),
        "baseline_found": bool(result.baseline_found),
        "summary": _sanitize_summary(result.summary),
        "ci_failures": [item.to_dict(include_guidance=include_guidance) for item in result.ci_failures],
        "advisory": [item.to_dict(include_guidance=include_guidance) for item in result.advisory],
        "contract_impact": _sanitize_checkpoint_contract_impact(result.contract_impact),
        "next_steps": [_sanitize_json_text(step) for step in result.next_steps],
    }


def checkpoint_ci_summary_to_dict(result: CheckpointCIResult) -> dict:
    """将 CheckpointCIResult 序列化为 `checkpoint --ci --format json --detail summary` 紧凑摘要。

    Behavior:
      - 输出稳定摘要键：`command` / `ci` / `status` / `exit_code` / `writes_files` /
        `baseline_source` / `baseline_path` / `baseline_found` / `summary` /
        `failure_counts` / `top_failures` / `advisory_counts` / `next_steps`。
      - `summary` 保留现有 checkpoint CI 汇总数字，确保门禁状态、baseline 语义与
        计数口径和 full 模式一致。
      - `failure_counts` / `advisory_counts` 仅暴露按 category 聚合后的轻量计数，
        便于人工排查与 CI 日志快速阅读。
      - `top_failures` 最多输出 5 条阻断项，只保留最小排查字段：
        `category`、`func_id` 或 `target_id`、`file_path`、`reason`。
      - 紧凑摘要不会输出 full 模式中的 `ci_failures` / `advisory` /
        `contract_impact` 全量结构，也不会输出 guidance、source fingerprint、
        source confidence、TypeScript 扩展 metadata 等重型细节。
      - 该摘要模式不改变 gate status、`exit_code`、baseline 语义或 next-steps 语义。

    Side Effects:
      - 只读序列化；不写文件、不接受 baseline、不刷新上下文。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only

    Args:
      result (CheckpointCIResult): 已构建的 checkpoint CI 结果对象。

    Returns:
      dict: 适合机器消费但更轻量的 checkpoint CI 摘要 JSON payload。
    """
    top_failures: List[dict] = []
    for item in _checkpoint_top_items(result.ci_failures, limit=5):
        row: Dict[str, object] = {
            "category": _sanitize_json_text(str(item.category or "")),
            "reason": _sanitize_json_text(str(item.reason or "")),
        }
        func_id = _sanitize_json_text(str(item.func_id or ""))
        target_id = _sanitize_json_text(str(item.target_id or ""))
        file_path = _sanitize_single_path(item.file_path)
        if func_id:
            row["func_id"] = func_id
        elif target_id:
            row["target_id"] = target_id
        if file_path:
            row["file_path"] = file_path
        top_failures.append(row)
    return {
        "command": result.command,
        "ci": True,
        "status": result.status,
        "exit_code": result.exit_code,
        "writes_files": False,
        "baseline_source": _sanitize_json_text(str(result.baseline_source or "")),
        "baseline_path": _sanitize_single_path(result.baseline_path),
        "baseline_found": bool(result.baseline_found),
        "summary": _sanitize_summary(result.summary),
        "failure_counts": _checkpoint_category_counts(result.ci_failures),
        "top_failures": top_failures,
        "advisory_counts": _checkpoint_category_counts(result.advisory),
        "next_steps": [_sanitize_json_text(step) for step in result.next_steps],
    }


def format_checkpoint_workflow_summary(result: CheckpointCIResult) -> str:
    """Render the default `harbor checkpoint` text output in a summary-first layout.

    Behavior:
      - 该 formatter 服务于非 CI 的 `harbor checkpoint` 默认文本输出。
      - 先展示决策摘要：总体状态、阻断数、建议数、阻断分类计数。
      - 保留 Contract Impact 计数、DDT 摘要、Top blockers、下一步建议。
      - 默认不展开全部 drift/modified/untracked/DDT advisory 明细；完整诊断由
        `harbor checkpoint --verbose` 路径负责。
      - Top blockers 最多展示 3 条，使用稳定展示优先级，不改变底层 gate 判定。
      - 当无阻断项时保持较短输出，但仍保留 DDT 与下一步摘要。

    Side Effects:
      - 纯文本渲染；不写文件、不刷新上下文、不接受 baseline。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only

    Args:
      result (CheckpointCIResult): 基于现有 checkpoint 数据构建出的摘要结果。

    Returns:
      str: `harbor checkpoint` 默认文本输出。
    """
    lines: List[str] = [t("cli.checkpoint.title")]
    blocking_count = len(list(result.ci_failures or []))
    advisory_count = len(list(result.advisory or []))
    lines.append("")
    lines.append(f"{t('cli.checkpoint.summary.status')}: {str(result.status or 'pass').upper()}")
    lines.append(f"{t('cli.checkpoint.summary.blocking')}: {blocking_count}")
    lines.append(f"{t('cli.checkpoint.summary.advisory')}: {advisory_count}")

    blocking_counts = _checkpoint_category_counts(result.ci_failures)
    if blocking_counts:
        lines.append("")
        lines.append(t("cli.checkpoint.summary.blocking_summary"))
        for category, count in blocking_counts.items():
            lines.append(f"- {category}: {count}")

    lines.append("")
    lines.append(t("cli.checkpoint.summary.contract_impact"))
    lines.append(f"- confirmed: {int(result.summary.get('confirmed_contract_impact', 0) or 0)}")
    lines.append(f"- possible: {int(result.summary.get('possible_contract_impact', 0) or 0)}")
    lines.append(f"- unknown: {int(result.summary.get('unknown_contract_impact', 0) or 0)}")

    lines.append("")
    lines.append(t("cli.checkpoint.summary.ddt"))
    bindings = (
        int(result.summary.get("ddt_bindings", 0) or 0)
        if "ddt_bindings" in result.summary
        else int(result.summary.get("ddt_total_bindings", 0) or 0)
    )
    lines.append(f"- bindings: {bindings}")
    lines.append(f"- violations: {int(result.summary.get('ddt_failures', 0) or 0)}")
    lines.append(f"- advisory: {int(result.summary.get('ddt_advisory', 0) or 0)}")

    top_items = _checkpoint_top_items(result.ci_failures, limit=3)
    if top_items:
        lines.append("")
        lines.append(t("cli.checkpoint.summary.top_blockers"))
        for index, item in enumerate(top_items, start=1):
            target = _sanitize_json_text(str(item.func_id or "")) or _sanitize_single_path(item.file_path)
            lines.append(f"{index}. {str(item.category or '')}")
            if target:
                lines.append(f"   {target}")

    lines.append("")
    lines.append(t("cli.checkpoint.summary.next"))
    for step in _checkpoint_workflow_next_steps(result):
        lines.append(f"- {step}")
    return "\n".join(lines)


def format_checkpoint_ci_result(result: CheckpointCIResult) -> str:
    lines: List[str] = []
    show_guidance = result.advice_mode == "basic" and result.include_in_text
    lines.append(t("cli.ci.checkpoint.title"))
    lines.append(t("cli.ci.mode_enabled"))
    lines.append(t("cli.ci.gate", status=t(f"cli.ci.status.{result.status.lower()}")))
    lines.append(f"{t('cli.ci.writes_files')}: false")
    lines.append(f"{t('cli.ci.checkpoint.baseline_source')}: {_sanitize_json_text(str(result.baseline_source or ''))}")
    lines.append(f"{t('cli.ci.checkpoint.baseline_path')}: {_sanitize_single_path(result.baseline_path)}")
    lines.append(f"{t('cli.ci.checkpoint.baseline_found')}: {str(bool(result.baseline_found)).lower()}")
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


def _checkpoint_category_counts(items: Sequence[CheckpointCIItem]) -> Dict[str, int]:
    counter = Counter(
        _sanitize_json_text(str(item.category or ""))
        for item in list(items or [])
        if str(item.category or "").strip()
    )
    return dict(sorted(counter.items(), key=lambda row: (_checkpoint_category_priority(row[0]), row[0])))


def _checkpoint_category_priority(category: str) -> int:
    order = {
        "accepted_baseline_missing": 0,
        "accepted_baseline_invalid": 1,
        "contract_gap": 2,
        "contract_parse_error": 3,
        "confirmed_contract_impact": 4,
        "possible_semantic_drift": 5,
        "contract_and_body_changed": 6,
        "contract_changed": 7,
        "untracked_function": 8,
        "missing_function": 9,
        "ddt_binding": 10,
        "checkpoint_internal_error": 11,
        "possible_contract_impact": 12,
        "unknown_contract_impact": 13,
        "skipped_no_contract": 14,
        "unsupported_syntax_advisory": 15,
        "ddt_version_baseline_missing": 16,
        "ddt_binding_advisory": 17,
    }
    return order.get(str(category or ""), 99)


def _checkpoint_top_items(items: Sequence[CheckpointCIItem], *, limit: int) -> List[CheckpointCIItem]:
    ranked = sorted(
        list(items or []),
        key=lambda item: (
            _checkpoint_category_priority(str(item.category or "")),
            _sanitize_single_path(item.file_path),
            _sanitize_json_text(str(item.func_id or "")),
            _sanitize_json_text(str(item.reason or "")),
        ),
    )
    return ranked[: max(int(limit or 0), 0)]


def _checkpoint_workflow_next_steps(result: CheckpointCIResult) -> List[str]:
    if result.ci_failures:
        return [
            "Run `harbor checkpoint --ci --format json`",
            "Run `harbor next --from <checkpoint-report.json>`",
        ]
    return [
        "Continue work or run `harbor finish --sync-context`",
    ]


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
                export_mode=_get_optional_text(entry, "export_mode"),
                public_surface_evidence=_get_optional_text(entry, "public_surface_evidence"),
                data_contract_kind=_get_optional_text(entry, "data_contract_kind"),
                schema_source_kind=_get_optional_text(entry, "schema_source_kind"),
                source_confidence_summary=_get_optional_text(entry, "source_confidence_summary"),
                contract_source_kinds=_get_optional_list(entry, "contract_source_kinds"),
                contract_source_fingerprints=_get_optional_list(entry, "contract_source_fingerprints"),
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
    data_contract_kind = str(getattr(entry, "data_contract_kind", "") or "").strip().lower()
    schema_source_kind = str(getattr(entry, "schema_source_kind", "") or "").strip().lower()
    public_surface_evidence = str(getattr(entry, "public_surface_evidence", "") or "").strip().lower()
    source_confidence_summary = str(getattr(entry, "source_confidence_summary", "") or "").strip().lower()
    source_kinds = {
        str(value or "").strip().lower()
        for value in list(getattr(entry, "contract_source_kinds", []) or [])
        if str(value or "").strip()
    }
    if category == "contract_gap":
        if source_confidence_summary in {"medium", "low"} and source_kinds & {"tsdoc", "jsdoc"}:
            return "TypeScript doc comment was detected, but its confidence is not high enough to count as a contract source."
        return "Required TypeScript contract source is missing or not contract-like."
    if category == "skipped_no_contract":
        if schema_source_kind in {"z.object", "z.enum"}:
            return "TypeScript Zod schema is tracked as shallow contract evidence only; blocking semantic comparison is skipped."
        if data_contract_kind:
            return "TypeScript exported data contract target is tracked in advisory-first mode; blocking semantic comparison is skipped."
        if public_surface_evidence == "default_export":
            return "TypeScript default export is tracked as public surface evidence, not as a contract source."
        return "No contract required for this TypeScript target; semantic comparison skipped."
    if category == "unsupported_syntax_advisory":
        return "TypeScript MVP parser could not safely classify this target."
    return default_reason


def _get_optional_text(source: object, field_name: str) -> Optional[str]:
    value = str(getattr(source, field_name, "") or "").strip()
    return value or None


def _get_optional_list(source: object, field_name: str) -> Optional[List[str]]:
    raw = getattr(source, field_name, None)
    if not raw:
        return None
    values = [str(value).strip() for value in list(raw) if str(value or "").strip()]
    return values or None


def _sanitize_string_list(values: Sequence[str]) -> List[str]:
    out: List[str] = []
    for value in values:
        text = _sanitize_json_text(str(value or "").strip())
        if text:
            out.append(text)
    return out


def _dedupe_checkpoint_items(items: Sequence[CheckpointCIItem]) -> List[CheckpointCIItem]:
    priority = {
        "accepted_baseline_missing": 0,
        "accepted_baseline_invalid": 1,
        "checkpoint_internal_error": 2,
        "ddt_binding": 3,
        "contract_and_body_changed": 4,
        "contract_changed": 5,
        "possible_semantic_drift": 6,
        "missing_function": 7,
        "untracked_function": 8,
        "contract_gap": 9,
        "contract_parse_error": 10,
        "confirmed_contract_impact": 11,
        "possible_contract_impact": 12,
        "unknown_contract_impact": 13,
        "skipped_no_contract": 14,
        "unsupported_syntax_advisory": 15,
        "ddt_version_baseline_missing": 16,
        "ddt_binding_advisory": 17,
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
    categories = {str(item.category or "") for item in ci_failures}
    if not ci_failures:
        return [
            t("cli.ci.checkpoint.next_steps.pass"),
            t("cli.ci.checkpoint.next_steps.rerun"),
        ]
    if "accepted_baseline_missing" in categories:
        return [
            t("cli.ci.checkpoint.next_steps.accepted_baseline_missing"),
            t("cli.ci.checkpoint.next_steps.commit_artifact"),
            t("cli.ci.checkpoint.next_steps.rerun"),
        ]
    if "accepted_baseline_invalid" in categories:
        return [
            t("cli.ci.checkpoint.next_steps.accepted_baseline_invalid"),
            t("cli.ci.checkpoint.next_steps.commit_artifact"),
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
