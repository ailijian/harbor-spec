from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from harbor.core.workspace import load_workspace_config, load_workspace_paths
from harbor.utils.i18n import t

Severity = Literal["pass", "warn", "info"]
GitIgnored = Literal[True, False, "unknown"]
GitExpected = Literal["ignored", "trackable", "optional"]


@dataclass
class WorkspaceLegacyPathStatus:
    path: str
    exists: bool
    role: str
    severity: Severity

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "exists": self.exists,
            "role": self.role,
            "severity": self.severity,
        }


@dataclass
class WorkspaceGitTrackingStatus:
    path: str
    ignored: GitIgnored
    expected: GitExpected
    severity: Severity
    note: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "ignored": self.ignored,
            "expected": self.expected,
            "severity": self.severity,
            "note": self.note,
        }


@dataclass
class WorkspaceGeneratedViewsStatus:
    project_structure_exists: bool
    module_capsule_count: int
    l2_readme_count: int
    diary_file_count: int
    report_file_count: int
    skill_count: int

    def to_dict(self) -> dict:
        return {
            "project_structure_exists": self.project_structure_exists,
            "module_capsule_count": self.module_capsule_count,
            "l2_readme_count": self.l2_readme_count,
            "diary_file_count": self.diary_file_count,
            "report_file_count": self.report_file_count,
            "skill_count": self.skill_count,
        }


@dataclass
class WorkspaceInspectReport:
    config: Dict[str, Any]
    canonical_paths: Dict[str, str]
    legacy_paths: List[WorkspaceLegacyPathStatus]
    git_tracking: List[WorkspaceGitTrackingStatus]
    generated_views: WorkspaceGeneratedViewsStatus
    advisory_summary: List[Dict[str, str]]


def build_workspace_inspect_report(repo_root: Path) -> WorkspaceInspectReport:
    root = Path(repo_root).resolve()
    loaded = load_workspace_config(root)
    cfg = dict(loaded.get("config") or {})
    paths = load_workspace_paths(root, enforce_write_safety=False)

    source_path = loaded.get("source_path")
    active_config = source_path if source_path is not None else loaded.get("new_config_path")
    code_roots = list(cfg.get("code_roots") or ["harbor/**"])
    source_roots = list(cfg.get("source_roots") or code_roots)

    config_section: Dict[str, Any] = {
        "active_config": _to_display_path(Path(active_config), repo_root=root),
        "legacy_config_detected": bool(Path(root / ".harbor" / "config.yaml").exists()),
        "source_roots": source_roots,
        "code_roots": code_roots,
    }

    canonical_paths: Dict[str, str] = {
        "config_root": _to_display_path(paths.config_root, repo_root=root),
        "policy_root": _to_display_path(paths.policy_root, repo_root=root),
        "state_root": _to_display_path(paths.state_root, repo_root=root),
        "cache_root": _to_display_path(paths.cache_root, repo_root=root),
        "views_root": _to_display_path(paths.views_root, repo_root=root),
        "project_structure_path": _to_display_path(paths.project_structure_path, repo_root=root),
        "modules_view_root": _to_display_path(paths.modules_view_root, repo_root=root),
        "l2_view_root": _to_display_path(paths.l2_view_root, repo_root=root),
        "l2_metadata_path": _to_display_path(paths.l2_view_root / "_meta.json", repo_root=root),
        "diary_root": _to_display_path(paths.diary_root, repo_root=root),
        "reports_root": _to_display_path(paths.reports_root, repo_root=root),
        "exports_root": _to_display_path(paths.exports_root, repo_root=root),
        "integrations_root": _to_display_path(paths.integrations_root, repo_root=root),
    }

    legacy_paths = _collect_legacy_paths(root)
    git_tracking = _collect_git_tracking(root)
    generated_views = _collect_generated_views(root, paths=canonical_paths)
    advisory_summary = _collect_advisory(config_section, canonical_paths, legacy_paths, git_tracking, generated_views)

    return WorkspaceInspectReport(
        config=config_section,
        canonical_paths=canonical_paths,
        legacy_paths=legacy_paths,
        git_tracking=git_tracking,
        generated_views=generated_views,
        advisory_summary=advisory_summary,
    )


def workspace_inspect_report_to_dict(report: WorkspaceInspectReport) -> dict:
    return {
        "advisory": True,
        "writes_files": False,
        "command": "workspace_inspect",
        "config": report.config,
        "canonical_paths": report.canonical_paths,
        "legacy_paths": [item.to_dict() for item in report.legacy_paths],
        "git_tracking": [item.to_dict() for item in report.git_tracking],
        "generated_views": report.generated_views.to_dict(),
        "advisory_summary": list(report.advisory_summary),
    }


