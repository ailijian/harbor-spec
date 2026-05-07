from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from harbor.core.workspace import load_workspace_paths
from harbor.utils.i18n import t


@dataclass
class WorkspaceMigrationPlanItem:
    id: str
    source: str
    target: str
    category: str
    status: str
    action: str
    risk: str
    recommendation: str
    automatic: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "category": self.category,
            "status": self.status,
            "action": self.action,
            "risk": self.risk,
            "recommendation": self.recommendation,
            "automatic": self.automatic,
            "reason": self.reason,
        }


@dataclass
class WorkspaceMigrateDryRunReport:
    mode: str
    writes_files: bool
    summary: Dict[str, Any]
    plan_items: List[WorkspaceMigrationPlanItem]
    advisory: List[str]
    next_steps: List[str]


def build_workspace_migrate_dry_run_report(repo_root: Path) -> WorkspaceMigrateDryRunReport:
    root = Path(repo_root).resolve()
    paths = load_workspace_paths(root, enforce_write_safety=False)

    legacy_config = root / ".harbor" / "config.yaml"
    legacy_l2_meta = root / ".harbor" / "l2_meta.json"
    legacy_diary_dir = root / "specs" / "diary"
    docs_export_dir = root / "docs" / "harbor"
    canonical_config = paths.config_root / "harbor.yaml"
    canonical_l2_meta = paths.l2_view_root / "_meta.json"
    canonical_diary = paths.diary_root
    canonical_views = paths.views_root

    diary_detected = legacy_diary_dir.exists() and any(legacy_diary_dir.glob("*.jsonl"))
    module_export_items = _collect_module_readme_exports(root, canonical_l2_root=paths.l2_view_root)

    plan_items: List[WorkspaceMigrationPlanItem] = [
        WorkspaceMigrationPlanItem(
            id="legacy_config",
            source=_to_display_path(legacy_config, repo_root=root),
            target=_to_display_path(canonical_config, repo_root=root),
            category="legacy_config",
            status="detected" if legacy_config.exists() else "not_detected",
            action="manual_review",
            risk="low",
            recommendation=t("cli.workspace.migrate.plan.legacy_config.recommendation"),
            automatic=False,
            reason=t("cli.workspace.migrate.plan.legacy_config.reason"),
        ),
        WorkspaceMigrationPlanItem(
            id="legacy_l2_metadata",
            source=_to_display_path(legacy_l2_meta, repo_root=root),
            target=_to_display_path(canonical_l2_meta, repo_root=root),
            category="legacy_metadata",
            status="detected" if legacy_l2_meta.exists() else "not_detected",
            action="manual_review",
            risk="low",
            recommendation=t("cli.workspace.migrate.plan.legacy_l2_meta.recommendation"),
            automatic=False,
            reason=t("cli.workspace.migrate.plan.legacy_l2_meta.reason"),
        ),
        WorkspaceMigrationPlanItem(
            id="legacy_diary",
            source=_to_display_path(legacy_diary_dir, repo_root=root),
            target=_to_display_path(canonical_diary, repo_root=root),
            category="legacy_diary",
            status="detected" if diary_detected else "not_detected",
            action="manual_merge_required",
            risk="high",
            recommendation=t("cli.workspace.migrate.plan.legacy_diary.recommendation"),
            automatic=False,
            reason=t("cli.workspace.migrate.plan.legacy_diary.reason"),
        ),
        WorkspaceMigrationPlanItem(
            id="docs_export",
            source=_to_display_path(docs_export_dir, repo_root=root),
            target=_to_display_path(canonical_views, repo_root=root),
            category="docs_export",
            status="detected" if docs_export_dir.exists() else "not_detected",
            action="no_action",
            risk="low",
            recommendation=t("cli.workspace.migrate.plan.docs_export.recommendation"),
            automatic=False,
            reason=t("cli.workspace.migrate.plan.docs_export.reason"),
        ),
    ]
    plan_items.extend(module_export_items)

    detected = [item for item in plan_items if item.status == "detected"]
    manual_actions = [
        item
        for item in detected
        if item.action in ("manual_review", "manual_merge_required")
    ]
    non_actions = [item for item in detected if item.action == "no_action"]
    high_risk = [item for item in detected if item.risk == "high"]

    summary: Dict[str, Any] = {
        "items_total": len(plan_items),
        "detected_items": len(detected),
        "manual_actions": len(manual_actions),
        "non_actions": len(non_actions),
        "high_risk_items": len(high_risk),
    }

    advisory = [
        t("cli.workspace.migrate.advisory.read_only"),
        t("cli.workspace.migrate.advisory.no_write"),
    ]
    if high_risk:
        advisory.append(t("cli.workspace.migrate.advisory.high_risk_diary"))

    next_steps = [
        t("cli.workspace.migrate.next_steps.inspect"),
        t("cli.workspace.migrate.next_steps.review"),
        t("cli.workspace.migrate.next_steps.future"),
    ]

    return WorkspaceMigrateDryRunReport(
        mode="dry_run",
        writes_files=False,
        summary=summary,
        plan_items=plan_items,
        advisory=advisory,
        next_steps=next_steps,
    )


