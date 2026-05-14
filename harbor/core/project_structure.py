from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from harbor.core.l2 import infer_module_from_path
from harbor.core.context_integrity import build_context_integrity_metadata, compose_markdown_with_frontmatter
from harbor.core.module_capsule import normalize_module_path
from harbor.core.module_skill import normalize_skill_slug
from harbor.core.readonly_index import load_readonly_index
from harbor.core.workspace import load_workspace_config, load_workspace_paths, parse_workspace_export_options


@dataclass
class ProjectMetadata:
    name: Optional[str]
    version: Optional[str]
    description: Optional[str]
    entrypoint: Optional[str]


@dataclass
class ProjectModuleSummary:
    module: str
    key_files: List[str]
    indexed_files_count: int
    indexed_contracts_count: int
    has_l2_readme: bool
    has_module_capsule: bool
    has_skill: bool


@dataclass
class ProjectAreaSummary:
    area: str
    purpose: str
    discovered_files_count: int
    indexed_contracts_count: int


@dataclass
class ProjectStructureContext:
    metadata: ProjectMetadata
    modules: List[ProjectModuleSummary]
    supporting_areas: List["ProjectSupportingSummary"]
    key_areas: List[ProjectAreaSummary]
    has_indexed_modules: bool
    discovery_mode: str
    contract_aware: str
    has_real_index_records: bool


@dataclass
class ProjectSupportingSummary:
    area: str
    purpose: str
    key_files: List[str]


@dataclass
class ProjectStructureWriteResult:
    canonical_path: Path
    exported_paths: List[Path]


def _normalize_rel_path(value: str) -> str:
    return (value or "").replace("\\", "/").strip("/")


def _looks_like_windows_absolute_path(path_text: str) -> bool:
    normalized = str(path_text or "").strip().replace("\\", "/")
    return bool(re.match(r"(?i)^[a-z]:/", normalized)) or normalized.startswith("//")


def _to_project_relative_path(file_path: str, root: Path) -> str:
    raw = str(file_path or "").strip()
    if not raw:
        return ""
    norm = raw.replace("\\", "/")
    if _looks_like_windows_absolute_path(norm):
        marker = f"/{root.name.lower()}/"
        lower = norm.lower()
        idx = lower.find(marker)
        if idx == -1:
            return ""
        return _normalize_rel_path(norm[idx + len(marker) :])
    try:
        path_obj = Path(norm)
    except Exception:
        return _normalize_rel_path(norm)
    if path_obj.is_absolute():
        try:
            return path_obj.resolve().relative_to(root.resolve()).as_posix()
        except Exception:
            return ""
    return _normalize_rel_path(norm)


def _sanitize_module(module: str, root: Path) -> str:
    mod = normalize_module_path(module)
    if not mod:
        return ""
    head = mod.split("/", 1)[0]
    if ":" in head:
        rel = _to_project_relative_path(mod, root)
        if not rel:
            return ""
        return normalize_module_path(rel)
    return mod


def _belongs_to_module(file_path: str, module: str) -> bool:
    rel = _normalize_rel_path(file_path)
    mod = normalize_module_path(module)
    if not rel or not mod:
        return False
    return rel == mod or rel.startswith(f"{mod}/")


def _load_index(
    root: Path,
    *,
    index_path: Optional[Path] = None,
    prefer_fresh_source: bool = True,
) -> Dict[str, Any]:
    return load_readonly_index(
        index_path=index_path,
        repo_root=root,
        prefer_fresh_source=prefer_fresh_source,
    )


def _collect_fallback_files(root: Path) -> List[str]:
    candidates = ["harbor/cli", "harbor/core", "harbor/utils", "tests", "docs"]
    patterns = ("*.py", "*.md")
    files: List[str] = []
    for rel_dir in candidates:
        base = root / rel_dir
        if not base.exists() or not base.is_dir():
            continue
        for pattern in patterns:
            for path in sorted(base.rglob(pattern)):
                if not path.is_file():
                    continue
                try:
                    rel = path.resolve().relative_to(root.resolve()).as_posix()
                except Exception:
                    continue
                files.append(_normalize_rel_path(rel))
    return sorted({f for f in files if f})


def _build_transient_index_from_files(files: List[str]) -> Dict[str, Any]:
    return {
        "files": {
            fp: {
                "items": [],
            }
            for fp in sorted({f for f in files if f})
        }
    }


