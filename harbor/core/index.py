from __future__ import annotations

import ast
import io
import json
import time
import hashlib
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from harbor.adapters.python.parser import PythonAdapter, FunctionContract


@dataclass
class IndexReport:
    scanned_files: int
    updated_files: int
    skipped_files: int
    total_items: int
    cache_path: str
    elapsed_ms: int


class IndexBuilder:
    def __init__(
        self,
        code_roots: Optional[List[str]] = None,
        cache_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        self.config_path = config_path or Path(".harbor/config.yaml")
        if code_roots is None or cache_dir is None:
            cfg = self._load_config(self.config_path)
            code_roots = code_roots or cfg.get("code_roots", ["harbor/**"])
            cache_base = Path(".harbor") / "cache"
            cache_dir = cache_dir or cache_base
        self.code_roots = code_roots
        self.cache_dir = cache_dir
        self.cache_file = self.cache_dir / "l3_index.json"
        self.adapter = PythonAdapter()

    def build(self, incremental: bool = True) -> IndexReport:
        """构建或增量更新 L3 索引到缓存。

        功能:
          - 扫描配置的代码根目录，解析 Python 文件中的 L3 契约元数据。
          - 计算每个函数/方法的 `signature_hash` 与 `body_hash`，生成索引条目。
          - 在增量模式下，复用未变更文件的旧条目，避免重复解析。
          - 将结果写入 `.harbor/cache/l3_index.json`。

        使用场景:
          - `harbor build-index` 命令。
          - `harbor status` 自动触发的增量索引。

        依赖:
          - harbor.adapters.python.PythonAdapter
          - .harbor/config.yaml 中的 code_roots

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          incremental (bool): 是否启用增量构建，默认为 True。

        Returns:
          IndexReport: 构建统计与缓存位置。

        Raises:
          IOError: 当缓存目录不可写或索引文件写入失败。
          ConfigError: 当配置文件加载失败或内容不合法。
        """
        t0 = time.time()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        old = self._load_cache()
        scanned = 0
        updated = 0
        skipped = 0
        files_index: Dict[str, Any] = old.get("files", {})
        for p in self._iter_py_files():
            scanned += 1
            fp = str(p.as_posix())
            mtime = p.stat().st_mtime
            fhash = self._file_hash(p)
            prev = files_index.get(fp)
            if incremental and prev and prev.get("mtime") == mtime and prev.get("file_hash") == fhash:
                skipped += 1
                continue
            source = p.read_text(encoding="utf-8")
            items: List[Dict[str, Any]] = []
            for fc in self.adapter.parse_file(fp):
                node = self._find_function_node(source, fc.lineno, fc.name)
                body_hash = self._compute_body_hash(source, node) if node else ""
                items.append(self._index_entry(fc, body_hash))
            files_index[fp] = {
                "mtime": mtime,
                "file_hash": fhash,
                "items": items,
            }
            updated += 1
        payload = {
            "meta": {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "schema_version": "1.0.2",
            },
            "files": files_index,
        }
        self._save_cache(payload)
        elapsed_ms = int((time.time() - t0) * 1000)
        total_items = sum(len(v.get("items", [])) for v in files_index.values())
        return IndexReport(
            scanned_files=scanned,
            updated_files=updated,
            skipped_files=skipped,
            total_items=total_items,
            cache_path=str(self.cache_file.as_posix()),
            elapsed_ms=elapsed_ms,
        )

    def _iter_py_files(self) -> List[Path]:
        roots = []
        for pattern in self.code_roots:
            base = Path.cwd()
            if "**" in pattern or "*" in pattern:
                for p in base.glob(pattern):
                    if p.is_file() and p.suffix == ".py":
                        roots.append(p)
                    elif p.is_dir():
                        roots.extend([x for x in p.rglob("*.py")])
            else:
                p = base / pattern
                if p.is_dir():
                    roots.extend([x for x in p.rglob("*.py")])
                elif p.is_file() and p.suffix == ".py":
                    roots.append(p)
        seen = {}
        dedup = []
        for p in roots:
            k = p.resolve().as_posix()
            if k in seen:
                continue
            seen[k] = True
            dedup.append(p)
        return dedup

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"code_roots": ["harbor/**"]}
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            raise RuntimeError("ConfigError: failed to load .harbor/config.yaml")

    def _load_cache(self) -> Dict[str, Any]:
        if not self.cache_file.exists():
            return {"files": {}}
        try:
            return json.loads(self.cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {"files": {}}

    def _save_cache(self, payload: Dict[str, Any]) -> None:
        try:
            self.cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            raise IOError("failed to write index cache")

    def _file_hash(self, p: Path) -> str:
        data = p.read_bytes()
        return hashlib.sha256(data).hexdigest()

    def _index_entry(self, fc: FunctionContract, body_hash: str) -> Dict[str, Any]:
        return {
            "id": fc.id,
            "qualified_name": fc.qualified_name,
            "name": fc.name,
            "signature_hash": fc.signature_hash,
            "body_hash": body_hash,
            "contract_hash": fc.contract_hash,
            "docstring_raw_hash": fc.docstring_raw_hash,
            "scope": fc.scope,
            "strictness": fc.strictness,
            "lineno": fc.lineno,
        }

    def _find_function_node(self, source: str, lineno: int, name: str) -> Optional[ast.AST]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and getattr(node, "name", None) == name:
                if getattr(node, "lineno", 0) == lineno:
                    return node
        return None

    def _compute_body_hash(self, source: str, fn_node: ast.AST) -> str:
        lines = source.splitlines(keepends=True)
        body = ""
        if hasattr(fn_node, "body"):
            stmts = list(getattr(fn_node, "body"))
            if stmts and isinstance(stmts[0], ast.Expr) and isinstance(getattr(stmts[0], "value", None), ast.Constant) and isinstance(stmts[0].value.value, str):
                stmts = stmts[1:]
            chunks: List[str] = []
            for s in stmts:
                start = getattr(s, "lineno", None)
                end = getattr(s, "end_lineno", None)
                if start is None or end is None:
                    continue
                seg = "".join(lines[start - 1 : end])
                chunks.append(seg)
            body = "".join(chunks)
        if not body:
            return hashlib.sha256(b"").hexdigest()
        tokens = tokenize.generate_tokens(io.StringIO(body).readline)
        parts: List[str] = []
        for tok in tokens:
            if tok.type in (
                tokenize.COMMENT,
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.ENCODING,
            ):
                continue
            val = tok.string.strip()
            if not val:
                continue
            parts.append(val)
        normalized = " ".join(parts)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

