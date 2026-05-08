from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Optional

from harbor.core.context_integrity import content_without_generated_at_for_compare, strip_frontmatter
from harbor.core.l2 import L2Generator
from harbor.core.module_capsule import (
    check_module_capsule_stale,
    collect_module_context,
    normalize_module_path,
)
from harbor.core.workspace import load_workspace_config, parse_workspace_export_options
from harbor.utils.i18n import t


@dataclass
class ViewStaleResult:
    view: str
    status: str
    reason: Optional[str] = None
    suggested_command: Optional[str] = None

    def to_dict(self, *, view_name: Optional[str] = None) -> dict:
        is_up_to_date = self.status == "up_to_date"
        return {
            "view": view_name or self.view.lower().replace(" ", "_"),
            "status": self.status,
            "reason": None if is_up_to_date else _sanitize_json_text(self.reason),
            "suggested_command": None if is_up_to_date else _sanitize_json_text(self.suggested_command),
        }


@dataclass
class ModuleStaleSummary:
    module: str
    l2_readme: ViewStaleResult
    l2_readme_export: ViewStaleResult
    module_capsule: ViewStaleResult

    def to_dict(self) -> dict:
        """将模块视图状态摘要序列化为稳定 JSON 结构。"""
        return {
            "module": _sanitize_module_for_json(self.module),
            "views": [
                self.l2_readme.to_dict(view_name="l2_readme"),
                self.l2_readme_export.to_dict(view_name="l2_readme_export"),
                self.module_capsule.to_dict(view_name="module_capsule"),
            ],
        }


def _normalize_l2_markdown_for_stale(text: str) -> str:
    return content_without_generated_at_for_compare(text)


def _normalize_l2_body_for_export_compare(text: str) -> str:
    return _normalize_l2_markdown_for_stale(strip_frontmatter(text))


def check_l2_readme_stale(module: str, *, generator: Optional[L2Generator] = None) -> ViewStaleResult:
    normalized = normalize_module_path(module)
    suggest = f"harbor docs --module {normalized} --write"
    context = collect_module_context(normalized)
    if not context.get("key_files") and not context.get("contracts"):
        return ViewStaleResult(
            view="L2 README",
            status="unknown",
            reason="no indexed records found for module",
            suggested_command=None,
        )

    gen = generator or L2Generator()
    expected = gen.generate(normalized)
    readme_path = gen.canonical_readme_path(normalized)
    if not readme_path.exists():
        return ViewStaleResult(
            view="L2 README",
            status="stale",
            reason="canonical README.md not found",
            suggested_command=suggest,
        )

    try:
        current = readme_path.read_text(encoding="utf-8")
    except Exception:
        return ViewStaleResult(
            view="L2 README",
            status="stale",
            reason="README content mismatch",
            suggested_command=suggest,
        )

    if _normalize_l2_body_for_export_compare(current) != _normalize_l2_body_for_export_compare(expected):
        return ViewStaleResult(
            view="L2 README",
            status="stale",
            reason="README content mismatch",
            suggested_command=suggest,
        )

    return ViewStaleResult(
        view="L2 README",
        status="up_to_date",
        reason="up to date",
        suggested_command=None,
    )


def check_l2_readme_export_stale(
    module: str,
    *,
    canonical_result: ViewStaleResult,
    generator: Optional[L2Generator] = None,
) -> ViewStaleResult:
    normalized = normalize_module_path(module)
    gen = generator or L2Generator()

    loaded = load_workspace_config(Path.cwd())
    cfg = loaded.get("config") or {}
    export_options = parse_workspace_export_options(cfg)
    module_readme_options = ((export_options.get("l2", {}) or {}).get("module_readme", {}) or {})
    export_enabled = bool(module_readme_options.get("enabled", True))

    if not export_enabled:
        return ViewStaleResult(
            view="L2 README Export",
            status="disabled",
            reason="module README export disabled by config",
            suggested_command=None,
        )

    if canonical_result.status != "up_to_date":
        return ViewStaleResult(
            view="L2 README Export",
            status="unknown",
            reason="canonical L2 README unavailable",
            suggested_command=None,
        )

    canonical_path = gen.canonical_readme_path(normalized)
    export_path = (Path.cwd().resolve() / normalized / "README.md").resolve()
    suggest = f"harbor docs --module {normalized} --write"

    if not export_path.exists():
        return ViewStaleResult(
            view="L2 README Export",
            status="stale",
            reason="module README export missing",
            suggested_command=suggest,
        )

    try:
        canonical_text = canonical_path.read_text(encoding="utf-8")
        export_text = export_path.read_text(encoding="utf-8")
    except Exception:
        return ViewStaleResult(
            view="L2 README Export",
            status="stale",
            reason="module README export out of sync",
            suggested_command=suggest,
        )

    if _normalize_l2_body_for_export_compare(export_text) != _normalize_l2_body_for_export_compare(canonical_text):
        return ViewStaleResult(
            view="L2 README Export",
            status="stale",
            reason="module README export out of sync",
            suggested_command=suggest,
        )

    return ViewStaleResult(
        view="L2 README Export",
        status="up_to_date",
        reason="up to date",
        suggested_command=None,
    )


