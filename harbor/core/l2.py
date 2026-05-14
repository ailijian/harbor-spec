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

    def generate(self, module_path: str) -> str:
        """生成指定模块的 L2 README Markdown 文本。

        功能:
          - 从索引缓存聚合该模块下的 L3 函数（public/internal）。
          - 调用 DDT 校验，生成每个函数的绑定状态。
          - 按稳定多键顺序排序并渲染为 Markdown 文本。
          - 当多个符号短名相同时，跨平台保持一致的 README 行顺序。

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
            for it in meta.get("items", []):
                it2 = dict(it)
                it2["_file_path"] = fp
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

        pub = [it for it in items if (it.get("scope") or "internal") == "public"]
        internal = [it for it in items if (it.get("scope") or "internal") != "public"]
        pub_sorted = sorted(pub, key=item_sort_key)
        int_sorted = sorted(internal, key=item_sort_key)

        lines: List[str] = []
        lines.append(f"# Module: {module_path}")
        lines.append("")
        lines.append("## Public API")
        lines.append("| Function | Summary | Strictness | DDT Status |")
        lines.append("|---|---|---|---|")
        for it in pub_sorted:
            fn = it.get("qualified_name", it["id"])
            sm = summary_for(it)
            st = it.get("strictness", "standard") or "standard"
            ds = ddt_status(it)
            lines.append(f"| {fn} | {sm} | {st} | {ds} |")
        lines.append("")
        if int_sorted:
            lines.append("## Internal Details (optional)")
            lines.append("<details>")
            lines.append("<summary>Internal functions</summary>")
            lines.append("")
            lines.append("| Function | Summary | Strictness | DDT Status |")
            lines.append("|---|---|---|---|")
            for it in int_sorted:
                fn = it.get("qualified_name", it["id"])
                sm = summary_for(it)
                st = it.get("strictness", "standard") or "standard"
                ds = ddt_status(it)
                lines.append(f"| {fn} | {sm} | {st} | {ds} |")
            lines.append("")
            lines.append("</details>")
        lines.append("")
        lines.append("## Dependency (MVP)")
        lines.append("- (TBD) 未来基于 import 简要分析模块依赖。")
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
        if prev_hash == current_hash and not force and canonical_matches and export_matches:
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

        meta[module_norm] = current_hash
        self._save_meta(self.meta_path, meta)
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

    def _load_meta(self, path: Optional[Path] = None) -> Dict[str, Any]:
        if path is not None:
            return self._read_meta_file(path)
        meta = self._read_meta_file(self.meta_path)
        if meta:
            return meta
        return self._read_meta_file(self.legacy_meta_path)

    def _read_meta_file(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_meta(self, path: Path, meta: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

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