def workspace_migrate_report_to_dict(report: WorkspaceMigrateDryRunReport) -> dict:
    return {
        "command": "workspace_migrate",
        "mode": report.mode,
        "writes_files": report.writes_files,
        "summary": dict(report.summary),
        "plan_items": [item.to_dict() for item in report.plan_items],
        "advisory": list(report.advisory),
        "next_steps": list(report.next_steps),
    }


def format_workspace_migrate_report(report: WorkspaceMigrateDryRunReport) -> str:
    lines: List[str] = [
        t("cli.workspace.migrate.title"),
        "",
        t("cli.workspace.migrate.safety_notice"),
        t("cli.workspace.migrate.no_changes_line"),
        t("cli.workspace.migrate.plan_only_line"),
        "",
        t("cli.workspace.migrate.section.summary"),
        f"- mode: {report.mode}",
        f"- writes_files: {str(report.writes_files).lower()}",
        f"- items_total: {report.summary.get('items_total', 0)}",
        f"- detected_items: {report.summary.get('detected_items', 0)}",
        f"- manual_actions: {report.summary.get('manual_actions', 0)}",
        f"- non_actions: {report.summary.get('non_actions', 0)}",
        f"- high_risk_items: {report.summary.get('high_risk_items', 0)}",
        "",
        t("cli.workspace.migrate.section.plan_items"),
    ]

    for item in report.plan_items:
        lines.append(
            "- "
            f"[{item.id}] source={item.source} target={item.target} "
            f"status={item.status} action={item.action} risk={item.risk} automatic={str(item.automatic).lower()}"
        )
        lines.append(f"  category={item.category}")
        lines.append(f"  reason={item.reason}")
        lines.append(f"  recommendation={item.recommendation}")

    lines.append("")
    lines.append(t("cli.workspace.migrate.section.manual_actions"))
    manual_items = [
        item
        for item in report.plan_items
        if item.status == "detected" and item.action in ("manual_review", "manual_merge_required")
    ]
    if not manual_items:
        lines.append(f"- {t('cli.workspace.migrate.none')}")
    else:
        for item in manual_items:
            lines.append(f"- {item.id}: {item.action} ({item.source} -> {item.target})")

    lines.append("")
    lines.append(t("cli.workspace.migrate.section.non_actions"))
    non_actions = [
        item
        for item in report.plan_items
        if item.status == "detected" and item.action == "no_action"
    ]
    if not non_actions:
        lines.append(f"- {t('cli.workspace.migrate.none')}")
    else:
        for item in non_actions:
            lines.append(f"- {item.id}: {item.reason}")

    lines.append("")
    lines.append(t("cli.workspace.migrate.section.next_steps"))
    for step in report.next_steps:
        lines.append(f"- {step}")

    return "\n".join(lines).rstrip()


def _collect_module_readme_exports(repo_root: Path, *, canonical_l2_root: Path) -> List[WorkspaceMigrationPlanItem]:
    excluded_roots = {".harbor", ".agents", "docs", "tests", "specs"}
    items: List[WorkspaceMigrationPlanItem] = []

    for readme in sorted(repo_root.rglob("README.md")):
        rel_readme = _to_display_path(readme, repo_root=repo_root)
        rel_parts = rel_readme.split("/")
        if len(rel_parts) < 2:
            continue
        if rel_parts[0] in excluded_roots:
            continue
        module_dir = readme.parent
        if not _module_dir_has_python_files(module_dir):
            continue
        module_rel = _to_display_path(module_dir, repo_root=repo_root)
        target = _to_display_path(canonical_l2_root / module_rel / "README.md", repo_root=repo_root)
        items.append(
            WorkspaceMigrationPlanItem(
                id=f"module_readme_export:{module_rel}",
                source=rel_readme,
                target=target,
                category="module_readme_export",
                status="detected",
                action="no_action",
                risk="low",
                recommendation=t("cli.workspace.migrate.plan.module_readme.recommendation", module=module_rel),
                automatic=False,
                reason=t("cli.workspace.migrate.plan.module_readme.reason"),
            )
        )
    return items


def _module_dir_has_python_files(module_dir: Path) -> bool:
    for py_file in module_dir.rglob("*.py"):
        if py_file.name.endswith(".py"):
            return True
    return False


_WINDOWS_ABS_PATH_RE = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"']+")
_POSIX_ABS_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:[^ \t\r\n\"']+)")


def sanitize_text(value: str, *, repo_root: Path) -> str:
    def _replace(match: re.Match) -> str:
        return _to_display_path(Path(match.group(0)), repo_root=repo_root)

    sanitized = _WINDOWS_ABS_PATH_RE.sub(_replace, value)
    sanitized = _POSIX_ABS_PATH_RE.sub(_replace, sanitized)
    return sanitized


def _to_display_path(path: Path, *, repo_root: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
        except Exception:
            base = candidate.name
            return f"<outside-repo>/{base}" if base else "<outside-repo>"
    return candidate.as_posix().replace("\\", "/")
