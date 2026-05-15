from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from harbor.adapters.python.compat import function_contract_to_subject
from harbor.adapters.python.parser import PythonAdapter
from harbor.adapters.registry import AdapterRegistry
from harbor.core.contract_presence import evaluate_contract_presence
from harbor.core.utils import (
    compute_body_hash,
    discover_indexable_files,
    find_function_node,
    iter_project_files,
    resolve_code_roots,
)
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
    export_mode: Optional[str] = None
    public_surface_evidence: Optional[str] = None
    data_contract_kind: Optional[str] = None
    schema_source_kind: Optional[str] = None
    contract_source_kinds: Optional[List[str]] = None
    contract_source_fingerprints: Optional[List[str]] = None
    source_confidence_summary: Optional[str] = None
    public_boundary_state: Optional[str] = None
    public_boundary_confidence: Optional[str] = None
    public_boundary_evidence_kinds: Optional[List[str]] = None
    public_boundary_evidence_items: Optional[List[Dict[str, Any]]] = None
    public_boundary_reason: Optional[str] = None
    boundary_preset_mode: Optional[str] = None


def _subject_source_kinds(subject: object) -> List[str]:
    kinds: List[str] = []
    for source in list(getattr(subject, "contract_sources", ()) or ()):
        kind = getattr(source, "kind", None)
        value = getattr(kind, "value", kind)
        text = str(value or "").strip()
        if text:
            kinds.append(text)
    return kinds


def _subject_source_fingerprints(subject: object) -> List[str]:
    values: List[str] = []
    for source in list(getattr(subject, "contract_sources", ()) or ()):
        fingerprint = str(getattr(source, "fingerprint", "") or "").strip()
        if fingerprint:
            values.append(fingerprint)
    return values


