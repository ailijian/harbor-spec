from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, Optional

import yaml


_WINDOWS_ABS_RE = re.compile(r"^[a-zA-Z]:[\\/]")
_WINDOWS_UNC_RE = re.compile(r"^[\\/]{2}[^\\/]+[\\/][^\\/]+")


@dataclass(frozen=True)
class HarborWorkspacePaths:
    workspace_root: Path
    config_root: Path
    policy_root: Path
    state_root: Path
    cache_root: Path
    views_root: Path
    project_structure_path: Path
    modules_view_root: Path
    l2_view_root: Path
    diary_root: Path
    reports_root: Path
    exports_root: Path
    integrations_root: Path


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes", "on"):
            return True
        if v in ("0", "false", "no", "off"):
            return False
    return default


def _looks_like_windows_absolute_path(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    normalized = raw.replace("\\", "/")
    return bool(_WINDOWS_ABS_RE.match(raw)) or bool(_WINDOWS_UNC_RE.match(raw)) or normalized.startswith("//")


def _normalize_path_like(value: Any, *, repo_root: Path) -> Path:
    if isinstance(value, Path):
        raw = value.as_posix()
    else:
        raw = str(value or "").strip()

    if not raw:
        return repo_root

    candidate: Path
    if _looks_like_windows_absolute_path(raw):
        # Preserve Windows-style absolute inputs as absolute-like values on POSIX
        # instead of incorrectly rebasing them into the current repository.
        candidate = Path(PureWindowsPath(raw).as_posix())
        if candidate.is_absolute():
            return candidate.resolve()
    else:
        # Normalize slashes so Windows/POSIX style relative paths behave consistently.
        normalized = raw.replace("\\", "/")
        candidate = Path(normalized)

    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _validate_within_repo(path: Path, *, repo_root: Path, field_name: str, raw_value: Any) -> None:
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(
            f"Invalid workspace path for '{field_name}': '{raw_value}'. "
            f"Resolved path '{path.as_posix()}' escapes repo root '{repo_root.as_posix()}'."
        ) from exc


def _build_path(
    value: Any,
    *,
    repo_root: Path,
    field_name: str,
    default: str,
    enforce_within_repo: bool,
) -> Path:
    raw_value = value if value not in (None, "") else default
    resolved = _normalize_path_like(raw_value, repo_root=repo_root)
    if enforce_within_repo:
        _validate_within_repo(resolved, repo_root=repo_root, field_name=field_name, raw_value=raw_value)
    return resolved


def load_workspace_config(repo_root: Path) -> Dict[str, Any]:
    root = Path(repo_root).resolve()
    new_config_path = root / ".harbor" / "config" / "harbor.yaml"
    legacy_config_path = root / ".harbor" / "config.yaml"

    source_path: Optional[Path] = None
    payload: Dict[str, Any] = {}

    for candidate in (new_config_path, legacy_config_path):
        if not candidate.exists():
            continue
        source_path = candidate
        try:
            payload = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            raise RuntimeError(f"ConfigError: failed to load {candidate.as_posix()}") from exc
        break

    return {
        "config": payload,
        "source_path": source_path,
        "new_config_path": new_config_path,
        "legacy_config_path": legacy_config_path,
    }


def resolve_workspace_config_path(repo_root: Path) -> Path:
    loaded = load_workspace_config(repo_root)
    return (loaded.get("source_path") or loaded.get("new_config_path")).resolve()


def write_workspace_config(repo_root: Path, data: Dict[str, Any]) -> Path:
    """Write the canonical Harbor workspace config file.

    Behavior:
      - Writes the canonical workspace config to `.harbor/config/harbor.yaml`.
      - Creates parent directories when they do not already exist.
      - Replaces the full file content with the provided YAML mapping.

    Args:
      repo_root (Path): Repository root used to resolve the canonical config path.
      data (Dict[str, Any]): YAML-serializable workspace config payload.

    Returns:
      Path: Absolute path to the written canonical config file.

    File Write Targets:
      - `.harbor/config/harbor.yaml`

    Side Effects:
      - Creates `.harbor/config/` when missing.
      - Overwrites the canonical config file content.

    Idempotency:
      - Deterministic for the same `repo_root` and `data`.

    Security:
      - Must not write outside the repository root.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    root = Path(repo_root).resolve()
    target = root / ".harbor" / "config" / "harbor.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(data or {}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return target


def parse_workspace_export_options(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = config or {}
    views_cfg = cfg.get("views", {}) or {}
    views_export_docs_cfg = (((views_cfg.get("export", {}) or {}).get("docs", {})) or {})

    l2_cfg = cfg.get("l2", {}) or {}
    l2_export_module_readme_cfg = (((l2_cfg.get("export", {}) or {}).get("module_readme", {})) or {})

    return {
        "views": {
            "docs": {
                "enabled": _to_bool(views_export_docs_cfg.get("enabled"), default=False),
                "root": str(views_export_docs_cfg.get("root") or "docs/harbor"),
            }
        },
        "l2": {
            "module_readme": {
                "enabled": _to_bool(l2_export_module_readme_cfg.get("enabled"), default=True),
            }
        },
    }


def build_workspace_paths(
    repo_root: Path,
    config: Optional[Dict[str, Any]] = None,
    *,
    enforce_write_safety: bool = True,
) -> HarborWorkspacePaths:
    root = Path(repo_root).resolve()
    cfg = config or {}

    workspace_root = _build_path(
        (cfg.get("workspace", {}) or {}).get("root"),
        repo_root=root,
        field_name="workspace.root",
        default=".harbor",
        enforce_within_repo=enforce_write_safety,
    )

    config_root = _build_path(
        (cfg.get("config", {}) or {}).get("root"),
        repo_root=root,
        field_name="config.root",
        default=str(workspace_root / "config"),
        enforce_within_repo=enforce_write_safety,
    )
    policy_root = _build_path(
        (cfg.get("policy", {}) or {}).get("root"),
        repo_root=root,
        field_name="policy.root",
        default=str(workspace_root / "policy"),
        enforce_within_repo=enforce_write_safety,
    )
    state_root = _build_path(
        (cfg.get("state", {}) or {}).get("root"),
        repo_root=root,
        field_name="state.root",
        default=str(workspace_root / "state"),
        enforce_within_repo=enforce_write_safety,
    )
    cache_root = _build_path(
        (cfg.get("cache", {}) or {}).get("root"),
        repo_root=root,
        field_name="cache.root",
        default=str(workspace_root / "cache"),
        enforce_within_repo=enforce_write_safety,
    )
    views_root = _build_path(
        (cfg.get("views", {}) or {}).get("canonical_root"),
        repo_root=root,
        field_name="views.canonical_root",
        default=str(workspace_root / "views"),
        enforce_within_repo=enforce_write_safety,
    )
    project_structure_path = _build_path(
        (cfg.get("views", {}) or {}).get("project_structure_path"),
        repo_root=root,
        field_name="views.project_structure_path",
        default=str(views_root / "project-structure.md"),
        enforce_within_repo=enforce_write_safety,
    )
    modules_view_root = _build_path(
        (cfg.get("modules", {}) or {}).get("capsule_root"),
        repo_root=root,
        field_name="modules.capsule_root",
        default=str(views_root / "modules"),
        enforce_within_repo=enforce_write_safety,
    )
    l2_view_root = _build_path(
        (cfg.get("l2", {}) or {}).get("canonical_root"),
        repo_root=root,
        field_name="l2.canonical_root",
        default=str(views_root / "l2"),
        enforce_within_repo=enforce_write_safety,
    )
    diary_root = _build_path(
        (cfg.get("diary", {}) or {}).get("root"),
        repo_root=root,
        field_name="diary.root",
        default=str(workspace_root / "diary"),
        enforce_within_repo=enforce_write_safety,
    )
    reports_root = _build_path(
        (cfg.get("reports", {}) or {}).get("root"),
        repo_root=root,
        field_name="reports.root",
        default=str(workspace_root / "reports"),
        enforce_within_repo=enforce_write_safety,
    )
    exports_root = _build_path(
        (cfg.get("exports", {}) or {}).get("root"),
        repo_root=root,
        field_name="exports.root",
        default=str(workspace_root / "exports"),
        enforce_within_repo=enforce_write_safety,
    )
    integrations_root = _build_path(
        (cfg.get("integrations", {}) or {}).get("root"),
        repo_root=root,
        field_name="integrations.root",
        default=str(workspace_root / "integrations"),
        enforce_within_repo=enforce_write_safety,
    )

    return HarborWorkspacePaths(
        workspace_root=workspace_root,
        config_root=config_root,
        policy_root=policy_root,
        state_root=state_root,
        cache_root=cache_root,
        views_root=views_root,
        project_structure_path=project_structure_path,
        modules_view_root=modules_view_root,
        l2_view_root=l2_view_root,
        diary_root=diary_root,
        reports_root=reports_root,
        exports_root=exports_root,
        integrations_root=integrations_root,
    )


def load_workspace_paths(repo_root: Path, *, enforce_write_safety: bool = True) -> HarborWorkspacePaths:
    loaded = load_workspace_config(repo_root)
    return build_workspace_paths(
        repo_root=repo_root,
        config=(loaded.get("config") or {}),
        enforce_write_safety=enforce_write_safety,
    )
