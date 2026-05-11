from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from harbor.adapters.python.parser import PythonAdapter
from harbor.adapters.registry import AdapterRegistry
from harbor.core.contract_presence import evaluate_contract_presence
from harbor.core.utils import compute_body_hash, find_function_node, iter_project_files
from harbor.core.storage import HarborDB
from harbor.core.workspace import resolve_workspace_config_path


@dataclass
class StatusEntry:
    id: str
    name: str
    file_path: str
    change_type: str
    details: str
    target_id: Optional[str] = None
    language: Optional[str] = None
    symbol_kind: Optional[str] = None
    adapter: Optional[str] = None


@dataclass
class StatusReport:
    """`SyncEngine.check_status()` 的聚合结果。

    字段说明:
      - drift/modified/contract_changed: 契约与实现差异主分类。
      - contract_gap/skipped_no_contract/unsupported_syntax_advisory/contract_parse_error:
        契约可用性分类。
      - untracked/missing: 索引与当前代码集合差异。
      - counts: 各分类计数字典，键与上述字段同名。
    """
    drift: List[StatusEntry]
    modified: List[StatusEntry]
    contract_changed: List[StatusEntry]
    contract_gap: List[StatusEntry]
    skipped_no_contract: List[StatusEntry]
    contract_parse_error: List[StatusEntry]
    untracked: List[StatusEntry]
    missing: List[StatusEntry]
    counts: Dict[str, int]
    unsupported_syntax_advisory: List[StatusEntry] = field(default_factory=list)