def format_workspace_inspect_report(report: WorkspaceInspectReport) -> str:
    lines: List[str] = [t("cli.workspace.inspect.title"), ""]

    lines.append(t("cli.workspace.inspect.section.config"))
    lines.append(f"- active_config: {report.config.get('active_config', '')}")
    lines.append(f"- legacy_config_detected: {str(report.config.get('legacy_config_detected', False)).lower()}")
    lines.append(f"- source_roots: {', '.join(report.config.get('source_roots') or [])}")
    lines.append(f"- code_roots: {', '.join(report.config.get('code_roots') or [])}")
    lines.append("")

    lines.append(t("cli.workspace.inspect.section.canonical_paths"))
    for key in (
        "config_root",
        "policy_root",
        "state_root",
        "cache_root",
        "views_root",
        "project_structure_path",
        "modules_view_root",
        "l2_view_root",
        "l2_metadata_path",
        "diary_root",
        "reports_root",
        "exports_root",
        "integrations_root",
    ):
        lines.append(f"- {key}: {report.canonical_paths.get(key, '')}")
    lines.append("")

    lines.append(t("cli.workspace.inspect.section.legacy_paths"))
    for item in report.legacy_paths:
        lines.append(
            f"- {item.path}: exists={str(item.exists).lower()} role={item.role} severity={item.severity.upper()}"
        )
    lines.append("")

    lines.append(t("cli.workspace.inspect.section.git_tracking"))
    for item in report.git_tracking:
        lines.append(
            f"- {item.path}: ignored={str(item.ignored).lower()} expected={item.expected} severity={item.severity.upper()} ({item.note})"
        )
    lines.append("")

    lines.append(t("cli.workspace.inspect.section.generated_views"))
    gv = report.generated_views
    lines.append(f"- project_structure_exists: {str(gv.project_structure_exists).lower()}")
    lines.append(f"- module_capsule_count: {gv.module_capsule_count}")
    lines.append(f"- l2_readme_count: {gv.l2_readme_count}")
    lines.append(f"- diary_file_count: {gv.diary_file_count}")
    lines.append(f"- report_file_count: {gv.report_file_count}")
    lines.append(f"- skill_count: {gv.skill_count}")
    lines.append("")

    lines.append(t("cli.workspace.inspect.section.advisory"))
    for entry in report.advisory_summary:
        lines.append(f"- {entry.get('severity', 'info').upper()}: {entry.get('message', '')}")

    return "\n".join(lines).rstrip()


def _collect_legacy_paths(repo_root: Path) -> List[WorkspaceLegacyPathStatus]:
    rows = [
        (".harbor/config.yaml", "legacy config"),
        (".harbor/l2_meta.json", "legacy metadata"),
        ("specs/diary", "legacy diary"),
        ("docs/harbor", "optional docs export"),
        ("docs/harbor/modules", "optional docs export"),
        ("docs/harbor/project-structure.md", "optional docs export"),
    ]
    out: List[WorkspaceLegacyPathStatus] = []
    for rel, role in rows:
        exists = (repo_root / rel).exists()
        severity: Severity = "pass"
        if role in ("legacy config", "legacy metadata", "legacy diary") and exists:
            severity = "warn"
        elif role == "optional docs export" and exists:
            severity = "info"
        out.append(WorkspaceLegacyPathStatus(path=rel, exists=exists, role=role, severity=severity))
    return out


def _collect_git_tracking(repo_root: Path) -> List[WorkspaceGitTrackingStatus]:
    candidates = [
        (".harbor/config/harbor.yaml", "trackable"),
        (".harbor/views/project-structure.md", "trackable"),
        (".harbor/views/modules", "trackable"),
        (".harbor/views/l2", "trackable"),
        (".harbor/diary", "trackable"),
        (".harbor/cache", "ignored"),
        (".harbor/state", "ignored"),
        (".harbor/exports", "ignored"),
        ("docs/design", "trackable"),
        ("docs/harbor", "optional"),
        (".agents/skills", "optional"),
    ]
    out: List[WorkspaceGitTrackingStatus] = []
    for rel, expected in candidates:
        ignored = _check_git_ignored(repo_root, rel)
        severity, note = _classify_git_tracking(expected=expected, ignored=ignored)
        out.append(
            WorkspaceGitTrackingStatus(
                path=rel,
                ignored=ignored,
                expected=expected,
                severity=severity,
                note=note,
            )
        )
    return out


