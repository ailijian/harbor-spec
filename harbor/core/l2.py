from __future__ import annotations

import ast
import json
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from harbor.core.context_integrity import build_context_integrity_metadata, compose_markdown_with_frontmatter
from harbor.core.ddt import DDTScanner, DDTValidator
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
    candidate = Path(normalized)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
        except Exception:
            return None

    if _looks_like_windows_absolute_path(normalized):
        marker = f"/{repo_root.name.lower()}/"
        lower = normalized.lower()
        idx = lower.find(marker)
        if idx == -1:
            return None
        return normalized[idx + len(marker) :].strip("/")

    return None


def normalize_indexed_module_candidate(path: str | Path, *, repo_root: Optional[Path] = None) -> str:
    """将索引记录路径归一化为模块候选，优先映射 repo 内绝对路径。"""
    root = (repo_root or Path.cwd()).resolve()
    rel = _repo_relative_index_path(path, repo_root=root)
    if rel is not None:
        return infer_module_from_path(rel)
    return infer_module_from_path(path)


def collect_all_indexed_modules(index_path: Optional[Path] = None) -> List[str]:
    gen = L2Generator(index_path=index_path)
    return gen.collect_all_indexed_modules()


class L2Generator:
    def __init__(self, index_path: Optional[Path] = None, meta_path: Optional[Path] = None) -> None:
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
          - 稳定排序并渲染为 Markdown 文本。

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

        def name_key(it: Dict[str, Any]) -> str:
            return it.get("qualified_name", it["id"]).split(".")[-1]

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
        pub_sorted = sorted(pub, key=name_key)
        int_sorted = sorted(internal, key=name_key)

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
        module_norm = self._safe_module_subpath(module_path)
        if not module_norm:
            raise ValueError("Invalid module path: module path cannot be empty.")

        meta = self._load_meta()
        current_hash = self.compute_meta_hash(md)
        prev_hash = meta.get(module_norm)
        if prev_hash == current_hash and not force:
            return None

        written_paths: List[Path] = []
        canonical_readme = self._resolve_canonical_readme_path(module_norm)
        canonical_readme.parent.mkdir(parents=True, exist_ok=True)
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
        canonical_readme.write_text(canonical_markdown, encoding="utf-8")
        written_paths.append(canonical_readme)

        if self.export_module_readme_enabled:
            export_readme = self._resolve_export_readme_path(module_norm)
            if export_readme.resolve() != canonical_readme.resolve():
                export_readme.parent.mkdir(parents=True, exist_ok=True)
                export_readme.write_text(md, encoding="utf-8")
                written_paths.append(export_readme)

        meta[module_norm] = current_hash
        self._save_meta(self.meta_path, meta)
        return written_paths

    def compute_meta_hash(self, md: str) -> str:
        return hashlib.sha256(md.encode("utf-8")).hexdigest()

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
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        from harbor.core.storage import HarborDB
        db = HarborDB()
        files: Dict[str, Any] = {}
        for fp, mtime in db.get_all_files():
            items = []
            for it in db.get_file_entries(fp):
                items.append(
                    {
                        "id": it.get("id"),
                        "qualified_name": it.get("meta", {}).get("qualified_name"),
                        "name": it.get("meta", {}).get("name"),
                        "signature_hash": it.get("signature_hash"),
                        "body_hash": it.get("body_hash"),
                        "contract_hash": it.get("contract_hash"),
                        "docstring_raw_hash": it.get("meta", {}).get("docstring_raw_hash"),
                        "scope": it.get("meta", {}).get("scope"),
                        "strictness": it.get("meta", {}).get("strictness"),
                        "lineno": it.get("meta", {}).get("lineno"),
                    }
                )
            files[fp] = {"mtime": mtime, "file_hash": "", "items": items}
        return {"meta": {"schema_version": "1.0.2"}, "files": files}

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
    raw = str(path_text or "").strip().replace("\\", "/")
    if not raw:
        return ""
    if _looks_like_windows_absolute_path(raw):
        marker = f"/{repo_root.name.lower()}/"
        lower = raw.lower()
        idx = lower.find(marker)
        if idx == -1:
            return ""
        return raw[idx + len(marker) :].strip("/")
    path_obj = Path(raw)
    if path_obj.is_absolute():
        try:
            return path_obj.resolve().relative_to(repo_root.resolve()).as_posix()
        except Exception:
            return ""
    return raw.strip("/")
