from __future__ import annotations

import os
import ast
import io
import json
import time
import hashlib
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Iterator, Literal

import yaml

from harbor.adapters.python.parser import PythonAdapter, FunctionContract
from harbor.core.utils import compute_body_hash, find_function_node, iter_project_files
from harbor.core.git_utils import GitIgnoreMatcher


@dataclass
class IndexReport:
    scanned_files: int
    updated_files: int
    skipped_files: int
    total_items: int
    cache_path: str
    elapsed_ms: int

@dataclass
class ProgressEvent:
    """单文件进度事件。

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only

    Args:
      path (str): 当前处理的文件路径（posix 相对路径）。
      index (int): 当前文件在总列表中的序号（从 1 开始）。
      total (int): 待处理的文件总数。
      cached (bool): 是否命中增量缓存（跳过解析）。
      status (Literal): 处理状态：scanning | parsed | skipped | error。
      items_count (int): 成功解析产生的条目数量（parsed 时有效）。
    """
    path: str
    index: int
    total: int
    cached: bool
    status: Literal["scanning", "parsed", "skipped", "error"]
    items_count: int = 0


class IndexBuilder:
    def __init__(
        self,
        code_roots: Optional[List[str]] = None,
        cache_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        self.config_path = config_path or Path(".harbor/config.yaml")
        cfg = self._load_config(self.config_path)
        if code_roots is None or cache_dir is None:
            code_roots = code_roots or cfg.get("code_roots", ["harbor/**"])
            cache_base = Path(".harbor") / "cache"
            cache_dir = cache_dir or cache_base
        self.code_roots = code_roots
        self.cache_dir = cache_dir
        self.cache_file = self.cache_dir / "l3_index.json"
        self.adapter = PythonAdapter()
        self.exclude_paths = cfg.get("exclude_paths", [])
        self.gitignore = GitIgnoreMatcher.from_root(cfg_excludes=self.exclude_paths)

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
        scanned = 0
        updated = 0
        skipped = 0
        items_total = 0
        for ev in self.iter_build(incremental=incremental):
            if ev.status == "parsed":
                scanned += 1
                updated += 1
                items_total += ev.items_count
            elif ev.status == "skipped":
                scanned += 1
                skipped += 1
            elif ev.status == "error":
                scanned += 1
                skipped += 1
        elapsed_ms = int((time.time() - t0) * 1000)
        return IndexReport(
            scanned_files=scanned,
            updated_files=updated,
            skipped_files=skipped,
            total_items=items_total,
            cache_path=str(self.cache_file.as_posix()),
            elapsed_ms=elapsed_ms,
        )

    def iter_build(self, incremental: bool = True) -> Iterator[ProgressEvent]:
        """以生成器方式构建索引，逐文件产出进度事件。

        功能:
          - 与 `build` 相同的索引构建逻辑，但每处理一个文件即产出事件。
          - 事件包含总数、当前序号、是否增量跳过、状态与产生条目数。
          - 构建完成后写入缓存文件。

        使用场景:
          - CLI 层的 Rich 进度条渲染。

        依赖:
          - harbor.adapters.python.PythonAdapter
          - .harbor/config.yaml 中的 code_roots

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          incremental (bool): 是否启用增量构建，默认为 True。

        Returns:
          Iterator[ProgressEvent]: 逐文件的进度事件。
        """
        t0 = time.time()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        old = self._load_cache()
        files_index: Dict[str, Any] = old.get("files", {})
        scanned = 0
        updated = 0
        skipped = 0
        items_total = 0
        files = self._iter_py_files()
        total = len(files)
        for i, p in enumerate(files, start=1):
            scanned += 1
            fp = str(p.as_posix())
            mtime = p.stat().st_mtime
            fhash = self._file_hash(p)
            prev = files_index.get(fp)
            if incremental and prev and prev.get("mtime") == mtime and prev.get("file_hash") == fhash:
                skipped += 1
                yield ProgressEvent(path=fp, index=i, total=total, cached=True, status="skipped")
                continue
            try:
                yield ProgressEvent(path=fp, index=i, total=total, cached=False, status="scanning")
                source = p.read_text(encoding="utf-8")
                items: List[Dict[str, Any]] = []
                for fc in self.adapter.parse_file(fp):
                    node = find_function_node(source, fc.lineno, fc.name)
                    body_hash = compute_body_hash(source, node) if node else ""
                    items.append(self._index_entry(fc, body_hash))
                files_index[fp] = {
                    "mtime": mtime,
                    "file_hash": fhash,
                    "items": items,
                }
                cnt = len(items)
                items_total += cnt
                updated += 1
                yield ProgressEvent(path=fp, index=i, total=total, cached=False, status="parsed", items_count=cnt)
            except Exception:
                skipped += 1
                yield ProgressEvent(path=fp, index=i, total=total, cached=False, status="error")
                continue
        payload = {
            "meta": {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "schema_version": "1.0.2",
            },
            "files": files_index,
        }
        self._save_cache(payload)
        # 为了保持旧接口统计能力，最终在 CLI 侧自行统计或读取缓存。
        _ = (scanned, updated, skipped, items_total, int((time.time() - t0) * 1000))

    def _iter_py_files(self) -> List[Path]:
        """生成待扫描的 Python 文件列表（支持 Git 感知剪枝）。

        功能:
          - 与 SyncEngine 共享统一实现，使用 `.gitignore` 与 `exclude_paths` 进行目录剪枝。
          - 返回去重后的 `Path` 列表。

        使用场景:
          - `iter_build` 的文件枚举阶段。

        依赖:
          - GitIgnoreMatcher
          - os.walk

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        return iter_project_files(self.code_roots, self.exclude_paths)

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

    # body_hash 与节点查找逻辑已抽出至 harbor.core.utils 以供 SyncEngine 复用