def _collect_generated_views(repo_root: Path, *, paths: Dict[str, str]) -> WorkspaceGeneratedViewsStatus:
    views_root = repo_root / paths["views_root"]
    modules_root = repo_root / paths["modules_view_root"]
    l2_root = repo_root / paths["l2_view_root"]
    diary_root = repo_root / paths["diary_root"]
    reports_root = repo_root / paths["reports_root"]
    project_structure_path = repo_root / paths["project_structure_path"]

    module_capsule_count = len({card.parent.as_posix() for card in modules_root.glob("**/module-card.md")})
    l2_readme_count = len(list(l2_root.glob("**/README.md")))
    diary_file_count = len(list(diary_root.glob("*.jsonl")))
    report_file_count = len([p for p in reports_root.rglob("*") if p.is_file()])
    skill_count = len(list((repo_root / ".agents" / "skills").glob("**/SKILL.md")))

    return WorkspaceGeneratedViewsStatus(
        project_structure_exists=project_structure_path.exists(),
        module_capsule_count=module_capsule_count,
        l2_readme_count=l2_readme_count,
        diary_file_count=diary_file_count,
        report_file_count=report_file_count,
        skill_count=skill_count,
    )


def _collect_advisory(
    config_section: Dict[str, Any],
    canonical_paths: Dict[str, str],
    legacy_paths: List[WorkspaceLegacyPathStatus],
    git_tracking: List[WorkspaceGitTrackingStatus],
    generated_views: WorkspaceGeneratedViewsStatus,
) -> List[Dict[str, str]]:
    advisories: List[Dict[str, str]] = []

    if generated_views.project_structure_exists:
        advisories.append({"severity": "pass", "message": t("cli.workspace.inspect.advisory.project_structure.pass")})
    else:
        advisories.append({"severity": "warn", "message": t("cli.workspace.inspect.advisory.project_structure.warn")})

    legacy_meta = next((row for row in legacy_paths if row.path == ".harbor/l2_meta.json"), None)
    if legacy_meta and legacy_meta.exists:
        advisories.append({"severity": "warn", "message": t("cli.workspace.inspect.advisory.legacy_l2_meta.warn")})
    else:
        advisories.append({"severity": "pass", "message": t("cli.workspace.inspect.advisory.legacy_l2_meta.pass")})

    legacy_diary = next((row for row in legacy_paths if row.path == "specs/diary"), None)
    if legacy_diary and legacy_diary.exists:
        advisories.append({"severity": "warn", "message": t("cli.workspace.inspect.advisory.legacy_diary.warn")})
    else:
        advisories.append({"severity": "pass", "message": t("cli.workspace.inspect.advisory.legacy_diary.pass")})

    cache_git = next((row for row in git_tracking if row.path == ".harbor/cache"), None)
    if cache_git:
        if cache_git.ignored is True:
            advisories.append({"severity": "pass", "message": t("cli.workspace.inspect.advisory.cache_ignored.pass")})
        elif cache_git.ignored == "unknown":
            advisories.append({"severity": "info", "message": t("cli.workspace.inspect.advisory.cache_ignored.unknown")})
        else:
            advisories.append({"severity": "warn", "message": t("cli.workspace.inspect.advisory.cache_ignored.warn")})

    views_git = next((row for row in git_tracking if row.path == ".harbor/views/project-structure.md"), None)
    if views_git:
        if views_git.ignored is False:
            advisories.append({"severity": "pass", "message": t("cli.workspace.inspect.advisory.views_trackable.pass")})
        elif views_git.ignored == "unknown":
            advisories.append(
                {"severity": "info", "message": t("cli.workspace.inspect.advisory.views_trackable.unknown")}
            )
        else:
            advisories.append({"severity": "warn", "message": t("cli.workspace.inspect.advisory.views_trackable.warn")})

    if config_section.get("legacy_config_detected"):
        advisories.append({"severity": "warn", "message": t("cli.workspace.inspect.advisory.legacy_config.warn")})

    _ = canonical_paths  # keep signature contract stable for potential future advisory expansion
    return advisories


def _classify_git_tracking(expected: GitExpected, ignored: GitIgnored) -> tuple[Severity, str]:
    if ignored == "unknown":
        return "info", t("cli.workspace.inspect.git.unknown")
    if expected == "ignored":
        return ("pass", t("cli.workspace.inspect.git.expected_ignored")) if ignored is True else (
            "warn",
            t("cli.workspace.inspect.git.expected_ignored_but_trackable"),
        )
    if expected == "trackable":
        return ("pass", t("cli.workspace.inspect.git.expected_trackable")) if ignored is False else (
            "warn",
            t("cli.workspace.inspect.git.expected_trackable_but_ignored"),
        )
    return "info", t("cli.workspace.inspect.git.optional")


def _check_git_ignored(repo_root: Path, rel_path: str) -> GitIgnored:
    try:
        result = subprocess.run(
            ["git", "check-ignore", rel_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        # For directory rules (e.g. ".harbor/state/"), probing one nested path
        # avoids false negatives when the directory itself is not materialized.
        if result.returncode == 1:
            probe = rel_path.rstrip("/\\") + "/.harbor_ignore_probe"
            nested = subprocess.run(
                ["git", "check-ignore", probe],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if nested.returncode == 0:
                return True
            if nested.returncode not in (0, 1):
                return "unknown"
    except Exception:
        return "unknown"
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return "unknown"


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
