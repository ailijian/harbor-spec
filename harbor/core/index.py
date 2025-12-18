from __future__ import annotations

import os
import ast
import io
import json
import time
import hashlib
import tokenize
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Iterator, Literal

import yaml

from harbor.adapters.python.parser import PythonAdapter, FunctionContract
from harbor.core.utils import compute_body_hash, find_function_node, iter_project_files
from harbor.core.git_utils import GitIgnoreMatcher
from harbor.core.storage import HarborDB


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


def process_file_worker(fp: str) -> Tuple[str, float, List[Dict[str, Any]], Optional[str]]:
    """并行 Worker：解析并计算单文件条目。

    功能:
      - 读取 Python 源文件，使用 `PythonAdapter.parse_file` 提取契约。
      - 查找函数节点并计算 `body_hash`，组装条目。

    依赖:
      - harbor.adapters.python.PythonAdapter
      - harbor.core.utils.compute_body_hash/find_function_node

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only

    Args:
      fp (str): 需要处理的文件路径（posix 相对路径）。

    Returns:
      Tuple[str, float, List[Dict[str, Any]], Optional[str]]: (path, mtime, entries, error)
    """
    try:
        p = Path(fp)
        mtime = p.stat().st_mtime
        source = p.read_text(encoding="utf-8")
        adapter = PythonAdapter()
        items: List[Dict[str, Any]] = []
        for fc in adapter.parse_file(fp):
            node = find_function_node(source, fc.lineno, fc.name)
            body_hash = compute_body_hash(source, node) if node else ""
            items.append(
                {
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
            )
        return fp, mtime, items, None
    except Exception as ex:
        try:
            mtime = Path(fp).stat().st_mtime
        except Exception:
            mtime = 0.0
        return fp, mtime, [], str(ex)


class IndexBuilder:
    def __init__(
        self,
        code_roots: Optional[List[str]] = None,
        cache_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
        max_workers: Optional[int] = None,
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
        self.db = HarborDB(project_root=Path.cwd())
        self.max_workers = max_workers or os.cpu_count() or 1
        try:
            self.db.migrate_from_json(self.cache_file)
        except Exception:
            pass

    def build(self, incremental: bool = True) -> IndexReport:
        """构建或增量更新 L3 索引到缓存。

        功能:
          - 扫描配置的代码根目录，解析 Python 文件中的 L3 契约元数据（并行子进程执行 Parse & Hash）。
          - 计算每个函数/方法的 `signature_hash` 与 `body_hash`，生成索引条目（主进程写入 SQLite）。
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
            cache_path=str(self.db.db_path.as_posix()),
            elapsed_ms=elapsed_ms,
        )

    def iter_build(self, incremental: bool = True) -> Iterator[ProgressEvent]:
        """以生成器方式构建索引，逐文件产出进度事件。

        功能:
          - 改为 Producer-Consumer 并行架构：子进程执行 Parse & Hash，主进程写入 SQLite。
          - 每个文件会在提交任务时产出一次 `scanning` 事件；完成后产出 `parsed/skipped/error` 事件。
          - 事件包含总数、当前序号、是否增量跳过、状态与产生条目数；构建完成后写入缓存快照。

        使用场景:
          - CLI 层的 Rich 进度条渲染。

        依赖:
          - harbor.adapters.python.PythonAdapter
          - .harbor/config.yaml 中的 code_roots
          - concurrent.futures.ProcessPoolExecutor（Windows 兼容：顶层函数序列化）

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
        scanned = 0
        updated = 0
        skipped = 0
        items_total = 0
        files = self._iter_py_files()
        total = len(files)
        index_map: Dict[str, int] = {}
        to_process: List[Tuple[str, float]] = []
        for i, p in enumerate(files, start=1):
            root = self.db.root
            try:
                fp = str(p.resolve().relative_to(root).as_posix())
            except Exception:
                fp = str(p.resolve().as_posix())
            mtime = p.stat().st_mtime
            index_map[fp] = i
            scanned += 1
            db_meta = self.db.get_file(fp)
            if incremental and db_meta and float(db_meta.get("last_modified", 0.0)) == float(mtime):
                try:
                    self.db.upsert_file(fp, mtime, "indexed")
                except Exception:
                    pass
                skipped += 1
                yield ProgressEvent(path=fp, index=i, total=total, cached=True, status="skipped")
            else:
                yield ProgressEvent(path=fp, index=i, total=total, cached=False, status="scanning")
                to_process.append((fp, mtime))
        if to_process:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(process_file_worker, fp): (fp, mtime) for fp, mtime in to_process}
                for fut in as_completed(futures):
                    fp, mtime = futures[fut]
                    path, mtime2, entries, err = ("", 0.0, [], "unknown error")
                    try:
                        path, mtime2, entries, err = fut.result()
                    except KeyboardInterrupt:
                        executor.shutdown(wait=False, cancel_futures=True)
                        raise
                    except Exception as ex:
                        err = str(ex)
                    if err:
                        try:
                            self.db.upsert_file(fp, mtime, "error")
                        except Exception:
                            pass
                        skipped += 1
                        yield ProgressEvent(path=fp, index=index_map.get(fp, 0), total=total, cached=False, status="error")
                        continue
                    cnt = len(entries)
                    try:
                        with self.db.transaction():
                            self.db.upsert_file(fp, mtime2 or mtime, "indexed")
                            for it in entries:
                                meta = {
                                    "name": it.get("name"),
                                    "scope": it.get("scope"),
                                    "strictness": it.get("strictness"),
                                    "lineno": it.get("lineno"),
                                    "qualified_name": it.get("qualified_name"),
                                    "docstring_raw_hash": it.get("docstring_raw_hash"),
                                }
                                entry_obj = {
                                    "id": it.get("id"),
                                    "file_path": fp,
                                    "signature_hash": it.get("signature_hash"),
                                    "body_hash": it.get("body_hash"),
                                    "contract_hash": it.get("contract_hash"),
                                    "meta": meta,
                                }
                                self.db.upsert_entry(entry_obj)
                    except Exception:
                        try:
                            self.db.upsert_file(fp, mtime, "error")
                        except Exception:
                            pass
                        skipped += 1
                        yield ProgressEvent(path=fp, index=index_map.get(fp, 0), total=total, cached=False, status="error")
                        continue
                    items_total += cnt
                    updated += 1
                    yield ProgressEvent(path=fp, index=index_map.get(fp, 0), total=total, cached=False, status="parsed", items_count=cnt)
        _ = (scanned, updated, skipped, items_total, int((time.time() - t0) * 1000))
        try:
            self.db.purge_missing(files)
        except Exception:
            pass
        try:
            snapshot: Dict[str, Any] = {"meta": {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "schema_version": "1.0.2"}, "files": {}}
            all_files = self.db.get_all_files()
            for fp, mtime in all_files:
                items = []
                for it in self.db.get_file_entries(fp):
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
                snapshot["files"][fp] = {"mtime": mtime, "file_hash": "", "items": items}
            self._save_cache(snapshot)
        except Exception:
            pass

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
