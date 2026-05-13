from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

from harbor.core.index import process_file_worker
from harbor.core.index_entry import index_entry_to_cache_item
from harbor.core.storage import HarborDB
from harbor.core.utils import iter_project_files
from harbor.core.workspace import load_workspace_config

_TRANSIENT_INDEX_CACHE: Dict[str, Dict[str, Any]] = {}


def load_readonly_index(index_path: Path | None = None, *, repo_root: Path | None = None) -> Dict[str, Any]:
    root = (repo_root or Path.cwd()).resolve()
    target = _resolve_index_path(index_path, repo_root=root)
    if target.exists():
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Prefer a fresh source scan over runtime DB state so CI/view checks do not
    # depend on test-populated caches that are not source of truth.
    transient_payload = _build_transient_index(root)
    if transient_payload.get("files"):
        return transient_payload
    db_payload = _load_existing_db_index(repo_root=root)
    if db_payload is not None:
        return db_payload
    return transient_payload


def _resolve_index_path(index_path: Path | None, *, repo_root: Path) -> Path:
    candidate = Path(index_path) if index_path is not None else (Path(".harbor") / "cache" / "l3_index.json")
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _build_transient_index(repo_root: Path) -> Dict[str, Any]:
    cache_key = repo_root.as_posix()
    cached = _TRANSIENT_INDEX_CACHE.get(cache_key)
    if cached is not None:
        return copy.deepcopy(cached)

    loaded = load_workspace_config(repo_root)
    config = loaded.get("config") or {}
    code_roots = list(config.get("code_roots") or ["**/*.py"])
    exclude_paths = list(config.get("exclude_paths") or [])

    files: Dict[str, Any] = {}
    for source_path in iter_project_files(code_roots, exclude_paths):
        try:
            rel = source_path.resolve().relative_to(repo_root).as_posix()
        except Exception:
            rel = source_path.resolve().as_posix()
        _, mtime, items, _ = process_file_worker(str(source_path))
        files[rel] = {
            "mtime": mtime,
            "file_hash": "",
            "items": [index_entry_to_cache_item(item) for item in items],
        }

    payload: Dict[str, Any] = {
        "meta": {"schema_version": "1.0.2", "source": "transient_filesystem"},
        "files": files,
    }
    _TRANSIENT_INDEX_CACHE[cache_key] = copy.deepcopy(payload)
    return payload


def _load_existing_db_index(*, repo_root: Path) -> Dict[str, Any] | None:
    db_path = (repo_root / ".harbor" / "cache" / "harbor.db").resolve()
    if not db_path.exists():
        return None

    db = HarborDB(db_path=db_path, project_root=repo_root)
    try:
        files: Dict[str, Any] = {}
        for fp, mtime in db.get_all_files():
            items = []
            for it in db.get_file_entries(fp):
                meta = it.get("meta", {}) or {}
                items.append(
                    {
                        "id": it.get("id"),
                        "qualified_name": meta.get("qualified_name"),
                        "name": meta.get("name"),
                        "signature_hash": it.get("signature_hash"),
                        "body_hash": it.get("body_hash"),
                        "contract_hash": it.get("contract_hash"),
                        "docstring_raw_hash": meta.get("docstring_raw_hash"),
                        "scope": meta.get("scope"),
                        "strictness": meta.get("strictness"),
                        "lineno": meta.get("lineno"),
                    }
                )
            files[fp] = {"mtime": mtime, "file_hash": "", "items": items}
        if not files:
            return None
        return {"meta": {"schema_version": "1.0.2", "source": "existing_harbor_db"}, "files": files}
    finally:
        db.conn.close()