def _extract_toml_string_block(text: str, section: str, key: str) -> Optional[str]:
    pattern = rf"^\[{re.escape(section)}\]\s*$([\s\S]*?)(?=^\[|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return None
    block = match.group(1)
    key_match = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]*)"\s*$', block, flags=re.MULTILINE)
    if not key_match:
        return None
    value = key_match.group(1).strip()
    return value or None


def _read_project_metadata(root: Path) -> ProjectMetadata:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return ProjectMetadata(name=None, version=None, description=None, entrypoint=None)
    try:
        text = pyproject.read_text(encoding="utf-8")
    except Exception:
        return ProjectMetadata(name=None, version=None, description=None, entrypoint=None)

    entrypoint = _extract_toml_string_block(text, "project.scripts", "harbor")
    return ProjectMetadata(
        name=_extract_toml_string_block(text, "project", "name"),
        version=_extract_toml_string_block(text, "project", "version"),
        description=_extract_toml_string_block(text, "project", "description"),
        entrypoint=entrypoint,
    )


def _capsule_exists(root: Path, module: str) -> bool:
    base = root / "docs" / "harbor" / "modules" / Path(module)
    required = ["module-card.md", "review-checklist.md", "debug-playbook.md"]
    return all((base / name).exists() for name in required)


def _skill_exists(root: Path, module: str) -> bool:
    slug = normalize_skill_slug(module)
    return (root / ".agents" / "skills" / f"harbor-debug-{slug}" / "SKILL.md").exists()


def _area_purpose(area: str) -> str:
    mapping = {
        "harbor/cli": "CLI command parsing and workflow facade",
        "harbor/core": "Core Harbor logic",
        "harbor/utils": "Shared utilities",
        "tests": "Test suite",
        "docs": "Documentation",
    }
    if area in mapping:
        return mapping[area]
    return f"Derived from indexed files under {area}."


def _supporting_area_purpose(area: str) -> str:
    mapping = {
        "tests": "Test suite",
        "tests/core": "Core test suite",
        "tests/fixtures_sqlite": "Test fixtures",
        "docs": "Documentation",
        "docs/harbor": "Harbor rule and guide documents",
    }
    if area in mapping:
        return mapping[area]
    return f"Derived from discovered files under {area}."


def _infer_area(file_path: str) -> str:
    rel = _normalize_rel_path(file_path)
    for area in ["harbor/cli", "harbor/core", "harbor/utils", "tests", "docs"]:
        if rel == area or rel.startswith(f"{area}/"):
            return area
    first = rel.split("/", 1)[0] if rel else "unknown"
    return first or "unknown"


def _key_files_display(values: List[str], limit: int = 3) -> List[str]:
    files = sorted(
        {_normalize_rel_path(v) for v in values if _normalize_rel_path(v)},
        key=rank_key_file,
    )
    if len(files) <= limit:
        return files
    tail = len(files) - limit
    return files[:limit] + [f"... (+{tail} more)"]


def classify_project_area(module: str, key_files: Optional[List[str]] = None) -> str:
    mod = normalize_module_path(module)
    if not mod:
        return "supporting"

    code_prefixes = [
        "harbor/cli",
        "harbor/core",
        "harbor/utils",
        "app",
        "src",
        "packages",
        "backend",
        "frontend",
    ]
    supporting_prefixes = [
        "tests",
        "docs",
        "examples",
        "scripts",
    ]

    for prefix in code_prefixes:
        if mod == prefix or mod.startswith(f"{prefix}/"):
            return "code"
    for prefix in supporting_prefixes:
        if mod == prefix or mod.startswith(f"{prefix}/"):
            return "supporting"

    files = [_normalize_rel_path(v) for v in (key_files or []) if _normalize_rel_path(v)]
    has_python = any(f.endswith(".py") for f in files)
    has_explicit_supporting_path = any(
        f.startswith("tests/") or f.startswith("docs/") or f.startswith("scripts/") for f in files
    )
    if has_python and not has_explicit_supporting_path:
        return "code"
    return "supporting"


