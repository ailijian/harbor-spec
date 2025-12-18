from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from harbor.adapters.python.parser import PythonAdapter, FunctionContract
from harbor.core.utils import compute_body_hash, find_function_node, iter_project_files
from harbor.core.storage import HarborDB


@dataclass
class StatusEntry:
    id: str
    name: str
    file_path: str
    change_type: str
    details: str


@dataclass
class StatusReport:
    drift: List[StatusEntry]
    modified: List[StatusEntry]
    contract_changed: List[StatusEntry]
    untracked: List[StatusEntry]
    missing: List[StatusEntry]
    counts: Dict[str, int]


class SyncEngine:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or Path(".harbor/config.yaml")
        self.adapter = PythonAdapter()
        self.config = self._load_config(self.config_path)
        self.code_roots = self.config.get("code_roots", ["harbor/**"])
        self.exclude_paths = self.config.get("exclude_paths", [])
        self.db = HarborDB(project_root=Path.cwd())
        try:
            # 如果存在旧版 JSON 索引，优先迁移以提供基准
            self.db.migrate_from_json(Path(".harbor") / "cache" / "l3_index.json")
        except Exception:
            pass

    def check_status(self) -> StatusReport:
        """对比缓存索引与当前代码，输出 Harbor 上下文状态。

        功能:
          - 加载 `.harbor/cache/l3_index.json` 作为快照基准。
          - 实时解析 `code_roots` 下的 Python 文件，计算 `body_hash` 与 `contract_hash`。
          - 按照状态矩阵分类差异：Drift/Modified/Contract Changed/Untracked/Missing。

        使用场景:
          - CLI `harbor status`。
          - 本地开发时快速查看上下文一致性。

        依赖:
          - PythonAdapter
          - 与 IndexBuilder 一致的 body_hash 算法（harbor.core.utils.compute_body_hash）

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Returns:
          StatusReport: 包含各类状态分组与计数。

        Raises:
          IOError: 当索引缓存不可读。
          ConfigError: 当 `.harbor/config.yaml` 加载失败。
        """
        drift: List[StatusEntry] = []
        modified: List[StatusEntry] = []
        contract_changed: List[StatusEntry] = []
        untracked: List[StatusEntry] = []
        missing: List[StatusEntry] = []

        current_paths: List[str] = []
        files = self._iter_py_files()
        for p in files:
            fp = str(p.as_posix())
            current_paths.append(fp)
            disk_mtime = p.stat().st_mtime
            db_meta = self.db.get_file(fp)
            if db_meta and float(db_meta.get("last_modified", 0.0)) == float(disk_mtime):
                continue
            source = p.read_text(encoding="utf-8")
            new_items: Dict[str, Dict[str, Any]] = {}
            for fc in self.adapter.parse_file(fp):
                node = find_function_node(source, fc.lineno, fc.name)
                body_hash = compute_body_hash(source, node) if node else ""
                new_items[fc.id] = {
                    "id": fc.id,
                    "name": fc.name,
                    "body_hash": body_hash,
                    "contract_hash": fc.contract_hash,
                }
            old_items = {it["id"]: it for it in self.db.get_file_entries(fp)}
            all_ids = set(old_items.keys()) | set(new_items.keys())
            for id_ in sorted(all_ids):
                c = old_items.get(id_)
                n = new_items.get(id_)
                if c and n:
                    body_changed = (c.get("body_hash") != n.get("body_hash"))
                    contract_changed_flag = (c.get("contract_hash") != n.get("contract_hash"))
                    if body_changed and not contract_changed_flag:
                        drift.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Drift", details="Body changed, Contract static"))
                    elif body_changed and contract_changed_flag:
                        modified.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Modified", details="Body + Contract changed"))
                    elif (not body_changed) and contract_changed_flag:
                        contract_changed.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Contract Changed", details="Contract updated"))
                elif n and not c:
                    untracked.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Untracked", details="New function"))
                elif c and not n:
                    missing.append(StatusEntry(id=id_, name=c.get("meta", {}).get("name", ""), file_path=fp, change_type="Missing", details="Function removed"))

        db_files = [path for path, _ in self.db.get_all_files()]
        rel_current_set = set(
            Path(fp).resolve().relative_to(self.db.root).as_posix() for fp in current_paths
        )
        for db_fp in db_files:
            if db_fp not in rel_current_set:
                for it in self.db.get_file_entries(db_fp):
                    missing.append(StatusEntry(id=it.get("id", ""), name=it.get("meta", {}).get("name", ""), file_path=db_fp, change_type="Missing", details="File removed"))

        counts = {
            "drift": len(drift),
            "modified": len(modified),
            "contract_changed": len(contract_changed),
            "untracked": len(untracked),
            "missing": len(missing),
        }
        return StatusReport(
            drift=drift,
            modified=modified,
            contract_changed=contract_changed,
            untracked=untracked,
            missing=missing,
            counts=counts,
        )

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"code_roots": ["harbor/**"]}
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            raise RuntimeError("ConfigError: failed to load .harbor/config.yaml")

    def _iter_py_files(self) -> List[Path]:
        return iter_project_files(self.code_roots, self.exclude_paths)