class SyncEngine:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or resolve_workspace_config_path(Path.cwd())
        self.config = self._load_config(self.config_path)
        self.registry = AdapterRegistry.from_config(self.config)
        self.code_roots = self.config.get("code_roots", ["harbor/**"])
        self.exclude_paths = self.config.get("exclude_paths", [])
        self.db = HarborDB(project_root=Path.cwd())
        try:
            # 如果存在旧版 JSON 索引，优先迁移以提供基准
            self.db.migrate_from_json(Path(".harbor") / "cache" / "l3_index.json")
        except Exception:
            pass

    @property
    def adapter(self) -> PythonAdapter:
        adapter = self.registry.get_adapter("python")
        if adapter is None:
            raise RuntimeError("Python adapter is disabled in registry config")
        return adapter

    def check_status(self) -> StatusReport:
        """对比缓存索引与当前代码，输出 Harbor 上下文状态。

        功能:
          - 基于 HarborDB 快照进行比对（初始化阶段会尝试从 `.harbor/cache/l3_index.json` 迁移旧索引）。
          - 通过 AdapterRegistry 的启用语言门控获取待扫描文件；v1.4.0 默认仅启用 Python。
          - 实时解析 `code_roots` 下的 Python 文件，计算 `body_hash` 与 `contract_hash`。
          - 按照状态矩阵分类差异:
            - Drift/Modified/Contract Changed
            - Contract Gap/Skipped No Contract/Contract Parse Error
            - Untracked/Missing
          - 本阶段仅完成 registry skeleton 接入，不改变 `evaluate_contract_presence` 调用语义、
            old/new item 比较规则、StatusReport/StatusEntry 字段或 checkpoint 分类语义。

        使用场景:
          - CLI `harbor status`。
          - 本地开发时快速查看上下文一致性。

        依赖:
          - AdapterRegistry（文件发现门控）
          - PythonAdapter（仍返回 FunctionContract，保持 Python 状态比较路径兼容）
          - 与 IndexBuilder 一致的 body_hash 算法（harbor.core.utils.compute_body_hash）

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Returns:
          StatusReport: 包含各类状态分组与计数；文件集合经 AdapterRegistry 门控后仍按 Python-only
            语义生成 drift/modified/contract_changed/contract_gap/skipped_no_contract/
            unsupported_syntax_advisory/contract_parse_error/untracked/missing 分类。

        Raises:
          Exception: 可能透传文件系统读取、源码解析或存储层异常；该方法不会统一包装异常类型。
        """
        drift: List[StatusEntry] = []
        modified: List[StatusEntry] = []
        contract_changed: List[StatusEntry] = []
        contract_gap: List[StatusEntry] = []
        skipped_no_contract: List[StatusEntry] = []
        unsupported_syntax_advisory: List[StatusEntry] = []
        contract_parse_error: List[StatusEntry] = []
        untracked: List[StatusEntry] = []
        missing: List[StatusEntry] = []

        current_paths: List[str] = []
        files = self._iter_files_by_enabled_adapters()
        for p in files:
            fp = str(p.as_posix())
            if self._is_typescript_path(fp):
                ts_adapter = self.registry.get_adapter("typescript")
                if ts_adapter is None:
                    continue
                try:
                    subjects = list(ts_adapter.parse_file(fp))
                except Exception:
                    continue
                for subject in subjects:
                    entry_id = str(subject.legacy_func_id or subject.target_id or "").strip()
                    entry_name = str(subject.qualified_name or "").strip()
                    common_kwargs = {
                        "id": entry_id,
                        "name": entry_name,
                        "file_path": fp,
                        "target_id": str(subject.target_id or "").strip() or None,
                        "language": str(subject.language or "typescript").strip().lower(),
                        "symbol_kind": str(subject.symbol_kind or "").strip().lower() or None,
                        "adapter": "typescript",
                    }
                    presence = str(subject.contract_presence or "missing")
                    if presence == "unsupported_syntax":
                        unsupported_syntax_advisory.append(
                            StatusEntry(
                                change_type="Unsupported Syntax Advisory",
                                details="TypeScript MVP parser could not safely classify this target.",
                                **common_kwargs,
                            )
                        )
                        continue
                    if presence in {"missing", "non_contract_doc"}:
                        required = bool(subject.contract_required)
                        if required:
                            contract_gap.append(
                                StatusEntry(
                                    change_type="Contract Gap",
                                    details="Required TypeScript contract source is missing or not contract-like.",
                                    **common_kwargs,
                                )
                            )
                        else:
                            skipped_no_contract.append(
                                StatusEntry(
                                    change_type="Skipped No Contract",
                                    details="No contract required for this TypeScript target; semantic comparison skipped.",
                                    **common_kwargs,
                                )
                            )
                continue
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
                presence = evaluate_contract_presence(fc, fp)
                new_items[fc.id] = {
                    "id": fc.id,
                    "name": fc.name,
                    "body_hash": body_hash,
                    "contract_hash": fc.contract_hash,
                    "contract_presence": presence.presence,
                    "contract_required": presence.required,
                    "contract_reason": presence.reason,
                }
            old_items = {it["id"]: it for it in self.db.get_file_entries(fp)}
            all_ids = set(old_items.keys()) | set(new_items.keys())
            for id_ in sorted(all_ids):
                c = old_items.get(id_)
                n = new_items.get(id_)
                if c and n:
                    presence = str(n.get("contract_presence") or "present")
                    if presence == "malformed":
                        contract_parse_error.append(
                            StatusEntry(
                                id=id_,
                                name=n.get("name", ""),
                                file_path=fp,
                                change_type="Contract Parse Error",
                                details=str(n.get("contract_reason") or "Contract source malformed"),
                            )
                        )
                        continue
                    if presence != "present":
                        required = bool(n.get("contract_required"))
                        if required:
                            contract_gap.append(
                                StatusEntry(
                                    id=id_,
                                    name=n.get("name", ""),
                                    file_path=fp,
                                    change_type="Contract Gap",
                                    details="No contract source found for required target",
                                )
                            )
                        else:
                            skipped_no_contract.append(
                                StatusEntry(
                                    id=id_,
                                    name=n.get("name", ""),
                                    file_path=fp,
                                    change_type="Skipped No Contract",
                                    details="No contract required for this target",
                                )
                            )
                        continue
                    body_changed = (c.get("body_hash") != n.get("body_hash"))
                    contract_changed_flag = (c.get("contract_hash") != n.get("contract_hash"))
                    if body_changed and not contract_changed_flag:
                        drift.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Drift", details="Body changed, Contract static"))
                    elif body_changed and contract_changed_flag:
                        modified.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Modified", details="Body + Contract changed"))
                    elif (not body_changed) and contract_changed_flag:
                        contract_changed.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Contract Changed", details="Contract updated"))
                elif n and not c:
                    presence = str(n.get("contract_presence") or "present")
                    if presence == "malformed":
                        contract_parse_error.append(
                            StatusEntry(
                                id=id_,
                                name=n.get("name", ""),
                                file_path=fp,
                                change_type="Contract Parse Error",
                                details=str(n.get("contract_reason") or "Contract source malformed"),
                            )
                        )
                    elif presence != "present":
                        required = bool(n.get("contract_required"))
                        target = contract_gap if required else skipped_no_contract
                        target.append(
                            StatusEntry(
                                id=id_,
                                name=n.get("name", ""),
                                file_path=fp,
                                change_type="Contract Gap" if required else "Skipped No Contract",
                                details="No contract source found for required target" if required else "No contract required for this target",
                            )
                        )
                    else:
                        untracked.append(StatusEntry(id=id_, name=n.get("name", ""), file_path=fp, change_type="Untracked", details="New function"))
                elif c and not n:
                    missing.append(StatusEntry(id=id_, name=c.get("meta", {}).get("name", ""), file_path=fp, change_type="Missing", details="Function removed"))

        db_files = [path for path, _ in self.db.get_all_files()]
        rel_current_set = set(self.db._posix_rel(fp) for fp in current_paths)
        for db_fp in db_files:
            if not str(db_fp).endswith(".py"):
                continue
            if db_fp not in rel_current_set:
                for it in self.db.get_file_entries(db_fp):
                    missing.append(StatusEntry(id=it.get("id", ""), name=it.get("meta", {}).get("name", ""), file_path=db_fp, change_type="Missing", details="File removed"))

        counts = {
            "drift": len(drift),
            "modified": len(modified),
            "contract_changed": len(contract_changed),
            "contract_gap": len(contract_gap),
            "skipped_no_contract": len(skipped_no_contract),
            "unsupported_syntax_advisory": len(unsupported_syntax_advisory),
            "contract_parse_error": len(contract_parse_error),
            "untracked": len(untracked),
            "missing": len(missing),
        }
        return StatusReport(
            drift=drift,
            modified=modified,
            contract_changed=contract_changed,
            contract_gap=contract_gap,
            skipped_no_contract=skipped_no_contract,
            unsupported_syntax_advisory=unsupported_syntax_advisory,
            contract_parse_error=contract_parse_error,
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
            raise RuntimeError(f"ConfigError: failed to load {path.as_posix()}")

    def _iter_py_files(self) -> List[Path]:
        return iter_project_files(self.code_roots, self.exclude_paths)

    def _iter_files_by_enabled_adapters(self) -> List[Path]:
        files: List[Path] = []
        if self.registry.is_enabled("python"):
            files.extend(self._iter_py_files())
        if self.registry.is_enabled("typescript"):
            adapter = self.registry.get_adapter("typescript")
            if adapter is not None:
                try:
                    files.extend(adapter.discover_files(self._iter_code_roots()))
                except Exception:
                    pass

        dedup: Dict[str, Path] = {}
        for path in files:
            dedup[path.resolve().as_posix()] = path.resolve()
        return [dedup[key] for key in sorted(dedup.keys())]

    def _iter_code_roots(self) -> List[Path]:
        roots: Dict[str, Path] = {}
        cwd = Path.cwd()
        for raw in self.code_roots:
            token = str(raw or "").strip()
            if not token:
                continue
            if any(ch in token for ch in ("*", "?", "[")):
                for matched in cwd.glob(token):
                    roots[matched.resolve().as_posix()] = matched.resolve()
                continue
            path = Path(token)
            if not path.is_absolute():
                path = (cwd / path)
            roots[path.resolve().as_posix()] = path.resolve()
        return [roots[key] for key in sorted(roots.keys())]

    @staticmethod
    def _is_typescript_path(path_text: str) -> bool:
        normalized = str(path_text or "").strip().lower()
        return normalized.endswith(".ts") and not normalized.endswith(".d.ts")
