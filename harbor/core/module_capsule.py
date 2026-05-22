from __future__ import annotations
import ast

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


def _load_index(index_path: Optional[Path] = None, *, prefer_fresh_source: bool = False) -> Dict[str, Any]:
    return load_readonly_index(
        index_path=index_path,
        repo_root=Path.cwd(),
        prefer_fresh_source=prefer_fresh_source,
    )


def _belongs_to_module(file_path: str, module: str) -> bool:
    rel = (file_path or "").replace("\\", "/").strip("/")
    if not rel or not module:
        return False
    return rel == module or rel.startswith(f"{module}/")


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _module_profile(module: str) -> Dict[str, List[str]]:
    normalized = normalize_module_path(module)
    if normalized == "harbor/core" or normalized.startswith("harbor/core/"):
        return {
            "responsibility": [
                "Coordinates Harbor core workflows for generated context, stale checks, doctor checks, and verification.",
                "Owns workspace/path safety, file-write boundaries, and readonly index driven views.",
                "Hosts contract, DDT, CI, diary, baseline, and change-window related core logic.",
            ],
            "risks": [
                "JSON output and machine-readable CLI payload stability.",
                "Workspace path normalization, file write targets, and generated context safety.",
                "stale / doctor / verify-generated behavior drift across local and CI environments.",
                "Diary, change-window, and baseline logic that can mislead release or governance flows.",
            ],
            "review_focus": [
                "Check JSON output keys, file write targets, and workspace safety boundaries together.",
                "Verify generated context, stale, doctor, and verify-generated remain aligned.",
                "Inspect DDT, contract, and CI-facing metadata for additive vs blocking drift.",
            ],
        }
    if normalized == "harbor/cli" or normalized.startswith("harbor/cli/"):
        return {
            "responsibility": [
                "Defines Harbor CLI entrypoints, command routing, and user-visible workflow orchestration.",
                "Bridges core behaviors into stable flags, stdout/stderr, and exit behavior.",
            ],
            "risks": [
                "CLI args, exit behavior, and stdout/stderr contract drift.",
                "Windows/i18n text output and `--format json` compatibility.",
            ],
            "review_focus": [
                "Check CLI args, exit behavior, JSON output stability, and localized text together.",
                "Verify PowerShell/Windows stdout behavior remains parseable for JSON routes.",
            ],
        }
    if normalized == "harbor/adapters/typescript" or normalized.startswith("harbor/adapters/typescript/"):
        return {
            "responsibility": [
                "Implements TypeScript public-boundary, contract-source, and preview/advisory logic.",
                "Keeps TypeScript governance additive and non-blocking where v1.4.x requires preview-only behavior.",
            ],
            "risks": [
                "Preview/advisory semantics accidentally becoming blocking behavior.",
                "Incorrect JSDoc/TSDoc contract expectations or public-boundary explainability drift.",
            ],
            "review_focus": [
                "Preserve preview/advisory boundaries and avoid claiming formal TypeScript DDT or semantic audit gates.",
                "Check JSDoc/TSDoc proximity, contract_gap handling, and public-boundary explanation output.",
            ],
        }
    if normalized == "harbor/adapters/python" or normalized.startswith("harbor/adapters/python/"):
        return {
            "responsibility": [
                "Parses and normalizes Python contract-bearing source for Harbor governance workflows.",
                "Connects Python-specific syntax, compatibility, and export logic to the readonly index.",
            ],
            "risks": [
                "Parser/contract extraction regressions that silently reduce governance coverage.",
                "Cross-version compatibility and exported evidence drift.",
            ],
            "review_focus": [
                "Check parser output, contract extraction fidelity, and compatibility fallbacks.",
            ],
        }
    if normalized == "tests" or normalized.startswith("tests/"):
        return {
            "responsibility": [
                "Provides regression, contract, CLI, and generated-context coverage for Harbor behavior.",
            ],
            "risks": [
                "Weakening assertions or shifting tests away from contract intent.",
                "DDT/version binding drift and loss of coverage for strict targets.",
            ],
            "review_focus": [
                "Check whether assertions were weakened or no longer verify the intended contract.",
                "Inspect DDT/version expectations and generated-context assertions for stale assumptions.",
            ],
        }
    return {
        "responsibility": [
            f"Covers code and indexed contracts under `{normalized or '(unknown module)'}`.",
            "Acts as a generated maintenance view entrypoint for focused code changes.",
        ],
        "risks": [
            "Public behavior, schema, or file-write changes may require synchronized contract/test updates.",
        ],
        "review_focus": [
            "Check contract impact, test coverage, and runtime safety together before changing behavior.",
        ],
    }


