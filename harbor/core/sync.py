from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from harbor.adapters.python.parser import PythonAdapter, FunctionContract
from harbor.core.utils import compute_body_hash, find_function_node


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
        self.cache_file = Path(".harbor") / "cache" / "l3_index.json"
        self.adapter = PythonAdapter()
        self.config = self._load_config(self.config_path)
        self.code_roots = self.config.get("code_roots", ["harbor/**"])

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
        cached = self._load_index_cache()
        cached_map: Dict[str, Tuple[Dict[str, Any], str]] = {}
        for fp, meta in cached.get("files", {}).items():
            for it in meta.get("items", []):
                cached_map[it["id"]] = (it, fp)

        current_map: Dict[str, Tuple[Dict[str, Any], str]] = {}
        for p in self._iter_py_files():
            fp = str(p.as_posix())
            source = p.read_text(encoding="utf-8")
            for fc in self.adapter.parse_file(fp):
                node = find_function_node(source, fc.lineno, fc.name)
                body_hash = compute_body_hash(source, node) if node else ""
                current_map[fc.id] = (
                    {
                        "id": fc.id,
                        "name": fc.name,
                        "body_hash": body_hash,
                        "contract_hash": fc.contract_hash,
                    },
                    fp,
                )

        ids = set(cached_map.keys()) | set(current_map.keys())
        drift: List[StatusEntry] = []
        modified: List[StatusEntry] = []
        contract_changed: List[StatusEntry] = []
        untracked: List[StatusEntry] = []
        missing: List[StatusEntry] = []

        for id_ in sorted(ids):
            c_item = cached_map.get(id_)
            n_item = current_map.get(id_)
            if c_item and n_item:
                c, c_fp = c_item
                n, n_fp = n_item
                body_changed = (c.get("body_hash") != n.get("body_hash"))
                contract_changed_flag = (c.get("contract_hash") != n.get("contract_hash"))
                if body_changed and not contract_changed_flag:
                    drift.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=n_fp, change_type="Drift", details="Body changed, Contract static"))
                elif body_changed and contract_changed_flag:
                    modified.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=n_fp, change_type="Modified", details="Body + Contract changed"))
                elif (not body_changed) and contract_changed_flag:
                    contract_changed.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=n_fp, change_type="Contract Changed", details="Contract updated"))
            elif n_item and not c_item:
                n, n_fp = n_item
                untracked.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=n_fp, change_type="Untracked", details="New function"))
            elif c_item and not n_item:
                c, c_fp = c_item
                missing.append(StatusEntry(id=id_, name=c.get("name", ""), file_path=c_fp, change_type="Missing", details="Function removed"))

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

    def _load_index_cache(self) -> Dict[str, Any]:
        if not self.cache_file.exists():
            raise IOError("index cache not found: .harbor/cache/l3_index.json")
        return json.loads(self.cache_file.read_text(encoding="utf-8"))

    def _iter_py_files(self) -> List[Path]:
        roots = []
        base = Path.cwd()
        for pattern in self.code_roots:
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
        seen = set()
        dedup = []
        for p in roots:
            k = p.resolve().as_posix()
            if k in seen:
                continue
            seen.add(k)
            dedup.append(p)
        return dedup

