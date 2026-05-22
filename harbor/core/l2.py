from __future__ import annotations

import ast
import json
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from harbor.core.context_integrity import (
    build_context_integrity_metadata,
    compose_markdown_with_frontmatter,
    content_without_generated_at_for_compare,
)
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.path_normalization import looks_like_absolute_path, repo_relative_path
from harbor.core.readonly_index import load_readonly_index
from harbor.core.utils import find_function_node
from harbor.core.workspace import load_workspace_config, load_workspace_paths, parse_workspace_export_options


def infer_module_from_path(path: str | Path) -> str:
    """从文件路径推断模块目录（统一为 POSIX 风格）。"""
    raw = str(path or "").strip()
    if not raw:
        return ""
    norm = raw.replace("\\", "/")
    parts = [p for p in norm.split("/") if p and p != "."]
    if not parts:
        return ""
    last = parts[-1]
    if last == "__init__.py" or "." in last:
        parts = parts[:-1]
    module = "/".join(parts).strip("/")
    if module in ("", "."):
        return ""
    return module


def collect_modules_from_paths(paths: List[str | Path]) -> List[str]:
    modules = {infer_module_from_path(p) for p in paths}
    modules.discard("")
    return sorted(modules)


def _looks_like_windows_absolute_path(path_text: str) -> bool:
    normalized = str(path_text or "").strip().replace("\\", "/")
    return bool(re.match(r"(?i)^[a-z]:/", normalized)) or normalized.startswith("//")


def _repo_relative_index_path(path: str | Path, *, repo_root: Path) -> Optional[str]:
    raw = str(path or "").strip()
    if not raw:
        return None
    normalized = raw.replace("\\", "/")
    if not looks_like_absolute_path(normalized):
        return None
    return repo_relative_path(normalized, repo_root=repo_root)


def normalize_indexed_module_candidate(path: str | Path, *, repo_root: Optional[Path] = None) -> str:
    """将索引记录路径归一化为模块候选，优先映射 repo 内绝对路径。"""
    root = (repo_root or Path.cwd()).resolve()
    rel = _repo_relative_index_path(path, repo_root=root)
    if rel is not None:
        return infer_module_from_path(rel)
    return infer_module_from_path(path)


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _strictness_rank(value: str) -> int:
    mapping = {"light": 1, "standard": 2, "strict": 3}
    return mapping.get((value or "standard").lower(), 2)


def _display_strictness(value: Any, *, default: str = "unknown") -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"light", "standard", "strict"}:
        return normalized
    return default


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


def _resolve_import_token_to_module(token: str, *, repo_root: Path) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    parts = [part for part in raw.split(".") if part]
    while parts:
        rel = "/".join(parts)
        candidate_dir = repo_root / rel
        candidate_file = repo_root / f"{rel}.py"
        if candidate_dir.is_dir() or candidate_file.is_file():
            return rel.strip("/")
        parts = parts[:-1]
    return ""


def _dependency_group(module_path: str) -> str:
    normalized = str(module_path or "").replace("\\", "/").strip("/")
    if not normalized:
        return ""
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return ""
    if parts[0] == "harbor":
        if len(parts) >= 2:
            return "/".join(parts[:2])
        return ""
    if parts[0] == "tests":
        return "tests"
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0]


def _format_dependency_group_rows(groups: Dict[str, set[str]], *, sample_limit: int = 3, row_limit: int = 8) -> List[str]:
    rows: List[tuple[str, int, List[str]]] = []
    for group, values in groups.items():
        normalized_values = sorted({str(value or "").replace("\\", "/").strip("/") for value in values if str(value or "").strip("/")})
        if not group or not normalized_values:
            continue
        rows.append((group, len(normalized_values), normalized_values))
    rows.sort(key=lambda item: (-item[1], item[0]))

    rendered: List[str] = []
    for group, edge_count, samples in rows[:row_limit]:
        shown = samples[:sample_limit]
        omitted = max(0, len(samples) - len(shown))
        sample_text = ", ".join(shown)
        if omitted:
            sample_text = f"{sample_text}, ... (+{omitted} more)"
        rendered.append(f"{group} ({edge_count} edges): {sample_text}")
    return rendered