def _keyword_tokens(module: str, key_files: List[str], contracts: List[Dict[str, str]]) -> List[str]:
    tokens = {module.split("/")[-1].lower()} if module else set()
    for file_path in key_files:
        stem = Path(file_path).stem.lower()
        if stem and stem != "__init__":
            tokens.add(stem)
    for contract in contracts:
        symbol = str(contract.get("symbol") or "").replace("(", ".").replace(")", ".")
        for part in symbol.replace("/", ".").split("."):
            part = part.strip().lower()
            if len(part) >= 3:
                tokens.add(part)
    tokens.discard("")
    return sorted(tokens)


def _contracts_by_file(contracts: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for contract in contracts or []:
        rel = _normalize_rel_path(str(contract.get("file") or ""))
        if not rel:
            continue
        grouped.setdefault(rel, []).append(contract)
    return grouped


def _extract_import_tokens(source: str) -> List[str]:
    if not source.strip():
        return []
    try:
        tree = ast.parse(source)
    except Exception:
        return []
    tokens: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                tokens.append(str(alias.name or ""))
        elif isinstance(node, ast.ImportFrom):
            module = str(node.module or "")
            if module:
                tokens.append(module)
            for alias in node.names:
                name = str(alias.name or "")
                if module and name:
                    tokens.append(f"{module}.{name}")
                elif name:
                    tokens.append(name)
    return tokens


def _score_debug_file(
    module: str,
    file_path: str,
    contracts: List[Dict[str, str]],
    tests: List[str],
) -> tuple[int, List[str]]:
    rel = _normalize_rel_path(file_path)
    base = Path(rel).name.lower()
    stem = Path(rel).stem.lower()
    grouped = _contracts_by_file(contracts)
    file_contracts = grouped.get(rel, [])
    module_name = module.split("/")[-1].lower() if module else ""

    score = 0
    reasons: List[str] = []
    if base == "__init__.py":
        return (-100, ["package marker only"])
    if base == "main.py":
        score += 120
        reasons.append("entrypoint")
    if base in {"module_capsule.py", "l2.py", "project_structure.py", "generated_verify.py", "stale.py", "doctor.py", "workspace.py", "sync.py"}:
        score += 70
        reasons.append("workflow file")
    if file_contracts:
        score += 45
        reasons.append("indexed contracts")
    if any(str(c.get("strictness") or "").lower() == "strict" for c in file_contracts):
        score += 20
        reasons.append("strict target")
    if module_name and module_name in stem:
        score += 15
        reasons.append("module-name match")
    if any(stem and stem in Path(test_path).stem.lower() for test_path in tests):
        score += 10
        reasons.append("covered by matching tests")
    if rel.endswith(".py"):
        score += 5
    return (score, reasons or ["module context"])


def _rank_debug_files(context: Dict[str, Any], *, limit: int = 5) -> List[Dict[str, Any]]:
    module = str(context.get("module") or "")
    key_files = [_normalize_rel_path(str(p)) for p in (context.get("key_files") or []) if str(p)]
    contracts = list(context.get("contracts") or [])
    tests = [_normalize_rel_path(str(p)) for p in (context.get("tests") or []) if str(p)]
    ranked = []
    for file_path in key_files:
        score, reasons = _score_debug_file(module, file_path, contracts, tests)
        ranked.append({"path": file_path, "score": score, "reason": ", ".join(reasons[:2])})
    ranked.sort(key=lambda item: (-item["score"], item["path"]))
    return ranked[:limit]


def _score_test_candidate(
    module: str,
    test_path: str,
    key_files: List[str],
    contracts: List[Dict[str, str]],
    import_tokens: List[str],
    text: str,
) -> tuple[int, List[str]]:
    name = Path(test_path).stem.lower()
    module_name = module.split("/")[-1].lower() if module else ""
    key_stems = {Path(fp).stem.lower() for fp in key_files if Path(fp).stem and Path(fp).stem != "__init__"}
    contract_tokens = _keyword_tokens(module, key_files, contracts)
    imports_text = " ".join(import_tokens).lower()
    lower_text = text.lower()

    score = 0
    reasons: List[str] = []
    if module_name and module_name in name:
        score += 30
        reasons.append("module match")
    if any(stem and stem in name for stem in key_stems):
        score += 20
        reasons.append("file-name match")
    if any(token and token in imports_text for token in contract_tokens):
        score += 35
        reasons.append("imports target symbols")
    if any(token and token in lower_text for token in contract_tokens[:10]):
        score += 10
        reasons.append("mentions target workflow")
    if "assert" in lower_text:
        score += 5
    if "ddt" in lower_text or "l3_version" in lower_text:
        score += 10
        reasons.append("ddt-aware")
    return (score, reasons or ["nearby regression coverage"])


def _rank_tests(context: Dict[str, Any], *, limit: int = 3) -> List[Dict[str, Any]]:
    module = str(context.get("module") or "")
    key_files = [_normalize_rel_path(str(p)) for p in (context.get("key_files") or []) if str(p)]
    contracts = list(context.get("contracts") or [])
    ranked: List[Dict[str, Any]] = []
    for test_path in (context.get("tests") or []):
        rel = _normalize_rel_path(str(test_path))
        if not rel:
            continue
        text = _safe_read_text(Path(rel))
        imports = _extract_import_tokens(text)
        score, reasons = _score_test_candidate(module, rel, key_files, contracts, imports, text)
        ranked.append({"path": rel, "score": score, "reason": ", ".join(reasons[:2])})
    ranked.sort(key=lambda item: (-item["score"], item["path"]))
    return ranked[:limit]


def _format_bullets(values: List[str]) -> List[str]:
    if not values:
        return ["- None."]
    return [f"- {value}" for value in values]


def _workflow_group_specs(module: str) -> List[Dict[str, Any]]:
    normalized = normalize_module_path(module)
    specs: List[Dict[str, Any]] = [
        {
            "title": "Generated context / verify / stale / doctor",
            "description": "Use this path for generated context rendering, stale diagnosis, and verify-generated drift.",
            "keywords": ["generated", "verify", "stale", "doctor", "l2", "module_capsule", "project_structure"],
        },
        {
            "title": "CLI / JSON output",
            "description": "Use this path when behavior is visible through CLI text, CI JSON, or stable serialization.",
            "keywords": ["cli", "json", "to_dict", "report_to_dict", "ci", "main"],
        },
        {
            "title": "Workspace path / file write safety",
            "description": "Use this path for path normalization, repo-relative writes, export roots, and write safety.",
            "keywords": ["workspace", "path", "write", "export", "resolve"],
        },
        {
            "title": "Diary / log / change-window",
            "description": "Use this path for decision memory, log draft flow, baseline, and change-window state.",
            "keywords": ["diary", "log", "change_window", "baseline"],
        },
        {
            "title": "TypeScript adapter / public boundary preview",
            "description": "Use this path for TypeScript preview, public-boundary explainability, and advisory output.",
            "keywords": ["typescript", "preview", "public_boundary", "verification", "audit"],
        },
        {
            "title": "Tests / DDT / fixtures",
            "description": "Use this path for DDT bindings, fixture-backed regression checks, and contract-oriented tests.",
            "keywords": ["tests", "ddt", "fixture", "fixtures", "binding", "contract"],
        },
    ]
    if normalized == "harbor/adapters/typescript" or normalized.startswith("harbor/adapters/typescript/"):
        preferred = [
            "TypeScript adapter / public boundary preview",
            "Tests / DDT / fixtures",
            "CLI / JSON output",
        ]
        specs.sort(key=lambda item: (preferred.index(item["title"]) if item["title"] in preferred else len(preferred), item["title"]))
    return specs


def _workflow_file_matches(
    module: str,
    file_path: str,
    contracts: List[Dict[str, str]],
    tests: List[str],
    keywords: List[str],
) -> tuple[int, List[str]]:
    score, base_reasons = _score_debug_file(module, file_path, contracts, tests)
    lowered_path = file_path.lower()
    lowered_contracts = " ".join(
        f"{c.get('symbol', '')} {c.get('scope', '')} {c.get('strictness', '')}"
        for c in contracts
        if _normalize_rel_path(str(c.get("file") or "")) == _normalize_rel_path(file_path)
    ).lower()
    reasons: List[str] = []
    if any(keyword in lowered_path for keyword in keywords):
        score += 55
        reasons.append("keyword-matched entry file")
    if lowered_contracts and any(keyword in lowered_contracts for keyword in keywords):
        score += 28
        reasons.append("indexed contract evidence")
    reasons.extend(base_reasons[:2])
    unique_reasons: List[str] = []
    for reason in reasons:
        if reason not in unique_reasons:
            unique_reasons.append(reason)
    return score, unique_reasons


def _workflow_test_matches(
    module: str,
    test_path: str,
    key_files: List[str],
    contracts: List[Dict[str, str]],
    keywords: List[str],
) -> tuple[int, List[str]]:
    text = _safe_read_text(Path(test_path))
    imports = _extract_import_tokens(text)
    score, base_reasons = _score_test_candidate(module, test_path, key_files, contracts, imports, text)
    lowered = f"{test_path} {' '.join(imports)} {text}".lower()
    reasons: List[str] = []
    if any(keyword in lowered for keyword in keywords):
        score += 35
        reasons.append("workflow-specific assert/import evidence")
    if "fixture" in lowered:
        score += 10
        reasons.append("fixture coverage")
    reasons.extend(base_reasons[:2])
    unique_reasons: List[str] = []
    for reason in reasons:
        if reason not in unique_reasons:
            unique_reasons.append(reason)
    return score, unique_reasons


def _build_workflow_recommendations(
    context: Dict[str, Any],
    *,
    file_limit: int = 2,
    test_limit: int = 2,
    group_limit: int = 6,
) -> List[Dict[str, Any]]:
    module = str(context.get("module") or "")
    key_files = [_normalize_rel_path(str(p)) for p in (context.get("key_files") or []) if str(p)]
    contracts = list(context.get("contracts") or [])
    tests = [_normalize_rel_path(str(p)) for p in (context.get("tests") or []) if str(p)]
    groups: List[Dict[str, Any]] = []
    for spec in _workflow_group_specs(module):
        ranked_files: List[Dict[str, str]] = []
        for file_path in key_files:
            score, reasons = _workflow_file_matches(module, file_path, contracts, tests, spec["keywords"])
            if score <= 0:
                continue
            ranked_files.append({"path": file_path, "score": score, "reason": ", ".join(reasons[:3])})
        ranked_files.sort(key=lambda item: (-int(item["score"]), item["path"]))

        ranked_tests: List[Dict[str, str]] = []
        for test_path in tests:
            score, reasons = _workflow_test_matches(module, test_path, key_files, contracts, spec["keywords"])
            if score <= 0:
                continue
            ranked_tests.append({"path": test_path, "score": score, "reason": ", ".join(reasons[:3])})
        ranked_tests.sort(key=lambda item: (-int(item["score"]), item["path"]))

        if not ranked_files and not ranked_tests:
            continue
        groups.append(
            {
                "title": spec["title"],
                "description": spec["description"],
                "files": ranked_files[:file_limit],
                "tests": ranked_tests[:test_limit],
                "score": max(
                    [int(item["score"]) for item in ranked_files[:file_limit] + ranked_tests[:test_limit]] or [0]
                ),
            }
        )
    groups.sort(key=lambda item: (-int(item["score"]), item["title"]))
    return groups[:group_limit]


def _module_specific_checklist_lines(module: str) -> List[str]:
    normalized = normalize_module_path(module)
    if normalized == "harbor/core" or normalized.startswith("harbor/core/"):
        return [
            "- Check JSON output stability, file write targets, and workspace path safety together.",
            "- Re-verify stale / doctor / verify-generated behavior if generated context or workspace logic changed.",
            "- Confirm generated context remains aligned with source-of-truth code, tests, and policy.",
        ]
    if normalized == "harbor/cli" or normalized.startswith("harbor/cli/"):
        return [
            "- Check CLI args, stdout/stderr, exit codes, and `--format json` key stability together.",
            "- Verify i18n and Windows stdout compatibility for human-readable vs JSON routes.",
        ]
    if normalized == "harbor/adapters/typescript" or normalized.startswith("harbor/adapters/typescript/"):
        return [
            "- Preserve preview/advisory boundaries; do not imply a formal TypeScript DDT or semantic audit gate.",
            "- Check nearby JSDoc/TSDoc expectations, contract_gap handling, and public-boundary explanation output.",
        ]
    if normalized == "tests" or normalized.startswith("tests/"):
        return [
            "- Check whether assertions were weakened or no longer verify the intended contract.",
            "- Inspect DDT/version expectations and generated-context assertions for stale assumptions.",
        ]
    return [
        "- Check module-specific public behavior, contracts, and runtime safety boundaries together.",
    ]


def detect_tests_for_module(module: str, key_files: List[str], tests_root: Optional[Path] = None) -> List[str]:
    root = tests_root or Path("tests")
    if not root.exists():
        return []

    contracts = [{"file": fp, "symbol": Path(fp).stem, "scope": "unknown", "strictness": "standard"} for fp in key_files]
    ranked: List[tuple[int, str]] = []
    for test_file in root.rglob("test_*.py"):
        rel = test_file.as_posix()
        text = _safe_read_text(test_file)
        imports = _extract_import_tokens(text)
        score, _ = _score_test_candidate(module, rel, key_files, contracts, imports, text)
        if score > 0:
            ranked.append((score, rel))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [rel for _, rel in ranked]


def collect_module_context(
    module: str,
    index_path: Optional[Path] = None,
    *,
    prefer_fresh_source: bool = False,
) -> Dict[str, Any]:
    """Collect readonly context records used to render one module capsule.

    Behavior:
      - Loads indexed files, contracts, and detected tests for one module.
      - Supports `prefer_fresh_source=True` so generated-context writes and
        stale checks derive context from the same fresh/source readonly index
        used by clean CI validation.
      - Module capsule generation can therefore bypass runtime cache snapshots
        when source-derived readonly records are available.
      - Writes no files and does not mutate runtime cache state.

    Args:
      module (str): Repo-relative module path.
      index_path (Optional[Path]): Optional explicit readonly index path.
      prefer_fresh_source (bool): Prefer transient source-derived records over
        runtime cache snapshots when possible.

    Returns:
      Dict[str, Any]: Stable module context used by capsule generation/checks.

    Side Effects:
      - Reads source-derived or cached readonly index state plus detected test
        file names.
      - Writes no files.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    normalized = normalize_module_path(module)
    idx = _load_index(index_path=index_path, prefer_fresh_source=prefer_fresh_source)
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
    profile = _module_profile(str(module))
    ranked_files = _rank_debug_files(context, limit=5)
    ranked_tests = _rank_tests(context, limit=3)
    entry_points = ranked_files[:3]
    remaining_files = [item for item in ranked_files if item["path"] not in {row["path"] for row in entry_points}]

    lines: List[str] = [
        f"# Module Card: {module}",
        "",
        "> This file is generated by Harbor-spec.",
        "> It is a derived maintenance view, not a source of truth.",
        "",
        "## Responsibility",
        "",
    ]
    lines.extend(_format_bullets(profile["responsibility"]))
    lines.extend(
        [
            "",
            "## High-Risk Boundaries",
            "",
        ]
    )
    lines.extend(_format_bullets(profile["risks"]))
    lines.extend(
        [
            "",
            "## Common Change Entry Points",
            "",
        ]
    )
    if entry_points:
        lines.extend([f"- {item['path']} ({item['reason']})" for item in entry_points])
    else:
        lines.append(f"- {module or '(unknown module)'}")
    lines.extend(
        [
            "",
            "## Best Files To Inspect First",
            "",
        ]
    )
    if remaining_files:
        lines.extend([f"- {item['path']} ({item['reason']})" for item in remaining_files])
    elif entry_points:
        lines.append("- Common change entry points already cover the primary file starts for this module.")
    else:
        lines.append(f"- {module or '(unknown module)'}")
    lines.extend(
        [
            "",
            "## Relevant Tests",
            "",
        ]
    )
    if ranked_tests:
        lines.extend([f"- {item['path']} ({item['reason']})" for item in ranked_tests])
    else:
        lines.append("- No test files detected by Harbor.")
    lines.extend(
        [
            "",
            "## Detailed Key Files",
            "",
            "<details>",
            "<summary>All key files</summary>",
            "",
            "```text",
        ]
    )
    if key_files:
        lines.extend(key_files)
    else:
        lines.append("No indexed files found for this module.")
    lines.extend(
        [
            "```",
            "",
            "</details>",
            "",
            "## Detailed Indexed Contracts",
            "",
        ]
    )
    if contracts:
        lines.extend(
            [
                "<details>",
                "<summary>All indexed contracts</summary>",
                "",
                "| Symbol | File | Scope | Strictness |",
                "| ------ | ---- | ----- | ---------- |",
            ]
        )
        for c in contracts:
            lines.append(
                f"| {c.get('symbol','')} | {c.get('file','')} | {c.get('scope','unknown')} | {c.get('strictness','standard')} |"
            )
        lines.extend(["", "</details>"])
    else:
        lines.extend(["```text", "No indexed contracts found for this module.", "```"])

    lines.extend(
        [
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
    lines = [
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
        "## Generated Context Checks",
        "",
        "- If behavior or boundaries changed, refresh and re-check generated context instead of editing it manually.",
        "- Check project-structure, L2 README, and Module Capsule for stale or misleading summaries.",
        "",
        "## Diary Need",
        "",
        "- If this change affects workflow semantics, generated context shape, or release-relevant behavior, draft a Diary entry.",
        "",
        "## Module-Specific Focus",
        "",
    ]
    lines.extend(_module_specific_checklist_lines(str(module)))
    lines.extend(
        [
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
            "Generated Context:",
            "Semantic Drift:",
            "Runtime Safety:",
            "Diary Draft:",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def generate_debug_playbook(context: Dict[str, Any]) -> str:
    module = context.get("module", "")
    ranked_files = _rank_debug_files(context, limit=3)
    ranked_tests = _rank_tests(context, limit=3)
    workflow_groups = _build_workflow_recommendations(context)

    lines = [
        f"# Debug Playbook: {module}",
        "",
        "> This file is generated by Harbor-spec.",
        "> It is a derived debug guide, not a source of truth.",
        "",
        "## Workflow Entry Points",
        "",
    ]
    if workflow_groups:
        for group in workflow_groups:
            lines.extend(
                [
                    f"### {group['title']}",
                    "",
                    f"- Why: {group['description']}",
                ]
            )
            if group["files"]:
                for item in group["files"]:
                    lines.append(f"- File: {item['path']} ({item['reason']})")
            if group["tests"]:
                for item in group["tests"]:
                    lines.append(f"- Test: {item['path']} ({item['reason']})")
            lines.append("")
        if lines[-1] == "":
            lines.pop()
    else:
        lines.append(f"- {module or '(unknown module)'}")
    lines.extend(["", "## First Files to Inspect", ""])
    if ranked_files:
        lines.extend([f"- {item['path']} ({item['reason']})" for item in ranked_files])
    else:
        lines.append(f"- {module or '(unknown module)'}")
    lines.extend(["", "## Minimal Checks", "", "Run targeted tests first if available.", ""])

    if ranked_tests:
        lines.append("```powershell")
        for item in ranked_tests:
            lines.append(f"pytest {item['path']}")
        lines.append("```")
        lines.extend(["", "## Why These Tests", ""])
        lines.extend([f"- {item['path']} ({item['reason']})" for item in ranked_tests])
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