def rank_key_file(path: str) -> tuple:
    rel = _normalize_rel_path(path)
    base = Path(rel).name.lower()

    entry_files = {"main.py", "cli.py", "app.py", "server.py"}
    semantic_files = {
        "l2.py",
        "module_capsule.py",
        "module_skill.py",
        "project_structure.py",
        "stale.py",
        "doctor.py",
        "sync.py",
        "index.py",
        "storage.py",
        "ddt.py",
        "audit.py",
    }
    is_test_py = rel.endswith(".py") and (base.startswith("test_") or base.endswith("_test.py"))
    is_impl_py = rel.endswith(".py") and base != "__init__.py" and not is_test_py

    if base in entry_files:
        priority = 1
    elif base in semantic_files:
        priority = 2
    elif is_impl_py:
        priority = 3
    elif is_test_py:
        priority = 4
    elif base == "readme.md" or rel.endswith(".md"):
        priority = 5
    elif base == "__init__.py":
        priority = 6
    else:
        priority = 7
    return (priority, rel)


def _table_cell(value: Optional[str]) -> str:
    text = (value or "").strip()
    if not text:
        return "-"
    return text.replace("|", r"\|")


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def collect_project_structure_integrity_inputs(
    root: Path,
    index_path: Optional[Path] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Collect deterministic integrity inputs for project-structure generation.

    Behavior:
      - Uses fresh/source-derived readonly index semantics so clean CI and local
        generation derive canonical integrity inputs from the same repo state.
      - Falls back to repo-scoped filesystem discovery when no readonly index
        records are available.
      - Excludes absolute paths outside `root` from generated metadata.
      - Must not depend on local runtime cache presence for canonical output.

    Args:
      root (Path): Repository root used for repo-relative filtering.
      index_path (Optional[Path]): Optional readonly index override.

    Returns:
      Tuple[List[str], List[Dict[str, Any]]]: Stable `source_paths` and
      `contract_records` for context-integrity metadata.

    Side Effects:
      - Reads source files, workspace config, and readonly index inputs only.
      - Writes no files.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    root = Path(root).resolve()
    idx = _load_index(root, index_path=index_path, prefer_fresh_source=True)
    source_paths: List[str] = []
    contract_records: List[Dict[str, Any]] = []
    for fp, meta in (idx.get("files") or {}).items():
        rel = _to_project_relative_path(str(fp), root)
        if not rel:
            continue
        source_paths.append(rel)
        for item in meta.get("items", []) or []:
            contract_records.append(
                {
                    "symbol": str(item.get("qualified_name") or item.get("id") or item.get("name") or ""),
                    "file": rel,
                    "scope": str(item.get("scope") or ""),
                    "strictness": str(item.get("strictness") or ""),
                }
            )
    normalized_source_paths = sorted({_normalize_rel_path(path) for path in source_paths if _normalize_rel_path(path)})
    if not normalized_source_paths:
        normalized_source_paths = _collect_fallback_files(root)
    return normalized_source_paths, contract_records


def collect_project_structure_context(root: Path, index_path: Optional[Path] = None) -> ProjectStructureContext:
    """Collect the canonical project-structure context from index or filesystem.

    Behavior:
      - Uses fresh/source-derived readonly index semantics so local generation
        and clean CI observe the same canonical project structure inputs.
      - Falls back to filesystem discovery within `root` only when no readonly
        index records are available.
      - Normalizes path separators to POSIX-style display paths.
      - Includes only repo-relative files and modules; absolute paths outside
        `root`, including Windows-style absolute paths on POSIX runners, are
        ignored instead of being surfaced as project modules.
      - Must not depend on local runtime cache presence for canonical output.

    Args:
      root (Path): Repository root used for repo-relative filtering.
      index_path (Optional[Path]): Optional Harbor index path override.

    Returns:
      ProjectStructureContext: Deterministic project structure summary.

    Side Effects:
      - Reads index / workspace files only.
      - Writes no files.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    root = root.resolve()
    idx_path = index_path or (root / ".harbor" / "cache" / "l3_index.json")
    index_data = _load_index(root, index_path=idx_path, prefer_fresh_source=True)

    valid_files: List[str] = []
    for fp in (index_data.get("files") or {}).keys():
        rel = _to_project_relative_path(str(fp), root)
        if rel:
            valid_files.append(rel)

    has_real_index_records = bool(valid_files)
    used_filesystem_fallback = False
    if not valid_files:
        fallback_files = _collect_fallback_files(root)
        if fallback_files:
            index_data = _build_transient_index_from_files(fallback_files)
            valid_files = fallback_files
            used_filesystem_fallback = True

    if has_real_index_records and used_filesystem_fallback:
        discovery_mode = "Harbor index + filesystem fallback"
        contract_aware = "partial"
    elif has_real_index_records:
        discovery_mode = "Harbor index"
        contract_aware = "yes"
    else:
        discovery_mode = "filesystem fallback"
        contract_aware = "no"

    module_set = set()
    for fp, meta in (index_data.get("files") or {}).items():
        rel = _to_project_relative_path(str(fp), root)
        if not rel or not (meta.get("items") or []):
            continue
        module = _sanitize_module(infer_module_from_path(rel), root)
        if module:
            module_set.add(module)
    if not module_set:
        for fp in valid_files:
            rel = _to_project_relative_path(str(fp), root)
            module = _sanitize_module(infer_module_from_path(rel), root)
            if module:
                module_set.add(module)
    modules = sorted(module_set)

    code_modules: List[ProjectModuleSummary] = []
    supporting_areas: List[ProjectSupportingSummary] = []
    for module in modules:
        module_norm = normalize_module_path(module)
        module_files: List[str] = []
        contract_count = 0
        for fp, meta in (index_data.get("files") or {}).items():
            rel = _to_project_relative_path(str(fp), root)
            if not _belongs_to_module(rel, module_norm):
                continue
            module_files.append(rel)
            contract_count += len(meta.get("items", []) or [])
        unique_files = sorted({_normalize_rel_path(p) for p in module_files if _normalize_rel_path(p)})
        key_files = _key_files_display(unique_files)
        if classify_project_area(module_norm, unique_files) == "code":
            code_modules.append(
                ProjectModuleSummary(
                    module=module_norm,
                    key_files=key_files,
                    indexed_files_count=len(unique_files),
                    indexed_contracts_count=contract_count,
                    has_l2_readme=(root / module_norm / "README.md").exists(),
                    has_module_capsule=_capsule_exists(root, module_norm),
                    has_skill=_skill_exists(root, module_norm),
                )
            )
        else:
            supporting_areas.append(
                ProjectSupportingSummary(
                    area=module_norm,
                    purpose=_supporting_area_purpose(module_norm),
                    key_files=key_files,
                )
            )

    code_modules = sorted(code_modules, key=lambda x: x.module)
    supporting_areas = sorted(supporting_areas, key=lambda x: x.area)

    area_stats: Dict[str, Dict[str, int]] = {}
    for fp, meta in (index_data.get("files") or {}).items():
        rel = _to_project_relative_path(str(fp), root)
        if not rel:
            continue
        area = _infer_area(rel)
        area_stats.setdefault(area, {"files": 0, "contracts": 0})
        area_stats[area]["files"] += 1
        area_stats[area]["contracts"] += len(meta.get("items", []) or [])

    ordered_areas: List[str] = []
    for area in ["harbor/cli", "harbor/core", "harbor/utils", "tests", "docs"]:
        if area in area_stats:
            ordered_areas.append(area)
    for area in sorted(area_stats):
        if area not in ordered_areas:
            ordered_areas.append(area)

    key_areas = [
        ProjectAreaSummary(
            area=area,
            purpose=_area_purpose(area),
            discovered_files_count=area_stats[area]["files"],
            indexed_contracts_count=area_stats[area]["contracts"],
        )
        for area in ordered_areas
    ]

    return ProjectStructureContext(
        metadata=_read_project_metadata(root),
        modules=code_modules,
        supporting_areas=supporting_areas,
        key_areas=key_areas,
        has_indexed_modules=bool(code_modules),
        discovery_mode=discovery_mode,
        contract_aware=contract_aware,
        has_real_index_records=has_real_index_records,
    )


def generate_project_structure_markdown(context: ProjectStructureContext) -> str:
    """Render a deterministic Markdown view from project-structure context.

    Behavior:
      - Produces the canonical project-structure Markdown body.
      - Preserves stable section ordering for metadata, discovery mode,
        modules, supporting areas, and regeneration guidance.
      - Must not expose filtered outside-repo absolute paths when the input
        context was built from repo-scoped project files.

    Args:
      context (ProjectStructureContext): Prepared project structure context.

    Returns:
      str: Markdown body without frontmatter.

    Side Effects:
      - Pure formatter; writes no files.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    metadata = context.metadata
    discovery_notes = {
        "filesystem fallback": "No Harbor index records were found, so this view was generated from filesystem discovery.",
        "Harbor index": "This view was generated from Harbor indexed records.",
        "Harbor index + filesystem fallback": "This view combines Harbor indexed records with filesystem fallback discovery.",
    }
    lines: List[str] = [
        "# Project Structure",
        "",
        "> Generated by Harbor-spec.",
        "> This is a derived project-level structure view, not a source of truth.",
        "",
        "## Project Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Name | {_table_cell(metadata.name)} |",
        f"| Version | {_table_cell(metadata.version)} |",
        f"| Description | {_table_cell(metadata.description)} |",
        f"| CLI Entrypoint | {_table_cell(metadata.entrypoint)} |",
        "",
        "## Discovery Mode",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Mode | {_table_cell(context.discovery_mode)} |",
        f"| Contract-aware | {_table_cell(context.contract_aware)} |",
        f"| Notes | {_table_cell(discovery_notes.get(context.discovery_mode, '-'))} |",
        "",
        "When Discovery Mode is `filesystem fallback`, contract counts may be 0 because no Harbor index records were available.",
        "Run `harbor lock` or `harbor adopt <path>` to build richer contract-aware structure.",
        "",
        "## Source of Truth",
        "",
        "This file is derived from indexed code, contracts, tests, module capsules, and project metadata.",
        "",
        "Do not edit this file as the source of truth.",
        "",
        "Update the underlying code, contracts, schemas, tests, or Harbor metadata, then regenerate this view.",
        "",
        "## Key Areas",
        "",
        "| Area | Purpose | Discovered Files | Indexed Contracts |",
        "|---|---|---:|---:|",
    ]
    if context.key_areas:
        for area in context.key_areas:
            lines.append(
                f"| {_table_cell(area.area)} | {_table_cell(area.purpose)} | {area.discovered_files_count} | {area.indexed_contracts_count} |"
            )
    else:
        lines.append("| - | No indexed files found. | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Code Modules",
            "",
            "| Module | Key Files | L2 README | Module Capsule | Skill |",
            "|---|---|---|---|---|",
        ]
    )
    if context.modules:
        for module in context.modules:
            key_files = ", ".join(module.key_files) if module.key_files else "-"
            lines.append(
                f"| {_table_cell(module.module)} | {_table_cell(key_files)} | {_yes_no(module.has_l2_readme)} | {_yes_no(module.has_module_capsule)} | {_yes_no(module.has_skill)} |"
            )
    else:
        lines.append("| - | - | no | no | no |")
        lines.append("")
        lines.append("No indexed modules found.")

    lines.extend(
        [
            "",
            "## Supporting Areas",
            "",
            "| Area | Purpose | Key Files |",
            "|---|---|---|",
        ]
    )
    if context.supporting_areas:
        for area in context.supporting_areas:
            key_files = ", ".join(area.key_files) if area.key_files else "-"
            lines.append(
                f"| {_table_cell(area.area)} | {_table_cell(area.purpose)} | {_table_cell(key_files)} |"
            )
    else:
        lines.append("| - | - | - |")

    lines.extend(
        [
            "",
            "## Main Harbor Workflows",
            "",
            "### AI Coding Workflow",
            "",
            "```text",
            "harbor start",
            "AI coding",
            "harbor checkpoint",
            "AI coding",
            "harbor finish --sync-context",
            "harbor stale",
            "harbor doctor",
            "```",
            "",
            "### L2 README Workflow",
            "",
            "```text",
            "harbor docs --module <module>",
            "harbor docs --changed --write",
            "harbor docs --all --write",
            "```",
            "",
            "### Module Capsule Workflow",
            "",
            "```text",
            "harbor module inspect <module>",
            "harbor module seal <module> --write",
            "harbor module stale <module>",
            "harbor module promote-skill <module>",
            "```",
            "",
            "### Health Check Workflow",
            "",
            "```text",
            "harbor stale",
            "harbor doctor",
            "```",
            "",
            "## Where to Look First",
            "",
            "| Task | Start Here |",
            "|---|---|",
            "| CLI behavior | harbor/cli/main.py |",
            "| L2 README generation | harbor/core/l2.py |",
            "| Module Capsule generation | harbor/core/module_capsule.py |",
            "| Module Skill promotion | harbor/core/module_skill.py |",
            "| Stale checks | harbor/core/stale.py |",
            "| Doctor checks | harbor/core/doctor.py |",
            "| i18n text | harbor/utils/i18n.py |",
            "| Release metadata | pyproject.toml, RELEASE.md |",
            "| Tests | tests/ |",
            "",
            "## AI Context Loading Guidance",
            "",
            "For most coding tasks, load context in this order:",
            "",
            "1. `AGENTS.md`",
            "2. Project Rules, if present",
            "3. `.harbor/views/project-structure.md`",
            "4. Relevant L2 README",
            "5. Relevant Module Capsule",
            "6. Relevant source files",
            "7. Relevant tests",
            "",
            "Do not read the whole repository unless the project structure and module capsule are insufficient.",
            "",
            "## Regeneration",
            "",
            "To preview this file:",
            "",
            "```powershell",
            "harbor project structure",
            "```",
            "",
            "To update this file:",
            "",
            "```powershell",
            "harbor project structure --write",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _resolve_docs_export_project_structure_path(root: Path, config: Optional[Dict[str, Any]]) -> Optional[Path]:
    options = parse_workspace_export_options(config)
    docs_options = (options.get("views", {}) or {}).get("docs", {}) or {}
    if not bool(docs_options.get("enabled")):
        return None

    raw_root = str(docs_options.get("root") or "docs/harbor").strip()
    normalized_root = raw_root.replace("\\", "/")
    export_root = Path(normalized_root)
    if _looks_like_windows_absolute_path(raw_root) and not export_root.is_absolute():
        raise ValueError(
            f"Invalid workspace path for 'views.export.docs.root': '{raw_root}'. "
            f"Resolved path '{normalized_root}' escapes repo root '{root.resolve().as_posix()}'."
        )
    if not export_root.is_absolute():
        export_root = root / export_root
    export_root = export_root.resolve()
    try:
        export_root.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(
            f"Invalid workspace path for 'views.export.docs.root': '{raw_root}'. "
            f"Resolved path '{export_root.as_posix()}' escapes repo root '{root.resolve().as_posix()}'."
        ) from exc
    return export_root / "project-structure.md"


def write_project_structure(context: ProjectStructureContext, root: Path) -> ProjectStructureWriteResult:
    """Write the canonical project-structure view and optional export copy.

    Behavior:
      - Renders the project-structure Markdown for `context`.
      - Writes the canonical generated view under `.harbor/views/**`.
      - Optionally writes a configured export copy when the export target stays
        inside `root`.
      - Builds source-path integrity metadata from
        `collect_project_structure_integrity_inputs()` so writers and verifiers
        share the same fresh/source-derived readonly index semantics.
      - Excludes absolute paths outside `root`, including Windows-style
        absolute paths on POSIX runners, from generated metadata and output.
      - Must not depend on local runtime cache presence for canonical output.

    Args:
      context (ProjectStructureContext): Prepared project structure context.
      root (Path): Repository root used for generated write safety.

    Returns:
      ProjectStructureWriteResult: Canonical path plus any export paths written.

    Side Effects:
      - Writes generated Markdown files under approved workspace/export paths.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    root = Path(root).resolve()
    body = generate_project_structure_markdown(context)
    source_paths, contract_records = collect_project_structure_integrity_inputs(root)
    metadata = build_context_integrity_metadata(
        view_type="project_structure",
        module=None,
        generation_command="harbor project structure --write",
        source_paths=source_paths,
        contract_records=contract_records,
        repo_root=root,
    )

    workspace_paths = load_workspace_paths(root, enforce_write_safety=True)
    canonical_path = workspace_paths.project_structure_path
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    previous = ""
    if canonical_path.exists():
        try:
            previous = canonical_path.read_text(encoding="utf-8")
        except Exception:
            previous = ""
    markdown = compose_markdown_with_frontmatter(previous, metadata, body)
    canonical_path.write_text(markdown, encoding="utf-8")

    loaded = load_workspace_config(root)
    config = loaded.get("config") or {}
    export_path = _resolve_docs_export_project_structure_path(root, config)
    exported_paths: List[Path] = []
    if export_path is not None:
        if export_path.resolve() != canonical_path.resolve():
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(markdown, encoding="utf-8")
            exported_paths.append(export_path)

    return ProjectStructureWriteResult(
        canonical_path=canonical_path,
        exported_paths=exported_paths,
    )