def _subject_source_confidence_summary(subject: object) -> Optional[str]:
    priorities = {"high": 3, "medium": 2, "low": 1}
    strongest: Optional[str] = None
    best = 0
    for source in list(getattr(subject, "contract_sources", ()) or ()):
        confidence = str(getattr(source, "confidence", "") or "").strip().lower()
        score = priorities.get(confidence, 0)
        if score > best:
            strongest = confidence
            best = score
    return strongest


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

    def check_status(
        self,
        baseline_snapshot: Optional[object] = None,
        baseline_source: str = "runtime_cache",
    ) -> StatusReport:
        """对比缓存索引与当前代码，输出 Harbor 上下文状态。

        功能:
          - 基于 HarborDB 快照或显式传入的 accepted baseline artifact 快照进行比对
            （初始化阶段会尝试从 `.harbor/cache/l3_index.json` 迁移旧索引）。
          - 在 `checkpoint --ci` 路径中，accepted baseline artifact 是正式 CI baseline truth；
            缺失或非法 artifact 由 CLI 层单独归类，不回退到 runtime cache。
          - 通过 AdapterRegistry 的启用语言门控获取待扫描文件，按语言收集 Python / TypeScript 快照项。
          - Python 路径实时解析 `code_roots` 下源码并计算 `body_hash` 与 `contract_hash`。
          - TypeScript 路径收集 additive snapshot metadata（如 `target_id`、`language`、`symbol_kind`、
            `contract_source_*`），并纳入统一 comparison。
          - 当旧快照与当前文件的 `body_hash/contract_hash` 完全一致时，即使文件 mtime
            因 fresh clone / worktree 变化而不同，也保留 accepted baseline 语义，不重复报告
            历史 `contract_gap` / `skipped_no_contract` / `contract_parse_error`。
          - 按照状态矩阵分类差异:
            - Drift/Modified/Contract Changed
            - Contract Gap/Skipped No Contract/Contract Parse Error
            - Untracked/Missing
          - TypeScript comparison 采用 additive compatibility 方式扩展，不改变既有 Python gate 语义、
            `evaluate_contract_presence` 结果解释或 StatusReport/StatusEntry 字段契约。

        使用场景:
          - CLI `harbor status`。
          - 本地开发时快速查看上下文一致性。

        依赖:
          - AdapterRegistry（文件发现门控）
          - PythonAdapter（保持 Python 状态比较路径兼容）
          - TypeScript adapter（提供 TS snapshot item 与 identity metadata）
          - 与 IndexBuilder 一致的 body_hash 算法（harbor.core.utils.compute_body_hash）

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Returns:
          StatusReport: 包含各类状态分组与计数；比较结果会统一生成
            drift/modified/contract_changed/contract_gap/skipped_no_contract/
            unsupported_syntax_advisory/contract_parse_error/untracked/missing 分类，
            其中 TypeScript metadata 为 additive，既有 Python 分类语义保持不变。

        Raises:
          Exception: 可能透传文件系统读取、源码解析或存储层异常；该方法不会统一包装异常类型。
        """
        if baseline_snapshot is not None:
            current_snapshot = self.collect_current_snapshot()
            previous_snapshot = self._load_previous_snapshot_from_artifact(baseline_snapshot)
            return self._compare_snapshots(
                old_snapshot=previous_snapshot,
                new_snapshot=current_snapshot,
                baseline_source=baseline_source,
            )

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
                        "export_mode": str(subject.metadata.get("export_mode") or "").strip() or None,
                        "public_surface_evidence": str(subject.metadata.get("public_surface_evidence") or "").strip() or None,
                        "data_contract_kind": str(subject.metadata.get("data_contract_kind") or "").strip() or None,
                        "schema_source_kind": str(subject.metadata.get("schema_source_kind") or "").strip() or None,
                        "contract_source_kinds": _subject_source_kinds(subject) or None,
                        "contract_source_fingerprints": _subject_source_fingerprints(subject) or None,
                        "source_confidence_summary": _subject_source_confidence_summary(subject),
                        "public_boundary_state": str(subject.metadata.get("public_boundary_state") or "").strip() or None,
                        "public_boundary_confidence": str(subject.metadata.get("public_boundary_confidence") or "").strip() or None,
                        "public_boundary_evidence_kinds": [
                            str(value)
                            for value in list(subject.metadata.get("public_boundary_evidence_kinds") or [])
                            if str(value or "").strip()
                        ]
                        or None,
                        "public_boundary_evidence_items": [
                            dict(value)
                            for value in list(subject.metadata.get("public_boundary_evidence_items") or [])
                            if isinstance(value, dict)
                        ]
                        or None,
                        "public_boundary_reason": str(subject.metadata.get("public_boundary_reason") or "").strip() or None,
                        "boundary_preset_mode": str(subject.metadata.get("boundary_preset_mode") or "").strip() or None,
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
                    body_changed = (c.get("body_hash") != n.get("body_hash"))
                    contract_changed_flag = (c.get("contract_hash") != n.get("contract_hash"))
                    # Preserve accepted baseline semantics across fresh clones/worktrees:
                    # if implementation and contract hashes are unchanged, do not
                    # re-surface historical contract gaps purely because mtime changed.
                    if (not body_changed) and (not contract_changed_flag):
                        continue
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

    def collect_current_snapshot(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Collect the current comparable checkpoint snapshot from source files."""
        snapshot: Dict[str, Dict[str, Dict[str, Any]]] = {}
        files = self._iter_files_by_enabled_adapters()
        for path in files:
            file_path = self._normalize_repo_file_path(path)
            if self._is_typescript_path(file_path):
                items = self._collect_typescript_snapshot_items(file_path)
            else:
                items = self._collect_python_snapshot_items(path, file_path=file_path)
            snapshot[file_path] = items
        return snapshot

    def _load_previous_snapshot_from_artifact(self, payload: object) -> Dict[str, Dict[str, Dict[str, Any]]]:
        if isinstance(payload, dict) and "baseline" in payload:
            items = list((((payload.get("baseline") or {}) if isinstance(payload.get("baseline"), dict) else {}).get("items") or []))
        elif isinstance(payload, list):
            items = list(payload)
        elif isinstance(payload, dict):
            maybe_items = list(payload.values())
            if maybe_items and all(isinstance(value, dict) for value in maybe_items):
                return {
                    str(file_path): {
                        str(item_id): dict(item_payload)
                        for item_id, item_payload in (items_for_file or {}).items()
                        if isinstance(item_payload, dict)
                    }
                    for file_path, items_for_file in payload.items()
                    if isinstance(items_for_file, dict)
                }
            items = []
        else:
            items = []

        snapshot: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            file_path = str(item.get("file_path") or "").strip()
            item_id = str(item.get("id") or item.get("func_id") or "").strip()
            if not file_path or not item_id:
                continue
            snapshot.setdefault(file_path, {})[item_id] = dict(item)
        return snapshot

    def _compare_snapshots(
        self,
        *,
        old_snapshot: Dict[str, Dict[str, Dict[str, Any]]],
        new_snapshot: Dict[str, Dict[str, Dict[str, Any]]],
        baseline_source: str,
    ) -> StatusReport:
        drift: List[StatusEntry] = []
        modified: List[StatusEntry] = []
        contract_changed: List[StatusEntry] = []
        contract_gap: List[StatusEntry] = []
        skipped_no_contract: List[StatusEntry] = []
        unsupported_syntax_advisory: List[StatusEntry] = []
        contract_parse_error: List[StatusEntry] = []
        untracked: List[StatusEntry] = []
        missing: List[StatusEntry] = []

        all_files = sorted(set(old_snapshot.keys()) | set(new_snapshot.keys()))
        for file_path in all_files:
            old_items = old_snapshot.get(file_path, {})
            new_items = new_snapshot.get(file_path, {})
            all_ids = sorted(set(old_items.keys()) | set(new_items.keys()))
            for item_id in all_ids:
                current = new_items.get(item_id)
                previous = old_items.get(item_id)
                current_presence = str((current or {}).get("contract_presence") or "present")

                if current and current_presence == "unsupported_syntax":
                    unsupported_syntax_advisory.append(
                        self._status_entry_from_snapshot_item(
                            current,
                            change_type="Unsupported Syntax Advisory",
                            details="TypeScript MVP parser could not safely classify this target.",
                        )
                    )
                    continue

                if current and previous:
                    body_changed = str(previous.get("body_hash") or "") != str(current.get("body_hash") or "")
                    contract_changed_flag = str(previous.get("contract_hash") or "") != str(current.get("contract_hash") or "")
                    if (not body_changed) and (not contract_changed_flag):
                        continue
                    if current_presence == "malformed":
                        contract_parse_error.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Contract Parse Error",
                                details=str(current.get("contract_reason") or "Contract source malformed"),
                            )
                        )
                        continue
                    if current_presence != "present":
                        required = bool(current.get("contract_required"))
                        target = contract_gap if required else skipped_no_contract
                        target.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Contract Gap" if required else "Skipped No Contract",
                                details=(
                                    "No contract source found for required target"
                                    if required
                                    else "No contract required for this target"
                                ),
                            )
                        )
                        continue
                    if body_changed and not contract_changed_flag:
                        drift.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Drift",
                                details="Body changed, Contract static",
                            )
                        )
                    elif body_changed and contract_changed_flag:
                        modified.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Modified",
                                details="Body + Contract changed",
                            )
                        )
                    elif (not body_changed) and contract_changed_flag:
                        contract_changed.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Contract Changed",
                                details="Contract updated",
                            )
                        )
                    continue

                if current and not previous:
                    if current_presence == "malformed":
                        contract_parse_error.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Contract Parse Error",
                                details=str(current.get("contract_reason") or "Contract source malformed"),
                            )
                        )
                    elif current_presence != "present":
                        required = bool(current.get("contract_required"))
                        target = contract_gap if required else skipped_no_contract
                        target.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Contract Gap" if required else "Skipped No Contract",
                                details=(
                                    "No contract source found for required target"
                                    if required
                                    else "No contract required for this target"
                                ),
                            )
                        )
                    else:
                        untracked.append(
                            self._status_entry_from_snapshot_item(
                                current,
                                change_type="Untracked",
                                details=f"New function detected against {baseline_source} baseline",
                            )
                        )
                    continue

                if previous and not current:
                    missing.append(
                        self._status_entry_from_snapshot_item(
                            previous,
                            change_type="Missing",
                            details="Function removed",
                        )
                    )

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

    def _collect_python_snapshot_items(self, path: Path, *, file_path: str) -> Dict[str, Dict[str, Any]]:
        source = path.read_text(encoding="utf-8")
        items: Dict[str, Dict[str, Any]] = {}
        for contract in self.adapter.parse_file(file_path):
            node = find_function_node(source, contract.lineno, contract.name)
            body_hash = compute_body_hash(source, node) if node else ""
            presence = evaluate_contract_presence(contract, file_path)
            contract.contract_presence = presence.presence
            contract.contract_required = presence.required
            subject = function_contract_to_subject(contract, file_path)
            items[contract.id] = {
                "id": contract.id,
                "name": contract.name,
                "file_path": file_path,
                "target_id": subject.target_id,
                "func_id": contract.id,
                "language": "python",
                "symbol_kind": subject.symbol_kind,
                "adapter": "python",
                "body_hash": body_hash,
                "contract_hash": str(contract.contract_hash or ""),
                "contract_presence": presence.presence,
                "contract_required": bool(presence.required),
                "contract_reason": presence.reason,
            }
        return items

    def _collect_typescript_snapshot_items(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        adapter = self.registry.get_adapter("typescript")
        if adapter is None:
            return {}
        items: Dict[str, Dict[str, Any]] = {}
        for subject in adapter.parse_file(file_path):
            item_id = str(subject.legacy_func_id or subject.target_id or "").strip()
            if not item_id:
                continue
            items[item_id] = {
                "id": item_id,
                "name": str(subject.qualified_name or item_id),
                "file_path": file_path,
                "target_id": str(subject.target_id or ""),
                "func_id": item_id,
                "language": str(subject.language or "typescript"),
                "symbol_kind": str(subject.symbol_kind or ""),
                "adapter": "typescript",
                "body_hash": str(subject.body_hash or ""),
                "contract_hash": str(subject.contract_hash or ""),
                "contract_presence": str(subject.contract_presence or "missing"),
                "contract_required": bool(subject.contract_required),
                "contract_reason": str(subject.metadata.get("contract_required_reason") or ""),
                "export_mode": str(subject.metadata.get("export_mode") or ""),
                "public_surface_evidence": str(subject.metadata.get("public_surface_evidence") or ""),
                "data_contract_kind": str(subject.metadata.get("data_contract_kind") or ""),
                "schema_source_kind": str(subject.metadata.get("schema_source_kind") or ""),
                "contract_source_kinds": _subject_source_kinds(subject),
                "contract_source_fingerprints": _subject_source_fingerprints(subject),
                "source_confidence_summary": str(_subject_source_confidence_summary(subject) or ""),
                "public_boundary_state": str(subject.metadata.get("public_boundary_state") or ""),
                "public_boundary_confidence": str(subject.metadata.get("public_boundary_confidence") or ""),
                "public_boundary_evidence_kinds": [
                    str(value)
                    for value in list(subject.metadata.get("public_boundary_evidence_kinds") or [])
                    if str(value or "").strip()
                ],
                "public_boundary_evidence_items": [
                    dict(value)
                    for value in list(subject.metadata.get("public_boundary_evidence_items") or [])
                    if isinstance(value, dict)
                ],
                "public_boundary_reason": str(subject.metadata.get("public_boundary_reason") or ""),
                "boundary_preset_mode": str(subject.metadata.get("boundary_preset_mode") or ""),
            }
        return items

    def _status_entry_from_snapshot_item(self, item: Dict[str, Any], *, change_type: str, details: str) -> StatusEntry:
        return StatusEntry(
            id=str(item.get("id") or item.get("func_id") or ""),
            name=str(item.get("name") or item.get("func_id") or item.get("target_id") or ""),
            file_path=str(item.get("file_path") or ""),
            change_type=change_type,
            details=details,
            target_id=str(item.get("target_id") or "") or None,
            language=str(item.get("language") or "") or None,
            symbol_kind=str(item.get("symbol_kind") or "") or None,
            adapter=str(item.get("adapter") or "") or None,
            export_mode=str(item.get("export_mode") or "") or None,
            public_surface_evidence=str(item.get("public_surface_evidence") or "") or None,
            data_contract_kind=str(item.get("data_contract_kind") or "") or None,
            schema_source_kind=str(item.get("schema_source_kind") or "") or None,
            contract_source_kinds=[
                str(value)
                for value in list(item.get("contract_source_kinds") or [])
                if str(value or "").strip()
            ]
            or None,
            contract_source_fingerprints=[
                str(value)
                for value in list(item.get("contract_source_fingerprints") or [])
                if str(value or "").strip()
            ]
            or None,
            source_confidence_summary=str(item.get("source_confidence_summary") or "") or None,
            public_boundary_state=str(item.get("public_boundary_state") or "") or None,
            public_boundary_confidence=str(item.get("public_boundary_confidence") or "") or None,
            public_boundary_evidence_kinds=[
                str(value)
                for value in list(item.get("public_boundary_evidence_kinds") or [])
                if str(value or "").strip()
            ]
            or None,
            public_boundary_evidence_items=[
                dict(value)
                for value in list(item.get("public_boundary_evidence_items") or [])
                if isinstance(value, dict)
            ]
            or None,
            public_boundary_reason=str(item.get("public_boundary_reason") or "") or None,
            boundary_preset_mode=str(item.get("boundary_preset_mode") or "") or None,
        )

    def _normalize_repo_file_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(Path.cwd()).as_posix()
        except Exception:
            return path.resolve().as_posix()

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
        return discover_indexable_files(
            self.code_roots,
            self.exclude_paths,
            registry=self.registry,
            repo_root=Path.cwd(),
        )

    def _iter_code_roots(self) -> List[Path]:
        return resolve_code_roots(self.code_roots, repo_root=Path.cwd())

    @staticmethod
    def _is_typescript_path(path_text: str) -> bool:
        normalized = str(path_text or "").strip().lower()
        return normalized.endswith(".ts") and not normalized.endswith(".d.ts")
