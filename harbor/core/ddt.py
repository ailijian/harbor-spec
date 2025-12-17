from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from harbor.core.storage import HarborDB


@dataclass
class DDTBinding:
    func_id: str
    l3_version: Optional[int]
    strategy: str
    file_path: str
    test_name: str


@dataclass
class DDTReport:
    valid: List[DDTBinding]
    violations: List[Tuple[str, DDTBinding, str]]  # (type, binding, message)
    counts: Dict[str, int]


class DDTScanner:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or Path(".harbor/config.yaml")
        self.config = self._load_config(self.config_path)
        self.test_roots = self.config.get("test_roots", ["tests"])

    def scan_tests(self) -> List[DDTBinding]:
        bindings: List[DDTBinding] = []
        for p in self._iter_py_files(self.test_roots):
            try:
                src = p.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for dec in node.decorator_list:
                        call = dec if isinstance(dec, ast.Call) else None
                        if not call:
                            continue
                        callee_name = ""
                        if isinstance(call.func, ast.Name):
                            callee_name = call.func.id
                        elif isinstance(call.func, ast.Attribute):
                            callee_name = call.func.attr
                        if callee_name != "harbor_ddt_target":
                            continue
                        func_id = None
                        l3_version = None
                        strategy = "strict"
                        for kw in call.keywords:
                            key = kw.arg
                            val = kw.value
                            if key == "func" and isinstance(val, ast.Constant) and isinstance(val.value, str):
                                func_id = val.value
                            elif key == "l3_version" and isinstance(val, ast.Constant) and isinstance(val.value, int):
                                l3_version = val.value
                            elif key == "strategy" and isinstance(val, ast.Constant) and isinstance(val.value, str):
                                strategy = val.value
                        if not func_id:
                            # 优雅忽略：缺少常量 func 参数
                            continue
                        bindings.append(
                            DDTBinding(
                                func_id=func_id,
                                l3_version=l3_version,
                                strategy=strategy,
                                file_path=str(p.as_posix()),
                                test_name=node.name,
                            )
                        )
        return bindings

    def _iter_py_files(self, roots: List[str]) -> List[Path]:
        files: List[Path] = []
        base = Path.cwd()
        for pattern in roots:
            if "**" in pattern or "*" in pattern:
                for p in base.glob(pattern):
                    if p.is_dir():
                        files.extend([x for x in p.rglob("*.py")])
                    elif p.is_file() and p.suffix == ".py":
                        files.append(p)
            else:
                p = base / pattern
                if p.is_dir():
                    files.extend([x for x in p.rglob("*.py")])
                elif p.is_file() and p.suffix == ".py":
                    files.append(p)
        # 去重
        seen = set()
        result = []
        for p in files:
            k = p.resolve().as_posix()
            if k in seen:
                continue
            seen.add(k)
            result.append(p)
        return result

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"test_roots": ["tests"]}
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {"test_roots": ["tests"]}


class DDTValidator:
    def __init__(self, index_path: Optional[Path] = None, map_path: Optional[Path] = None) -> None:
        self.index_path = index_path or (Path(".harbor") / "cache" / "l3_index.json")
        self.map_path = map_path or (Path(".harbor") / "cache" / "l3_hash_map.json")
        self.index = self._load_index(self.index_path)
        self.version_map = self._load_map(self.map_path)
        # 构建 id -> (strictness, contract_hash)
        self._func_meta: Dict[str, Tuple[str, Optional[str]]] = {}
        for fp, meta in self.index.get("files", {}).items():
            for it in meta.get("items", []):
                self._func_meta[it["id"]] = (it.get("strictness", "standard") or "standard", it.get("contract_hash"))

    def validate(self, bindings: List[DDTBinding]) -> DDTReport:
        valid: List[DDTBinding] = []
        violations: List[Tuple[str, DDTBinding, str]] = []
        for b in bindings:
            strictness, contract_hash = self._func_meta.get(b.func_id, ("standard", None))
            if strictness == "strict" and b.strategy == "latest":
                violations.append(("strict_forbid_latest", b, "Strict function forbids strategy=latest"))
                continue
            # 推导当前版本（只在内存，不写盘）
            v_rec = self.version_map.get(b.func_id)
            if v_rec and v_rec.get("contract_hash") and contract_hash and v_rec["contract_hash"] != contract_hash:
                target_version = int(v_rec.get("l3_version", 1)) + 1
            else:
                target_version = int(v_rec.get("l3_version", 1)) if v_rec else 1
            if b.strategy == "latest":
                valid.append(b)
                continue
            # strict/explicit version path
            if b.l3_version is None:
                violations.append(("missing_binding_info", b, "l3_version required for strategy=strict"))
                continue
            if b.l3_version != target_version:
                violations.append(("version_mismatch", b, f"Version Mismatch: Contract changed. Expected v{target_version}, found v{b.l3_version}."))
            else:
                valid.append(b)
        counts = {
            "valid": len(valid),
            "violations": len(violations),
        }
        return DDTReport(valid=valid, violations=violations, counts=counts)

    def _load_index(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
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

    def _load_map(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