def check_module_derived_views_stale(module: str) -> ModuleStaleSummary:
    """检查单模块的 L2 / L2 export / Capsule 三类视图状态。

    Args:
        module: 模块路径（例如 ``harbor/core``）。

    Returns:
        ModuleStaleSummary: 聚合后的三视图状态。
            - `l2_readme` 由 canonical L2 判定。
            - `l2_readme_export` 仅在 canonical 可用时比较。
            - `module_capsule` 基于 capsule stale 结果映射。
    """
    normalized = normalize_module_path(module)
    context = collect_module_context(normalized)
    l2_result = check_l2_readme_stale(normalized)
    l2_export_result = check_l2_readme_export_stale(normalized, canonical_result=l2_result)

    capsule_raw = check_module_capsule_stale(context)
    capsule_reason = capsule_raw.get("reason") or ""
    capsule_status = "up_to_date" if capsule_raw.get("status") == "up_to_date" else "stale"
    if capsule_reason == "no indexed records found for module":
        capsule_status = "unknown"
    capsule_suggest = None
    if capsule_status != "up_to_date" and capsule_reason != "no indexed records found for module":
        capsule_suggest = f"harbor module seal {normalized} --write"

    capsule_result = ViewStaleResult(
        view="Module Capsule",
        status=capsule_status,
        reason=capsule_reason or None,
        suggested_command=capsule_suggest,
    )
    return ModuleStaleSummary(
        module=normalized,
        l2_readme=l2_result,
        l2_readme_export=l2_export_result,
        module_capsule=capsule_result,
    )


def format_stale_summary(results: List[ModuleStaleSummary], scope_text: str) -> str:
    """将 stale 检查结果渲染为 CLI 文本摘要。

    Args:
        results: 模块 stale 汇总列表。
        scope_text: 已解析的 scope 文本（changed/all/module）。

    Returns:
        str: 面向 CLI 的多行文本。
    """
    lines: List[str] = []
    lines.append(t("cli.stale.title"))
    lines.append(f"Scope: {scope_text}")

    all_up_to_date = True
    for summary in results:
        module_all_ok = (
            summary.l2_readme.status == "up_to_date"
            and summary.module_capsule.status == "up_to_date"
            and summary.l2_readme_export.status in ("up_to_date", "disabled")
        )
        if not module_all_ok:
            all_up_to_date = False
        lines.append("")
        lines.append(summary.module)
        lines.extend(_format_view_lines(t("cli.stale.l2"), summary.l2_readme))
        lines.extend(_format_view_lines(t("cli.stale.l2_export"), summary.l2_readme_export))
        lines.extend(_format_view_lines(t("cli.stale.capsule"), summary.module_capsule))

    if results:
        lines.append("")
    if all_up_to_date:
        lines.append(t("cli.stale.all_up_to_date"))

    return "\n".join(lines)


def stale_report_to_dict(results: List[ModuleStaleSummary], scope: str) -> dict:
    """将 stale 检查结果序列化为 machine-readable JSON 对象。

    Args:
        results: 模块 stale 汇总列表。
        scope: 输出中的 scope 字段值。

    Returns:
        dict: 稳定的 stale JSON payload。
    """
    normalized_results = sorted(results, key=lambda item: item.module)
    stale_views = 0
    up_to_date_views = 0
    unknown_views = 0
    disabled_views = 0
    for module_summary in normalized_results:
        for view in (module_summary.l2_readme, module_summary.l2_readme_export, module_summary.module_capsule):
            if view.status == "up_to_date":
                up_to_date_views += 1
            elif view.status == "disabled":
                disabled_views += 1
            elif view.status == "unknown":
                unknown_views += 1
            else:
                stale_views += 1

    overall_status = "pass"
    if stale_views > 0 or unknown_views > 0:
        overall_status = "warn"

    return {
        "command": "stale",
        "scope": scope,
        "status": overall_status,
        "summary": {
            "modules_checked": len(normalized_results),
            "stale_views": stale_views,
            "up_to_date_views": up_to_date_views,
            "unknown_views": unknown_views,
            "disabled_views": disabled_views,
        },
        "modules": [item.to_dict() for item in normalized_results],
        "advisory": True,
        "writes_files": False,
    }


def _format_view_lines(label: str, result: ViewStaleResult) -> List[str]:
    """格式化单个视图状态的文本行。"""
    status = t("cli.stale.up_to_date")
    if result.status == "stale":
        status = t("cli.stale.stale")
    elif result.status == "unknown":
        status = t("cli.stale.unknown")
    elif result.status == "disabled":
        status = t("cli.stale.disabled")

    lines = [f"- {label}: {status}"]
    if result.reason and result.status != "up_to_date":
        lines.append(f"  {t('cli.stale.reason')}: {result.reason}")
    if result.suggested_command and result.status != "up_to_date":
        lines.append(f"  {t('cli.stale.suggested')}: {result.suggested_command}")
    return lines


_WINDOWS_ABS_PATH_RE = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"']+")
_POSIX_ABS_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:[^ \t\r\n\"']+)")


def _sanitize_module_for_json(module: str) -> str:
    return _sanitize_single_path(module)


def _sanitize_json_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

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
