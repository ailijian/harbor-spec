from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from harbor.core.context_integrity import (
    build_context_integrity_metadata,
    compose_markdown_with_frontmatter,
    extract_integrity_fingerprints,
)
from harbor.core.readonly_index import load_readonly_index
from harbor.core.workspace import (
    _looks_like_windows_absolute_path,
    load_workspace_config,
    load_workspace_paths,
    parse_workspace_export_options,
)


@dataclass
class ModuleCapsuleWriteResult:
    canonical_paths: List[Path]
    exported_paths: List[Path]


def normalize_module_path(module: str) -> str:
    raw = (module or "").strip().replace("\\", "/")
    while "//" in raw:
        raw = raw.replace("//", "/")
    return raw.strip("/")


def module_capsule_dir(module: str, output_root: Optional[Path] = None) -> Path:
    root = output_root or (Path(".harbor") / "views" / "modules")
    normalized = normalize_module_path(module)
    return root / normalized


def _ensure_within_root(path: Path, *, root: Path, field_name: str, raw_value: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(
            f"Invalid workspace path for '{field_name}': '{raw_value}'. "
            f"Resolved path '{path.resolve().as_posix()}' escapes repo root '{root.resolve().as_posix()}'."
        ) from exc


def _safe_module_subpath(module: str) -> str:
    normalized = normalize_module_path(module)
    if not normalized:
        return normalized
    if normalized.startswith("/") or _looks_like_windows_absolute_path(normalized):
        raise ValueError(f"Invalid module path: '{module}'. Absolute paths are not allowed.")
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise ValueError(f"Invalid module path: '{module}'. Relative parent segments are not allowed.")
    return "/".join(parts)


def _resolve_module_target_dir(base_dir: Path, module: str) -> Path:
    safe_module = _safe_module_subpath(module)
    candidate = (base_dir / safe_module).resolve()
    _ensure_within_root(candidate, root=base_dir, field_name="module", raw_value=module)
    return candidate


def _resolve_docs_export_modules_root(root: Path, config: Optional[Dict[str, Any]]) -> Optional[Path]:
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
    _ensure_within_root(
        export_root,
        root=root,
        field_name="views.export.docs.root",
        raw_value=raw_root,
    )
    return export_root / "modules"


def resolve_module_capsule_paths(
    module: str,
    *,
    root: Optional[Path] = None,
    output_root: Optional[Path] = None,
) -> Dict[str, Optional[Path]]:
    repo_root = (root or Path.cwd()).resolve()
    if output_root is not None:
        canonical_root = output_root.resolve()
        canonical_dir = _resolve_module_target_dir(canonical_root, module)
        return {
            "canonical_dir": canonical_dir,
            "export_dir": None,
        }

    workspace_paths = load_workspace_paths(repo_root, enforce_write_safety=True)
    canonical_root = workspace_paths.modules_view_root.resolve()
    _ensure_within_root(
        canonical_root,
        root=repo_root,
        field_name="modules.capsule_root",
        raw_value=canonical_root.as_posix(),
    )
    canonical_dir = _resolve_module_target_dir(canonical_root, module)

    loaded = load_workspace_config(repo_root)
    config = loaded.get("config") or {}
    export_modules_root = _resolve_docs_export_modules_root(repo_root, config)
    export_dir: Optional[Path] = None
    if export_modules_root is not None:
        export_modules_root = export_modules_root.resolve()
        _ensure_within_root(
            export_modules_root,
            root=repo_root,
            field_name="views.export.docs.root",
            raw_value=export_modules_root.as_posix(),
        )
        export_dir = _resolve_module_target_dir(export_modules_root, module)

    return {
        "canonical_dir": canonical_dir,
        "export_dir": export_dir,
    }


def _sort_unique(values: List[str]) -> List[str]:
    return sorted({v for v in values if v})


def _normalize_rel_path(value: str) -> str:
    return (value or "").replace("\\", "/").strip("/")


def _stable_contract_rows(contracts: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for c in contracts or []:
        symbol = str(c.get("symbol") or "").strip()
        if not symbol:
            continue
        rows.append(
            {
                "symbol": symbol,
                "file": _normalize_rel_path(str(c.get("file") or "")),
                "scope": str(c.get("scope") or "unknown"),
                "strictness": str(c.get("strictness") or "standard"),
            }
        )
    return sorted(rows, key=lambda x: (x["symbol"], x["file"], x["scope"], x["strictness"]))


def _strictness_rank(value: str) -> int:
    mapping = {"light": 1, "standard": 2, "strict": 3}
    return mapping.get((value or "standard").lower(), 2)


def _summarize_strictness(contracts: List[Dict[str, str]]) -> str:
    if not contracts:
        return "standard"
    top = max(_strictness_rank(c.get("strictness", "standard")) for c in contracts)
    if top >= 3:
        return "strict"
    if top <= 1:
        return "light"
    return "standard"


def _load_index(index_path: Optional[Path] = None) -> Dict[str, Any]:
    return load_readonly_index(index_path=index_path, repo_root=Path.cwd())


def _belongs_to_module(file_path: str, module: str) -> bool:
    rel = (file_path or "").replace("\\", "/").strip("/")
    if not rel or not module:
        return False
    return rel == module or rel.startswith(f"{module}/")


def detect_tests_for_module(module: str, key_files: List[str], tests_root: Optional[Path] = None) -> List[str]:
    root = tests_root or Path("tests")
    if not root.exists():
        return []

    module_name = module.split("/")[-1] if module else ""
    keywords = {module_name} if module_name else set()
    for fp in key_files:
        stem = Path(fp).stem
        if stem:
            keywords.add(stem)

    matches: List[str] = []
    for test_file in root.rglob("test_*.py"):
        rel = test_file.as_posix()
        name = test_file.stem.lower()
        if any(kw and kw.lower() in name for kw in keywords):
            matches.append(rel)
    return _sort_unique(matches)


def collect_module_context(module: str, index_path: Optional[Path] = None) -> Dict[str, Any]:
    normalized = normalize_module_path(module)
    idx = _load_index(index_path=index_path)
    key_files: List[str] = []
    contracts: List[Dict[str, str]] = []

    for fp, meta in (idx.get("files") or {}).items():
        rel = (str(fp) or "").replace("\\", "/").strip("/")
        if not _belongs_to_module(rel, normalized):
            continue
        key_files.append(rel)
        for item in meta.get("items", []) or []:
            symbol = item.get("qualified_name") or item.get("id") or item.get("name") or ""
            contracts.append(
                {
                    "symbol": str(symbol),
                    "file": rel,
                    "scope": str(item.get("scope") or "unknown"),
                    "strictness": str(item.get("strictness") or "standard"),
                }
            )

    key_files = _sort_unique(key_files)
    contracts = sorted(
        [c for c in contracts if c.get("symbol")],
        key=lambda x: (x.get("symbol", ""), x.get("file", "")),
    )
    tests = detect_tests_for_module(normalized, key_files)
    return {
        "module": normalized,
        "key_files": key_files,
        "contracts": contracts,
        "tests": tests,
        "strictness": _summarize_strictness(contracts),
    }


def compute_module_fingerprint(context: Dict[str, Any]) -> str:
    module = normalize_module_path(str(context.get("module") or ""))
    key_files = _sort_unique([_normalize_rel_path(str(p)) for p in (context.get("key_files") or [])])
    tests = _sort_unique([_normalize_rel_path(str(p)) for p in (context.get("tests") or [])])
    contracts = _stable_contract_rows(context.get("contracts") or [])
    strictness = str(context.get("strictness") or "standard")
    payload = {
        "module": module,
        "key_files": key_files,
        "contracts": contracts,
        "tests": tests,
        "strictness": strictness,
    }
    stable = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def read_capsule_fingerprint(module_card_path: Path) -> Optional[str]:
    if not module_card_path.exists():
        return None
    try:
        text = module_card_path.read_text(encoding="utf-8")
    except Exception:
        return None
    fp_payload = extract_integrity_fingerprints(text)
    fp = str(fp_payload.get("view_fingerprint") or fp_payload.get("fingerprint") or "").strip()
    return fp or None


def check_module_capsule_stale(
    context: Dict[str, Any],
    output_root: Optional[Path] = None,
    root: Optional[Path] = None,
) -> Dict[str, str]:
    module = normalize_module_path(str(context.get("module") or ""))
    key_files = context.get("key_files") or []
    contracts = context.get("contracts") or []
    current_fingerprint = compute_module_fingerprint(context)
    result = {
        "module": module,
        "status": "stale",
        "reason": "",
        "current_fingerprint": current_fingerprint,
        "stored_fingerprint": "",
    }
    if not key_files and not contracts:
        result["reason"] = "no indexed records found for module"
        return result

    paths = resolve_module_capsule_paths(module, root=root, output_root=output_root)
    canonical_dir = paths["canonical_dir"]
    assert canonical_dir is not None
    module_card_path = canonical_dir / "module-card.md"
    if not module_card_path.exists():
        result["reason"] = "module-card.md not found"
        return result

    stored = read_capsule_fingerprint(module_card_path)
    if not stored:
        result["reason"] = "fingerprint missing"
        return result

    result["stored_fingerprint"] = stored
    if stored != current_fingerprint:
        result["reason"] = "fingerprint mismatch"
        return result

    result["status"] = "up_to_date"
    result["reason"] = "up to date"
    return result


def generate_module_card(context: Dict[str, Any]) -> str:
    module = context.get("module", "")
    key_files = context.get("key_files", []) or []
    contracts = context.get("contracts", []) or []
    tests = context.get("tests", []) or []
    debug_entries = key_files[:2]

    lines: List[str] = [
        f"# Module Card: {module}",
        "",
        "> This file is generated by Harbor-spec.",
        "> It is a derived maintenance view, not a source of truth.",
        "",
        "## Responsibility",
        "",
        "This module appears to cover code under:",
        "",
        "```text",
        module or "(unknown module)",
        "```",
        "",
        "If this summary is too generic, update the underlying contracts or module documentation rather than treating this file as the source of truth.",
        "",
        "## Key Files",
        "",
        "```text",
    ]
    if key_files:
        lines.extend(key_files)
    else:
        lines.append("No indexed files found for this module.")
    lines.extend(
        [
            "```",
            "",
            "## Public / Indexed Contracts",
            "",
        ]
    )
    if contracts:
        lines.extend(
            [
                "| Symbol | File | Scope | Strictness |",
                "| ------ | ---- | ----- | ---------- |",
            ]
        )
        for c in contracts:
            lines.append(
                f"| {c.get('symbol','')} | {c.get('file','')} | {c.get('scope','unknown')} | {c.get('strictness','standard')} |"
            )
    else:
        lines.extend(["```text", "No indexed contracts found for this module.", "```"])

    lines.extend(["", "## Tests", "", "```text"])
    if tests:
        lines.extend(tests)
    else:
        lines.append("No test files detected by Harbor.")

    lines.extend(
        [
            "```",
            "",
            "## Review Focus",
            "",
            "* Check Contract Impact before changing public behavior.",
            "* Check schema/type drift if this module exposes data structures.",
            "* Check DDT/test coverage for strict targets.",
            "* Check Runtime Safety if this module writes files, changes data, or touches external systems.",
            "",
            "## Debug Entry Points",
            "",
            "Start with:",
            "",
            "```text",
        ]
    )
    if debug_entries:
        lines.extend(debug_entries)
    else:
        lines.append(module or "(unknown module)")

    lines.extend(
        [
            "```",
            "",
            "## Related Views",
            "",
            "```text",
            "L2 README:",
            f"  {module}/README.md",
            "",
            "Capsule files:",
            f"  .harbor/views/modules/{module}/review-checklist.md",
            f"  .harbor/views/modules/{module}/debug-playbook.md",
            "",
            "Optional docs export (if enabled):",
            f"  docs/harbor/modules/{module}/review-checklist.md",
            f"  docs/harbor/modules/{module}/debug-playbook.md",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def generate_review_checklist(context: Dict[str, Any]) -> str:
    module = context.get("module", "")
    return "\n".join(
        [
            f"# Review Checklist: {module}",
            "",
            "> This file is generated by Harbor-spec.",
            "> It helps AI coding assistants review this module without loading the whole repository.",
            "",
            "## Contract Checks",
            "",
            "- Did behavior, args, returns, raises, schema, side effects, state, idempotency, security, or external-visible result change?",
            "- If yes, update the relevant Contract before or together with implementation.",
            "- If no, state `Contract Impact: none`.",
            "",
            "## Schema / Type Checks",
            "",
            "- Check Pydantic models, OpenAPI, TypeScript types, event schemas, or database migrations if this module touches them.",
            "- Mark `[Contract Conflict]` if schema and docstring disagree.",
            "",
            "## DDT / Test Checks",
            "",
            "- Strict targets must use explicit `l3_version`.",
            '- Do not use `strategy="latest"` for strict targets.',
            "- Add or update tests for args boundary, returns, raises, side effects, and failure paths.",
            "",
            "## Runtime Safety Checks",
            "",
            "Ask before:",
            "",
            "- deleting files",
            "- changing migrations",
            "- changing CI/CD",
            "- touching secrets",
            "- installing dependencies",
            "- changing production config",
            "- modifying auth, permission, billing, or user data handling",
            "",
            "## Semantic Drift Checks",
            "",
            "Mark:",
            "",
            "```text",
            "[Possible Semantic Drift]",
            "```",
            "",
            "when implementation and contract may disagree.",
            "",
            "Mark:",
            "",
            "```text",
            "[Confirmed Semantic Drift]",
            "```",
            "",
            "when implementation definitely contradicts contract.",
            "",
            "## Final Review Output",
            "",
            "Use:",
            "",
            "```text",
            "Change Summary:",
            "Contract Impact:",
            "Strictness:",
            "Tests / DDT:",
            "Semantic Drift:",
            "Runtime Safety:",
            "Diary Draft:",
            "```",
            "",
        ]
    )


def generate_debug_playbook(context: Dict[str, Any]) -> str:
    module = context.get("module", "")
    key_files = context.get("key_files", []) or []
    tests = context.get("tests", []) or []

    lines = [
        f"# Debug Playbook: {module}",
        "",
        "> This file is generated by Harbor-spec.",
        "> It is a derived debug guide, not a source of truth.",
        "",
        "## First Files to Inspect",
        "",
        "```text",
    ]
    if key_files:
        lines.extend(key_files[:2])
    else:
        lines.append(module or "(unknown module)")
    lines.extend(["```", "", "## Minimal Checks", "", "Run targeted tests first if available.", ""])

    if tests:
        lines.extend(["```powershell", f"pytest {tests[0]}", "```"])
    else:
        lines.extend(
            [
                "```text",
                "No module-specific test command detected. Use project-level test commands from Project Rules.",
                "```",
            ]
        )

    lines.extend(
        [
            "",
            "## Common Debug Questions",
            "",
            "* What changed since the last passing state?",
            "* Did Contract Impact occur?",
            "* Did schema/type shape change?",
            "* Did a strict target lose DDT coverage?",
            "* Did implementation drift from docstring or schema?",
            "* Did path normalization or platform-specific behavior change?",
            "* Did the fix require a regression test?",
            "",
            "## Safe Fix Order",
            "",
            "1. Reproduce the issue.",
            "2. Identify relevant contract and schema.",
            "3. Add or update failing test if possible.",
            "4. Fix implementation.",
            "5. Re-run targeted tests.",
            "6. Check semantic drift.",
            "7. Draft Diary entry if the fix is important.",
            "",
            "## When to Escalate",
            "",
            "Escalate to full Harbor workflow if the fix touches:",
            "",
            "* public API",
            "* schema",
            "* parser/export/writeback",
            "* workflow",
            "* migration",
            "* security",
            "* user-visible behavior",
            "",
        ]
    )
    return "\n".join(lines)


def preview_module_capsule(context: Dict[str, Any]) -> Dict[str, str]:
    return {
        "module-card.md": generate_module_card(context),
        "review-checklist.md": generate_review_checklist(context),
        "debug-playbook.md": generate_debug_playbook(context),
    }


def build_module_card_frontmatter(
    module: str,
    *,
    source_paths: List[str],
    contract_records: List[Dict[str, Any]],
    repo_root: Path,
    generation_command: str,
    fingerprint: str,
) -> Dict[str, Any]:
    metadata = build_context_integrity_metadata(
        view_type="module_card",
        module=module,
        generation_command=generation_command,
        source_paths=source_paths,
        contract_records=contract_records,
        repo_root=repo_root,
    )
    metadata["view_fingerprint"] = fingerprint
    metadata["fingerprint"] = fingerprint
    return metadata


def write_module_capsule(
    context: Dict[str, Any],
    output_root: Optional[Path] = None,
    root: Optional[Path] = None,
) -> ModuleCapsuleWriteResult:
    """Write the canonical Module Capsule views for one module.

    Behavior:
      - Resolves canonical capsule paths under `.harbor/views/modules/**`.
      - Renders `module-card.md`, `review-checklist.md`, and `debug-playbook.md`.
      - Writes optional docs export copies only when the configured export root
        stays inside the repository.
      - Rejects parent traversal and cross-platform absolute module paths.

    Args:
      context (Dict[str, Any]): Module context used to render capsule views.
      output_root (Optional[Path]): Override for canonical output root in tests
        or targeted writes.
      root (Optional[Path]): Repository root used for path validation and
        integrity metadata generation.

    Returns:
      ModuleCapsuleWriteResult: Canonical and optional exported file paths that
      were written for this module.

    File Write Targets:
      - `.harbor/views/modules/<module>/module-card.md`
      - `.harbor/views/modules/<module>/review-checklist.md`
      - `.harbor/views/modules/<module>/debug-playbook.md`
      - Optional docs export copies under the configured docs root

    Side Effects:
      - Creates parent directories for generated module capsule files.
      - Overwrites generated capsule files with refreshed rendered content.

    Idempotency:
      - Deterministic for the same `context`, output roots, and repository state.

    Security:
      - Must not write outside the repository root or configured safe output roots.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    module_name = str(context.get("module", "") or "")
    paths = resolve_module_capsule_paths(module_name, root=root, output_root=output_root)
    canonical_dir = paths["canonical_dir"]
    export_dir = paths["export_dir"]
    assert canonical_dir is not None

    canonical_dir.mkdir(parents=True, exist_ok=True)
    previews = preview_module_capsule(context)
    canonical_paths: List[Path] = []
    module_norm = normalize_module_path(str(context.get("module") or ""))
    source_paths = _sort_unique([_normalize_rel_path(str(p)) for p in (context.get("key_files") or [])])
    contract_records = context.get("contracts") or []
    generation_command = f"harbor module seal {module_norm} --write"
    module_fp = compute_module_fingerprint(context)

    for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
        path = canonical_dir / name
        repo_root = (root or Path.cwd()).resolve()
        if name == "module-card.md":
            metadata = build_module_card_frontmatter(
                module_norm,
                source_paths=source_paths,
                contract_records=contract_records,
                repo_root=repo_root,
                generation_command=generation_command,
                fingerprint=module_fp,
            )
        else:
            view_type = {
                "review-checklist.md": "review_checklist",
                "debug-playbook.md": "debug_playbook",
            }[name]
            metadata = build_context_integrity_metadata(
                view_type=view_type,
                module=module_norm,
                generation_command=generation_command,
                source_paths=source_paths,
                contract_records=contract_records,
                repo_root=repo_root,
            )
        previous = ""
        if path.exists():
            try:
                previous = path.read_text(encoding="utf-8")
            except Exception:
                previous = ""
        rendered = compose_markdown_with_frontmatter(previous, metadata, previews[name])
        path.write_text(rendered, encoding="utf-8")
        canonical_paths.append(path)

    exported_paths: List[Path] = []
    if export_dir is not None and export_dir.resolve() != canonical_dir.resolve():
        export_dir.mkdir(parents=True, exist_ok=True)
        for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
            export_path = export_dir / name
            repo_root = (root or Path.cwd()).resolve()
            if name == "module-card.md":
                metadata = build_module_card_frontmatter(
                    module_norm,
                    source_paths=source_paths,
                    contract_records=contract_records,
                    repo_root=repo_root,
                    generation_command=generation_command,
                    fingerprint=module_fp,
                )
            else:
                view_type = {
                    "review-checklist.md": "review_checklist",
                    "debug-playbook.md": "debug_playbook",
                }[name]
                metadata = build_context_integrity_metadata(
                    view_type=view_type,
                    module=module_norm,
                    generation_command=generation_command,
                    source_paths=source_paths,
                    contract_records=contract_records,
                    repo_root=repo_root,
                )
            previous = ""
            if export_path.exists():
                try:
                    previous = export_path.read_text(encoding="utf-8")
                except Exception:
                    previous = ""
            rendered = compose_markdown_with_frontmatter(previous, metadata, previews[name])
            export_path.write_text(rendered, encoding="utf-8")
            exported_paths.append(export_path)

    return ModuleCapsuleWriteResult(
        canonical_paths=canonical_paths,
        exported_paths=exported_paths,
    )