def _build_repo_import_graph(repo_root: Path) -> Dict[str, Dict[str, set[str]]]:
    imports_by_file: Dict[str, set[str]] = {}
    module_by_file: Dict[str, set[str]] = {}
    scan_roots = ["harbor", "tests"]
    all_python_files: List[Path] = []
    for root_name in scan_roots:
        root_dir = repo_root / root_name
        if root_dir.exists():
            all_python_files.extend(sorted(root_dir.rglob("*.py")))

    for abs_path in all_python_files:
        try:
            rel = abs_path.resolve().relative_to(repo_root).as_posix()
        except Exception:
            continue
        source = _safe_read_text(abs_path)
        imports = {
            resolved
            for resolved in (
                _resolve_import_token_to_module(token, repo_root=repo_root)
                for token in _extract_import_tokens(source)
            )
            if resolved
        }
        imports_by_file[rel] = imports
        module_by_file.setdefault(rel, set()).add(infer_module_from_path(rel))
    return {"imports_by_file": imports_by_file, "module_by_file": module_by_file}


def _resolve_file_imports(rel: str, *, repo_root: Path, import_graph: Dict[str, Dict[str, set[str]]]) -> set[str]:
    normalized = str(rel or "").replace("\\", "/").strip("/")
    cached = import_graph.get("imports_by_file", {}).get(normalized)
    if cached is not None:
        return set(cached)
    source = _safe_read_text(repo_root / normalized)
    return {
        resolved
        for resolved in (
            _resolve_import_token_to_module(token, repo_root=repo_root)
            for token in _extract_import_tokens(source)
        )
        if resolved
    }


def _collect_module_dependency_summary(
    module_path: str,
    module_files: List[str],
    *,
    repo_root: Path,
    import_graph: Optional[Dict[str, Dict[str, set[str]]]] = None,
) -> Dict[str, List[str]]:
    normalized_module = str(module_path or "").replace("\\", "/").strip("/")
    python_files = [fp for fp in module_files if str(fp).endswith(".py")]
    outbound_groups: Dict[str, set[str]] = {}
    inbound_groups: Dict[str, set[str]] = {}
    graph = import_graph or _build_repo_import_graph(repo_root)

    for rel in python_files:
        for resolved in _resolve_file_imports(rel, repo_root=repo_root, import_graph=graph):
            if not resolved or resolved == normalized_module or resolved.startswith(f"{normalized_module}/"):
                continue
            group = _dependency_group(resolved)
            if not group:
                continue
            outbound_groups.setdefault(group, set()).add(resolved)

    module_file_set = {str(fp).replace("\\", "/").strip("/") for fp in python_files}

    for rel, imports in sorted(graph.get("imports_by_file", {}).items()):
        if rel in module_file_set:
            continue
        if not imports:
            continue
        if any(
            imported == normalized_module
            or imported.startswith(f"{normalized_module}/")
            or imported in module_file_set
            for imported in imports
        ):
            importer_modules = graph.get("module_by_file", {}).get(rel) or {infer_module_from_path(rel)}
            importer_module = sorted(importer_modules)[0]
            group = _dependency_group(importer_module)
            if not group:
                continue
            inbound_groups.setdefault(group, set()).add(importer_module)

    return {
        "outbound": _format_dependency_group_rows(outbound_groups),
        "inbound": _format_dependency_group_rows(inbound_groups),
    }


