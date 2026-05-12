from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

from harbor.core.index import process_file_worker
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
    return _build_transient_index(root)


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
        files[rel] = {"mtime": mtime, "file_hash": "", "items": items}

    payload: Dict[str, Any] = {
        "meta": {"schema_version": "1.0.2", "source": "transient_filesystem"},
        "files": files,
    }
    _TRANSIENT_INDEX_CACHE[cache_key] = copy.deepcopy(payload)
    return payload