def collect_all_indexed_modules(index_path: Optional[Path] = None, *, prefer_fresh_source: bool = False) -> List[str]:
    """Collect normalized module paths from readonly index records.

    Behavior:
      - Aggregates module candidates from indexed files that still contain items.
      - Supports `prefer_fresh_source=True` so generated-context and stale
        workflows can derive modules from the same source-derived readonly
        index used in clean CI.
      - Keeps module discovery read-only and does not mutate runtime cache or
        workspace files.

    Args:
      index_path (Optional[Path]): Optional explicit readonly index path.
      prefer_fresh_source (bool): Prefer transient source-derived records over
        runtime cache snapshots when possible.

    Returns:
      List[str]: Sorted unique repo-relative module paths with indexed records.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    gen = L2Generator(index_path=index_path, prefer_fresh_source=prefer_fresh_source)
    return gen.collect_all_indexed_modules()


class L2Generator:
    def __init__(
        self,
        index_path: Optional[Path] = None,
        meta_path: Optional[Path] = None,
        *,
        prefer_fresh_source: bool = False,
    ) -> None:
        """Initialize the L2 generator against a readonly index source.

        Behavior:
          - Resolves canonical workspace paths for L2 README generation.
          - Uses `prefer_fresh_source=True` to prefer transient source-derived
            readonly index data over runtime cache snapshots.
          - This option controls the same generated-context source-of-truth used
            by L2 writes and stale validation paths.
          - Keeps generation read-only until `write()` is called.

        Args:
          index_path (Optional[Path]): Optional explicit readonly index path.
          meta_path (Optional[Path]): Optional L2 meta file path override.
          prefer_fresh_source (bool): Prefer transient source-derived index
            data over runtime cache snapshots when possible.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        self.repo_root = Path.cwd().resolve()
        workspace_paths = load_workspace_paths(self.repo_root, enforce_write_safety=True)
        self.l2_view_root = workspace_paths.l2_view_root.resolve()
        self._ensure_within_root(
            self.l2_view_root,
            root=self.repo_root,
            field_name="l2.canonical_root",
            raw_value=self.l2_view_root.as_posix(),
        )
        self.index_path = index_path or (Path(".harbor") / "cache" / "l3_index.json")
        self.prefer_fresh_source = prefer_fresh_source
        self.meta_path = self._resolve_meta_path(meta_path)
        self.legacy_meta_path = (self.repo_root / ".harbor" / "l2_meta.json").resolve()
        loaded = load_workspace_config(self.repo_root)
        cfg = loaded.get("config") or {}
        export_options = parse_workspace_export_options(cfg)
        module_readme_options = ((export_options.get("l2", {}) or {}).get("module_readme", {}) or {})
        self.export_module_readme_enabled = bool(module_readme_options.get("enabled", True))
        self.scanner = DDTScanner()
        # validator uses default paths unless overridden
        self.validator = DDTValidator()
        self._repo_import_graph: Optional[Dict[str, Dict[str, set[str]]]] = None

    def generate(self, module_path: str) -> str:
        """生成指定模块的 L2 README Markdown 文本。

        功能:
          - 从索引缓存聚合该模块下的 L3 函数（public/internal）。
          - 调用 DDT 校验，生成每个函数的绑定状态。
          - 按稳定多键顺序排序并渲染为 Markdown 文本。
          - 当多个符号短名相同时，跨平台保持一致的 README 行顺序。
          - 使用实例级 repo import graph 缓存生成静态依赖摘要，避免
            docs/verify 全量流程为每个模块重复扫描整个仓库。
          - 依赖摘要只展示可定位的 repo 内子域边，不展示 `import harbor`
            这类低信息量根包边。

        使用场景:
          - CLI `harbor gen l2`。

        依赖:
          - .harbor/cache/l3_index.json
          - DDTScanner/Validator

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Args:
          module_path (str): 要生成视图的模块路径前缀。

        Returns:
          str: 渲染的 Markdown 文本。
        """
        idx = self._load_index(self.index_path)
        items: List[Dict[str, Any]] = []
        module_files: List[str] = []
        cwd = Path.cwd().resolve()
        module_norm = module_path.replace("\\", "/")
        for fp, meta in idx.get("files", {}).items():
            rel = fp
            try:
                rel = Path(fp).resolve().relative_to(cwd).as_posix()
            except Exception:
                rel = Path(fp).as_posix()
            if f"{module_norm}/" not in rel.replace("\\", "/"):
                continue
            module_files.append(rel.replace("\\", "/"))
            for it in meta.get("items", []):
                it2 = dict(it)
                it2["_file_path"] = fp
                it2["_rel_file_path"] = rel.replace("\\", "/")
                items.append(it2)
        bindings = self.scanner.scan_tests()
        rep = self.validator.validate(bindings)
        bind_ok = {b.func_id for b in rep.valid}
        bind_bad = {}
        for typ, b, msg in rep.violations:
            bind_bad.setdefault(b.func_id, []).append((typ, msg))

        def item_sort_key(it: Dict[str, Any]) -> Tuple[str, str, str, int, str]:
            qualified = str(it.get("qualified_name") or it.get("id") or "")
            short_name = qualified.split(".")[-1] if qualified else str(it.get("name") or "")
            file_path = _to_repo_relative(str(it.get("_file_path") or ""), cwd) or str(it.get("_file_path") or "").replace(
                "\\",
                "/",
            )
            try:
                lineno = int(it.get("lineno") or 0)
            except Exception:
                lineno = 0
            return (short_name, qualified, file_path, lineno, str(it.get("id") or ""))

        def ddt_status(it: Dict[str, Any]) -> str:
            fid = it["id"]
            strictness = it.get("strictness", "standard") or "standard"
            if fid in bind_ok:
                return "✅ Valid"
            if fid in bind_bad:
                return "⚠️ " + "; ".join([t for t, _ in bind_bad[fid]])
            if strictness == "strict":
                return "❌ Missing"
            return "⚪ Missing"

        def summary_for(it: Dict[str, Any]) -> str:
            try:
                src = Path(it["_file_path"]).read_text(encoding="utf-8")
                node = find_function_node(src, it.get("lineno", 0), it.get("name", ""))
                doc = ast.get_docstring(node) if node else None
            except Exception:
                doc = None
            if not doc:
                return "—"
            first = doc.strip().split("\n", 1)[0].strip()
            return (first[:57] + "...") if len(first) > 60 else first

        items_sorted = sorted(items, key=item_sort_key)

        def file_path_for(it: Dict[str, Any]) -> str:
            return str(it.get("_rel_file_path") or _to_repo_relative(str(it.get("_file_path") or ""), cwd) or "").replace("\\", "/")

        def behavior_risk_score(it: Dict[str, Any]) -> Tuple[int, str, str]:
            fn = str(it.get("qualified_name") or it.get("id") or "")
            scope = str(it.get("scope") or "internal")
            strictness = _display_strictness(it.get("strictness"), default="standard")
            file_rel = file_path_for(it)
            score = 0
            reasons: List[str] = []
            lowered = f"{fn} {file_rel}".lower()
            for keyword, weight, reason in (
                ("write", 36, "file write"),
                ("export", 24, "export/output path"),
                ("json", 34, "JSON output"),
                ("to_dict", 38, "JSON serialization"),
                ("report_to_dict", 38, "report serialization"),
                ("cli", 34, "CLI behavior"),
                ("main", 18, "entrypoint"),
                ("doctor", 22, "doctor workflow"),
                ("stale", 24, "stale workflow"),
                ("verify", 28, "generated verification"),
                ("generated", 24, "generated context"),
                ("workspace", 36, "workspace path"),
                ("path", 16, "path normalization"),
                ("safety", 26, "safety boundary"),
                ("baseline", 28, "baseline state"),
                ("diary", 28, "diary persistence"),
                ("log", 18, "log/change window"),
                ("change_window", 24, "change-window state"),
            ):
                if keyword in lowered:
                    score += weight
                    reasons.append(reason)
            if strictness == "strict":
                score += 18
                reasons.append("strict target")
            if scope == "public":
                score += 14
                reasons.append("public surface")
            focus = reasons[0] if reasons else "behavioral hotspot"
            return score, focus, ", ".join(reasons[:3]) or "indexed target"

        def coverage_gap_score(it: Dict[str, Any]) -> Tuple[int, str]:
            status = ddt_status(it)
            scope = str(it.get("scope") or "internal")
            strictness = _display_strictness(it.get("strictness"), default="standard")
            score = 0
            reasons: List[str] = []
            if status.startswith("❌"):
                score += 60
                reasons.append("Missing DDT")
            elif status.startswith("⚠️"):
                score += 42
                reasons.append("DDT violation")
            if strictness == "strict":
                score += 25
                reasons.append("strict target")
            if scope == "public":
                score += 18
                reasons.append("public surface")
            return score, ", ".join(reasons[:3]) or "coverage review needed"

        summary_rows = {
            "Public by contract": sum(1 for it in items_sorted if (it.get("scope") or "internal") == "public"),
            "Strict targets": sum(1 for it in items_sorted if str(it.get("strictness") or "standard") == "strict"),
            "Private-named but strict": sum(
                1 for it in items_sorted if (it.get("scope") or "internal") != "public" and str(it.get("strictness") or "standard") == "strict"
            ),
            "Internal indexed": sum(1 for it in items_sorted if (it.get("scope") or "internal") != "public"),
            "Strict targets missing DDT": sum(
                1 for it in items_sorted if str(it.get("strictness") or "standard") == "strict" and ddt_status(it).startswith("❌")
            ),
            "Targets with DDT warnings": sum(1 for it in items_sorted if ddt_status(it).startswith("⚠️")),
        }
        ranked_behavior_targets = sorted(
            [
                {
                    "item": it,
                    "score": behavior_risk_score(it)[0],
                    "focus": behavior_risk_score(it)[1],
                    "reason": behavior_risk_score(it)[2],
                }
                for it in items_sorted
                if behavior_risk_score(it)[0] > 0
            ],
            key=lambda row: (-row["score"], item_sort_key(row["item"])),
        )
        top_behavior_targets = ranked_behavior_targets[:12]
        ranked_coverage_gaps = sorted(
            [
                {
                    "item": it,
                    "score": coverage_gap_score(it)[0],
                    "reason": coverage_gap_score(it)[1],
                }
                for it in items_sorted
                if coverage_gap_score(it)[0] > 0
            ],
            key=lambda row: (-row["score"], item_sort_key(row["item"])),
        )
        top_coverage_gaps = ranked_coverage_gaps[:10]
        dependencies = _collect_module_dependency_summary(
            module_norm,
            sorted(set(module_files)),
            repo_root=cwd,
            import_graph=self._get_repo_import_graph(),
        )

        lines: List[str] = []
        lines.append(f"# Module: {module_path}")
        lines.append("")
        lines.append("## Public API Summary")
        lines.append("| Metric | Count |")
        lines.append("|---|---:|")
        for label, count in summary_rows.items():
            lines.append(f"| {label} | {count} |")
        lines.append("")
        lines.append("## High-Risk Targets")
        if top_behavior_targets:
            lines.append("| Function | File | Risk Focus | Scope | Strictness | Why |")
            lines.append("|---|---|---|---|---|---|")
            for row in top_behavior_targets:
                it = row["item"]
                lines.append(
                    f"| {it.get('qualified_name', it.get('id', ''))} | {file_path_for(it)} | {row['focus']} | {it.get('scope', 'internal')} | {_display_strictness(it.get('strictness'))} | {row['reason']} |"
                )
        else:
            lines.append("```text")
            lines.append("No behavior-oriented hotspots detected from indexed contracts.")
            lines.append("```")
        lines.append("")
        lines.append("### Contract / DDT Coverage Gaps")
        if top_coverage_gaps:
            lines.append("| Function | File | Scope | Strictness | DDT Status | Why |")
            lines.append("|---|---|---|---|---|---|")
            for row in top_coverage_gaps:
                it = row["item"]
                lines.append(
                    f"| {it.get('qualified_name', it.get('id', ''))} | {file_path_for(it)} | {it.get('scope', 'internal')} | {_display_strictness(it.get('strictness'))} | {ddt_status(it)} | {row['reason']} |"
                )
        else:
            lines.append("```text")
            lines.append("No contract or DDT coverage gaps detected from indexed contracts.")
            lines.append("```")
        lines.append("")
        lines.append("## Dependency Summary")
        lines.append("")
        lines.append("**Outbound Dependencies**")
        if dependencies["outbound"]:
            for dep in dependencies["outbound"]:
                lines.append(f"- {dep}")
        else:
            lines.append("- None detected from repo-local Python imports.")
        lines.append("")
        lines.append("**Inbound Dependents**")
        if dependencies["inbound"]:
            for dep in dependencies["inbound"]:
                lines.append(f"- {dep}")
        else:
            lines.append("- None detected from repo-local Python imports.")
        lines.append("")
        lines.append("## Full Indexed Contracts")
        if items_sorted:
            lines.append("<details>")
            lines.append("<summary>All indexed contracts</summary>")
            lines.append("")
            lines.append("| Function | File | Scope | Strictness | DDT Status | Summary |")
            lines.append("|---|---|---|---|---|---|")
            for it in items_sorted:
                lines.append(
                    f"| {it.get('qualified_name', it.get('id', ''))} | {file_path_for(it)} | {it.get('scope', 'internal')} | {_display_strictness(it.get('strictness'))} | {ddt_status(it)} | {summary_for(it)} |"
                )
            lines.append("")
            lines.append("</details>")
        else:
            lines.append("```text")
            lines.append("No indexed contracts found for this module.")
            lines.append("```")
        md = "\n".join(lines)
        return md

    def write(self, module_path: str, md: str, force: bool = False) -> Optional[List[Path]]:
        """Write the canonical L2 README and synchronized metadata for one module.

        Behavior:
          - Resolves the canonical L2 README under `.harbor/views/l2/**` and
            the optional module README export under `<module>/README.md`.
          - Rebuilds frontmatter integrity metadata from the current readonly
            index inputs before deciding whether a rewrite is required.
          - Treats frontmatter/integrity drift as a required refresh even when
            the rendered body hash in `_meta.json` is unchanged.
          - Keeps canonical README rewrites and `_meta.json` updates aligned for
            the same module write operation.
          - Preserves the current public behavior: returns `None` only when the
            canonical view, optional export, and meta hash are already aligned.

        Args:
          module_path (str): Repo-relative module path such as `harbor/core`.
          md (str): Rendered L2 README body without canonical frontmatter.
          force (bool): When `True`, rewrites generated outputs even if the
            current canonical/exported views already match.

        Returns:
          Optional[List[Path]]: Written canonical/export paths, or `None` when
          no refresh is required.

        File Write Targets:
          - `.harbor/views/l2/<module>/README.md`
          - `.harbor/views/l2/_meta.json`
          - Optional `<module>/README.md` export when enabled

        Side Effects:
          - Creates parent directories for generated L2 views when needed.
          - Overwrites generated L2 views and canonical meta entries for the
            target module.

        Idempotency:
          - Deterministic for the same module body, readonly index inputs, and
            workspace configuration.

        Security:
          - Rejects module paths that escape the repository root.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        module_norm = self._safe_module_subpath(module_path)
        if not module_norm:
            raise ValueError("Invalid module path: module path cannot be empty.")

        raw_canonical_meta = self._read_meta_file(self.meta_path)
        meta = self._load_meta()
        current_hash = self.compute_meta_hash(md)
        prev_hash = meta.get(module_norm)
        canonical_readme = self._resolve_canonical_readme_path(module_norm)
        source_paths, contract_records = self._collect_integrity_inputs(module_norm)
        metadata = build_context_integrity_metadata(
            view_type="l2_readme",
            module=module_norm,
            generation_command=f"harbor docs --module {module_norm} --write",
            source_paths=source_paths,
            contract_records=contract_records,
            repo_root=self.repo_root,
        )
        previous = ""
        if canonical_readme.exists():
            try:
                previous = canonical_readme.read_text(encoding="utf-8")
            except Exception:
                previous = ""
        canonical_markdown = compose_markdown_with_frontmatter(previous, metadata, md)

        export_readme: Optional[Path] = None
        export_current = ""
        export_matches = True
        if self.export_module_readme_enabled:
            export_readme = self._resolve_export_readme_path(module_norm)
            if export_readme.resolve() != canonical_readme.resolve():
                if export_readme.exists():
                    try:
                        export_current = export_readme.read_text(encoding="utf-8")
                    except Exception:
                        export_current = ""
                export_matches = export_current == md

        canonical_matches = (
            canonical_readme.exists()
            and content_without_generated_at_for_compare(previous)
            == content_without_generated_at_for_compare(canonical_markdown)
        )
        meta_after_write = dict(meta)
        meta_after_write[module_norm] = current_hash
        meta_after_write = self._sanitize_meta_entries(meta_after_write)
        meta_needs_write = (not self.meta_path.exists()) or (raw_canonical_meta != meta_after_write)
        if prev_hash == current_hash and not force and canonical_matches and export_matches and not meta_needs_write:
            return None

        written_paths: List[Path] = []
        canonical_readme.parent.mkdir(parents=True, exist_ok=True)
        canonical_readme.write_text(canonical_markdown, encoding="utf-8")
        written_paths.append(canonical_readme)

        if self.export_module_readme_enabled:
            assert export_readme is not None
            if export_readme.resolve() != canonical_readme.resolve():
                export_readme.parent.mkdir(parents=True, exist_ok=True)
                export_readme.write_text(md, encoding="utf-8")
                written_paths.append(export_readme)

        self._save_meta(self.meta_path, meta_after_write)
        return written_paths

    def compute_meta_hash(self, md: str) -> str:
        """Hash L2 body content using the canonical `_meta.json` normalization.

        Behavior:
          - Normalizes line endings to `\n`.
          - Ignores trailing newline-only differences so the stored meta hash
            matches both generated bodies and canonical README bodies extracted
            from frontmatter-wrapped files.

        Args:
          md (str): L2 README body content before or after canonical wrapping.

        Returns:
          str: Stable SHA-256 hex digest for `_meta.json`.

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: deterministic
        """
        normalized = str(md or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def canonical_readme_path(self, module_path: str) -> Path:
        return self._resolve_canonical_readme_path(module_path)

    def collect_all_indexed_modules(self) -> List[str]:
        idx = self._load_index(self.index_path)
        modules: List[str] = []
        for fp, meta in idx.get("files", {}).items():
            if not meta.get("items"):
                continue
            module = normalize_indexed_module_candidate(str(fp), repo_root=self.repo_root)
            if module:
                modules.append(module)
        return sorted(set(modules))

    def _load_index(self, path: Path) -> Dict[str, Any]:
        return load_readonly_index(
            index_path=path,
            repo_root=self.repo_root,
            prefer_fresh_source=self.prefer_fresh_source,
        )

    def _get_repo_import_graph(self) -> Dict[str, Dict[str, set[str]]]:
        if self._repo_import_graph is None:
            self._repo_import_graph = _build_repo_import_graph(self.repo_root)
        return self._repo_import_graph

    def _load_meta(self, path: Optional[Path] = None) -> Dict[str, Any]:
        if path is not None:
            return self._sanitize_meta_entries(self._read_meta_file(path))
        meta = self._sanitize_meta_entries(self._read_meta_file(self.meta_path))
        if meta:
            return meta
        return self._sanitize_meta_entries(self._read_meta_file(self.legacy_meta_path))

    def _read_meta_file(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_meta(self, path: Path, meta: Dict[str, Any]) -> None:
        cleaned = self._sanitize_meta_entries(meta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")

    def _sanitize_meta_entries(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        for raw_key, value in (meta or {}).items():
            normalized = self._normalize_meta_key(str(raw_key or ""))
            if not normalized:
                continue
            cleaned[normalized] = value
        return {key: cleaned[key] for key in sorted(cleaned)}

    def _normalize_meta_key(self, raw_key: str) -> str:
        text = str(raw_key or "").strip()
        if not text:
            return ""

        normalized = text.replace("\\", "/")
        if looks_like_absolute_path(normalized):
            rel = _repo_relative_index_path(normalized, repo_root=self.repo_root)
            if rel is None:
                return ""
            return normalize_indexed_module_candidate(rel, repo_root=self.repo_root)

        candidate = normalize_indexed_module_candidate(normalized, repo_root=self.repo_root)
        if not candidate:
            return ""
        if candidate.startswith("../") or candidate.startswith("/"):
            return ""
        return candidate

    def _resolve_meta_path(self, meta_path: Optional[Path]) -> Path:
        if meta_path is None:
            return (self.l2_view_root / "_meta.json").resolve()
        candidate = Path(meta_path)
        if not candidate.is_absolute():
            candidate = self.repo_root / candidate
        resolved = candidate.resolve()
        self._ensure_within_root(
            resolved,
            root=self.repo_root,
            field_name="l2.meta_path",
            raw_value=str(meta_path),
        )
        return resolved

    def _resolve_canonical_readme_path(self, module_path: str) -> Path:
        safe_module = self._safe_module_subpath(module_path)
        target = (self.l2_view_root / safe_module / "README.md").resolve()
        self._ensure_within_root(
            target,
            root=self.l2_view_root,
            field_name="l2.canonical_root",
            raw_value=module_path,
        )
        self._ensure_within_root(
            target,
            root=self.repo_root,
            field_name="module",
            raw_value=module_path,
        )
        return target

    def _resolve_export_readme_path(self, module_path: str) -> Path:
        safe_module = self._safe_module_subpath(module_path)
        target = (self.repo_root / safe_module / "README.md").resolve()
        self._ensure_within_root(
            target,
            root=self.repo_root,
            field_name="module",
            raw_value=module_path,
        )
        return target

    def _collect_integrity_inputs(self, module_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        idx = self._load_index(self.index_path)
        source_paths: List[str] = []
        contract_records: List[Dict[str, Any]] = []
        mod = str(module_path or "").replace("\\", "/").strip("/")
        prefix = f"{mod}/" if mod else ""
        for fp, meta in (idx.get("files") or {}).items():
            rel = _to_repo_relative(str(fp), self.repo_root)
            if not rel:
                continue
            if mod and rel != mod and not rel.startswith(prefix):
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
        return sorted(set(source_paths)), contract_records

    def _safe_module_subpath(self, module_path: str) -> str:
        normalized = str(module_path or "").strip().replace("\\", "/")
        while "//" in normalized:
            normalized = normalized.replace("//", "/")
        if normalized.startswith("/") or _looks_like_windows_absolute_path(normalized):
            raise ValueError(
                f"Invalid module path: '{module_path}'. Resolved path '{normalized}' escapes repo root '{self.repo_root.as_posix()}'."
            )
        normalized = normalized.strip("/")
        if not normalized:
            return ""
        parts = [part for part in normalized.split("/") if part not in ("", ".")]
        if any(part == ".." for part in parts):
            raise ValueError(f"Invalid module path: '{module_path}'. Relative parent segments are not allowed.")
        return "/".join(parts)

    def _ensure_within_root(self, path: Path, *, root: Path, field_name: str, raw_value: str) -> None:
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(
                f"Invalid workspace path for '{field_name}': '{raw_value}'. "
                f"Resolved path '{path.resolve().as_posix()}' escapes repo root '{root.resolve().as_posix()}'."
            ) from exc


def _to_repo_relative(path_text: str, repo_root: Path) -> str:
    return repo_relative_path(path_text, repo_root=repo_root) or ""
